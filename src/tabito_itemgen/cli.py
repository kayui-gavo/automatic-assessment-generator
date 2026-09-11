from __future__ import annotations

import argparse
from pathlib import Path

from .generate_request import create_q4_request, create_review_request, create_revision_request
from .io import load_json
from .models import HumanQA, Item, Review
from .paths import find_project_root
from .production import (
    approve_item,
    import_item_response,
    import_review_response,
    release_readiness,
    save_human_qa,
)
from .render import compile_xelatex, render_item_tex
from .validate import check_bank_similarity, compare_review, validate_item_file


def cmd_new_item(args: argparse.Namespace) -> int:
    root = find_project_root()
    item_id, request_path, spec_path = create_q4_request(
        root,
        topic=args.topic,
        difficulty=args.difficulty,
        domain=args.domain,
        scope=args.scope,
        notes=args.notes,
        surface_family=args.family,
    )
    print(item_id)
    print(f"request: {request_path}")
    print(f"spec:    {spec_path}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    item, response_path, draft_path, errors, warnings = import_item_response(
        root, source.read_text(encoding="utf-8")
    )
    print(f"item_id:  {item.item_id}")
    print(f"response: {response_path}")
    print(f"draft:    {draft_path}")
    return _print_validation(item, errors, warnings)


def _print_validation(item, errors, warnings) -> int:
    if errors:
        print("FAIL")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARNING: {warning}")
        return 1
    print("PASS")
    if item:
        slot_count = sum(len(task.answer_slots) for task in item.tasks)
        print(f"item_id: {item.item_id}")
        print(f"tasks: {len(item.tasks)}")
        print(f"answer_slots: {slot_count}")
        print(f"blueprint: {item.workflow.blueprint_version}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    item, errors, warnings = validate_item_file(Path(args.file).resolve())
    return _print_validation(item, errors, warnings)


def cmd_review_request(args: argparse.Namespace) -> int:
    root = find_project_root()
    out = create_review_request(root, Path(args.file).resolve())
    print(out)
    return 0


def cmd_import_review(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    review, target = import_review_response(root, source.read_text(encoding="utf-8"))
    print(f"item_id: {review.item_id}")
    print(target)
    return 0


def cmd_review_check(args: argparse.Namespace) -> int:
    item = Item.model_validate(load_json(Path(args.item).resolve()))
    review = Review.model_validate(load_json(Path(args.review).resolve()))
    errors, warnings = compare_review(item, review)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("PASS")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 1 if errors else 0


def cmd_revision_request(args: argparse.Namespace) -> int:
    root = find_project_root()
    out = create_revision_request(
        root,
        Path(args.item).resolve(),
        Path(args.review).resolve(),
    )
    print(out)
    return 0


def cmd_similarity(args: argparse.Namespace) -> int:
    root = find_project_root()
    item = Item.model_validate(load_json(Path(args.file).resolve()))
    matches = check_bank_similarity(item, root / "item_bank" / "approved")
    if not matches:
        print("No notable similarity against approved bank.")
        return 0
    for item_id, score in matches[:10]:
        print(f"{score:.3f}\t{item_id}")
    return 0


def cmd_release_check(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    readiness = release_readiness(root, source)
    print("READY" if readiness.ready else "NOT READY")
    for gate in readiness.gates:
        mark = "PASS" if gate.passed else "FAIL"
        print(f"{mark}\t{gate.name}\t{gate.detail}")
    return 0 if readiness.ready else 1


def cmd_approve(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()

    if args.review:
        review_source = Path(args.review).resolve()
        import_review_response(root, review_source.read_text(encoding="utf-8"))
    if args.human_qa:
        qa = HumanQA.model_validate(load_json(Path(args.human_qa).resolve()))
        save_human_qa(root, qa)

    try:
        target, readiness = approve_item(root, source)
    except ValueError as exc:
        print(f"Cannot approve: {exc}")
        return 1

    print(f"approved: {target}")
    for gate in readiness.gates:
        print(f"PASS\t{gate.name}\t{gate.detail}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    item = Item.model_validate(load_json(source))
    out_dir = root / "output" / item.item_id
    student_tex = render_item_tex(item, out_dir, teacher=False)
    teacher_tex = render_item_tex(item, out_dir, teacher=True)
    student_pdf = compile_xelatex(student_tex) if args.compile else None
    teacher_pdf = compile_xelatex(teacher_tex) if args.compile else None
    print(f"student tex: {student_tex}")
    print(f"teacher tex: {teacher_tex}")
    if args.compile:
        print(f"student pdf: {student_pdf or 'xelatex unavailable'}")
        print(f"teacher pdf: {teacher_pdf or 'xelatex unavailable'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tabito-itemgen")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("new-item", help="Create a manual ChatGPT request for Q4")
    command.add_argument("--topic", required=True)
    command.add_argument(
        "--difficulty",
        choices=["official_like", "easy", "medium", "hard"],
        default="official_like",
    )
    command.add_argument("--domain", default="auto")
    command.add_argument("--scope", choices=["full", "mini"], default="full")
    command.add_argument(
        "--family",
        choices=["main_2026", "makeup_2026"],
        default="main_2026",
        help="2026 Q4 surface family to reproduce with original content",
    )
    command.add_argument("--notes", default=None)
    command.set_defaults(func=cmd_new_item)

    command = sub.add_parser(
        "import-response",
        help="Import a manual ChatGPT JSON response into workspace + draft and validate it",
    )
    command.add_argument("file")
    command.set_defaults(func=cmd_import)

    command = sub.add_parser("validate", help="Validate an item JSON")
    command.add_argument("file")
    command.set_defaults(func=cmd_validate)

    command = sub.add_parser("review-request", help="Create a blind independent-review prompt")
    command.add_argument("file")
    command.set_defaults(func=cmd_review_request)

    command = sub.add_parser("import-review", help="Validate and save a review JSON")
    command.add_argument("file")
    command.set_defaults(func=cmd_import_review)

    command = sub.add_parser("review-check", help="Compare blind-review answers with the answer key")
    command.add_argument("--item", required=True)
    command.add_argument("--review", required=True)
    command.set_defaults(func=cmd_review_check)

    command = sub.add_parser("revision-request", help="Create a revision prompt from item + review")
    command.add_argument("--item", required=True)
    command.add_argument("--review", required=True)
    command.set_defaults(func=cmd_revision_request)

    command = sub.add_parser("similarity", help="Compare an item with the approved bank")
    command.add_argument("file")
    command.set_defaults(func=cmd_similarity)

    command = sub.add_parser(
        "release-check",
        help="Check validation + blind review + human QA + similarity gates",
    )
    command.add_argument("file")
    command.set_defaults(func=cmd_release_check)

    command = sub.add_parser(
        "approve",
        help="Approve only after deterministic validation, blind review, human QA and similarity gates",
    )
    command.add_argument("file")
    command.add_argument("--review", help="Optionally import a review JSON before approval")
    command.add_argument("--human-qa", help="Optionally import a human-QA JSON before approval")
    command.set_defaults(func=cmd_approve)

    command = sub.add_parser("render", help="Render student/teacher LaTeX files")
    command.add_argument("file")
    command.add_argument("--compile", action="store_true")
    command.set_defaults(func=cmd_render)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()

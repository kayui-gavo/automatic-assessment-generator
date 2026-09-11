from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .generate_request import create_q4_request, create_review_request, create_revision_request
from .io import load_json
from .models import Item, Review
from .paths import find_project_root
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
    )
    print(item_id)
    print(f"request: {request_path}")
    print(f"spec:    {spec_path}")
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    item = Item.model_validate(load_json(source))
    target = root / "item_bank" / "draft" / f"{item.item_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"imported draft: {target}")
    return 0


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
    review = Review.model_validate(load_json(source))
    target = root / "workspace" / "reviews" / f"{review.item_id}.review.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
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


def cmd_approve(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    item, errors, warnings = validate_item_file(source)
    if errors or item is None:
        print("Cannot approve: item validation failed")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if not args.override_review:
        if not args.review:
            print("Cannot approve: --review is required (or use --override-review explicitly)")
            return 1
        review = Review.model_validate(load_json(Path(args.review).resolve()))
        review_errors, review_warnings = compare_review(item, review)
        errors.extend(review_errors)
        warnings.extend(review_warnings)
        if review_errors:
            print("Cannot approve: blind review gate failed")
            for error in review_errors:
                print(f"ERROR: {error}")
            return 1

    matches = check_bank_similarity(item, root / "item_bank" / "approved")
    if matches and matches[0][1] >= 0.35 and not args.override_similarity:
        print("Cannot approve: high similarity to approved bank")
        for other_id, score in matches[:5]:
            print(f"SIMILAR: {score:.3f} {other_id}")
        print("Use --override-similarity only after human confirmation.")
        return 1

    target = root / "item_bank" / "approved" / f"{item.item_id}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f"approved: {target}")
    for warning in warnings:
        print(f"WARNING: {warning}")
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
        help="official_like keeps a mixed difficulty gradient instead of flattening the whole Q4",
    )
    command.add_argument("--domain", default="auto")
    command.add_argument("--scope", choices=["full", "mini"], default="full")
    command.add_argument("--notes", default=None)
    command.set_defaults(func=cmd_new_item)

    command = sub.add_parser("import-response", help="Validate schema and import generated JSON")
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

    command = sub.add_parser("approve", help="Approve an item after validation + blind review")
    command.add_argument("file")
    command.add_argument("--review")
    command.add_argument("--override-review", action="store_true")
    command.add_argument("--override-similarity", action="store_true")
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

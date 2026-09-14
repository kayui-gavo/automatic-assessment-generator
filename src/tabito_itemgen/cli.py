from __future__ import annotations

import argparse
from pathlib import Path

from .exam_generate import (
    create_all_section_requests,
    create_section_review_request,
    create_section_revision_request,
)
from .exam_production import (
    approve_exam,
    create_exam_project,
    exam_release_readiness,
    import_section_response,
    import_section_review,
    manifest_path,
)
from .exam_render import render_exam
from .exam_validation import validate_exam
from .generate_request import create_q4_request, create_review_request, create_revision_request
from .io import load_json
from .model_policy import PREFERRED_MODEL
from .models import Item, Review
from .paths import find_project_root
from .production import approve_item, import_item_response, release_readiness
from .render import compile_xelatex, render_item_tex
from .review_io import import_bound_review_response
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
    item, _, target, errors, warnings = import_item_response(
        root,
        source.read_text(encoding="utf-8"),
    )
    print(f"imported draft: {target}")
    print(f"item_id: {item.item_id}")
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 1 if errors else 0


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
    review, target = import_bound_review_response(root, source.read_text(encoding="utf-8"))
    print(f"saved review: {target}")
    print(f"item_id: {review.item_id}")
    return 0


def cmd_review_check(args: argparse.Namespace) -> int:
    item = Item.model_validate(load_json(Path(args.item).resolve()))
    review = Review.model_validate(load_json(Path(args.review).resolve()))
    errors, warnings = compare_review(item, review)
    print("PASS" if not errors else "FAIL")
    for error in errors:
        print(f"ERROR: {error}")
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
    readiness = release_readiness(root, Path(args.file).resolve())
    print(f"item_id: {readiness.item_id}")
    if readiness.fingerprint:
        print(f"fingerprint: {readiness.fingerprint}")
    for gate in readiness.gates:
        status = "PASS" if gate.passed else "FAIL"
        print(f"{status}: {gate.name} — {gate.detail}")
    return 0 if readiness.ready else 1


def cmd_approve(args: argparse.Namespace) -> int:
    root = find_project_root()
    try:
        target, readiness = approve_item(root, Path(args.file).resolve())
    except ValueError as exc:
        print(f"Cannot approve: {exc}")
        return 1
    print(f"approved: {target}")
    print(f"fingerprint: {readiness.fingerprint}")
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


def _resolve_exam_manifest(root: Path, exam_id: str) -> Path:
    draft = manifest_path(root, exam_id)
    if draft.exists():
        return draft
    approved = manifest_path(root, exam_id, approved=True)
    if approved.exists():
        return approved
    raise FileNotFoundError(f"exam project not found: {exam_id}")


def cmd_new_exam(args: argparse.Namespace) -> int:
    root = find_project_root()
    manifest, path = create_exam_project(
        root,
        exam_family=args.family,
        title_ja=args.title,
        notes=args.notes or "",
        q4_topic_request=args.q4_topic or "",
        q5_topic_request=args.q5_topic or "",
    )
    requests = create_all_section_requests(root, manifest.exam_id)
    print(manifest.exam_id)
    print(f"manifest: {path}")
    for section, request in requests.items():
        print(f"{section}: {request}")
    return 0


def cmd_exam_import_section(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    try:
        target, result = import_section_response(
            root,
            args.exam_id,
            args.section,
            source.read_text(encoding="utf-8"),
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Cannot import section: {exc}")
        return 1
    print(f"saved: {target}")
    for error in result.errors:
        print(f"ERROR: {error}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    return 1 if result.errors else 0


def cmd_exam_validate(args: argparse.Namespace) -> int:
    root = find_project_root()
    try:
        path = _resolve_exam_manifest(root, args.exam_id)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1
    result = validate_exam(path)
    print("PASS" if result.passed else "FAIL")
    for error in result.errors:
        print(f"ERROR: {error}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    return 0 if result.passed else 1


def cmd_exam_review_request(args: argparse.Namespace) -> int:
    root = find_project_root()
    try:
        out = create_section_review_request(root, args.exam_id, args.section)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Cannot create review request: {exc}")
        return 1
    print(out)
    return 0


def cmd_exam_import_review(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    try:
        out = import_section_review(
            root,
            args.exam_id,
            args.section,
            source.read_text(encoding="utf-8"),
            model_label=args.model,
            reasoning_level=args.reasoning,
            fresh_chat_confirmed=args.fresh_chat_confirmed,
            authoring_context_seen=args.authoring_context_seen,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Cannot import review: {exc}")
        return 1
    print(out)
    if not args.fresh_chat_confirmed:
        print("WARNING: blind-review release gate will fail until a fresh-chat review is imported")
    return 0


def cmd_exam_revision_request(args: argparse.Namespace) -> int:
    root = find_project_root()
    try:
        out = create_section_revision_request(root, args.exam_id, args.section)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Cannot create revision request: {exc}")
        return 1
    print(out)
    return 0


def cmd_exam_release_check(args: argparse.Namespace) -> int:
    root = find_project_root()
    try:
        readiness = exam_release_readiness(root, args.exam_id)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Cannot evaluate release: {exc}")
        return 1
    print(f"exam_id: {readiness.subject_id}")
    print(f"fingerprint: {readiness.fingerprint}")
    for gate in readiness.gates:
        status = "PASS" if gate.passed else "FAIL"
        print(f"{status}: {gate.name} — {gate.detail}")
    return 0 if readiness.ready else 1


def cmd_exam_approve(args: argparse.Namespace) -> int:
    root = find_project_root()
    try:
        target, readiness = approve_exam(root, args.exam_id)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Cannot approve exam: {exc}")
        return 1
    print(f"approved: {target}")
    print(f"fingerprint: {readiness.fingerprint}")
    return 0


def cmd_exam_render(args: argparse.Namespace) -> int:
    root = find_project_root()
    try:
        outputs = render_exam(root, args.exam_id, compile_pdf=args.compile)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Cannot render exam: {exc}")
        return 1
    for key, path in outputs.items():
        print(f"{key}: {path or 'xelatex unavailable'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tabito-itemgen")
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("new-exam", help="Create a Q1-Q5 full mock-exam project")
    command.add_argument(
        "--family", choices=["main_2026", "makeup_2026"], default="main_2026"
    )
    command.add_argument("--title", default=None)
    command.add_argument("--q4-topic", default=None)
    command.add_argument("--q5-topic", default=None)
    command.add_argument("--notes", default=None)
    command.set_defaults(func=cmd_new_exam)

    command = sub.add_parser("exam-import-section", help="Import one generated section JSON")
    command.add_argument("exam_id")
    command.add_argument("section", choices=["Q1", "Q2", "Q3", "Q4", "Q5"])
    command.add_argument("file")
    command.set_defaults(func=cmd_exam_import_section)

    command = sub.add_parser("exam-validate", help="Validate one full 200-point exam")
    command.add_argument("exam_id")
    command.set_defaults(func=cmd_exam_validate)

    command = sub.add_parser("exam-review-request", help="Create a blind-review prompt for one section")
    command.add_argument("exam_id")
    command.add_argument("section", choices=["Q1", "Q2", "Q3", "Q4", "Q5"])
    command.set_defaults(func=cmd_exam_review_request)

    command = sub.add_parser("exam-import-review", help="Import a fingerprint-bound section review")
    command.add_argument("exam_id")
    command.add_argument("section", choices=["Q1", "Q2", "Q3", "Q4", "Q5"])
    command.add_argument("file")
    command.add_argument("--model", default=PREFERRED_MODEL)
    command.add_argument(
        "--reasoning",
        choices=["instant", "medium", "high", "extra_high", "pro", "unknown"],
        default="high",
    )
    command.add_argument(
        "--fresh-chat-confirmed",
        action="store_true",
        help="Confirm that the reviewer ran in a new chat with no authoring/revision context",
    )
    command.add_argument(
        "--authoring-context-seen",
        action="store_true",
        help="Record that the reviewer saw authoring context; this intentionally fails the release gate",
    )
    command.set_defaults(func=cmd_exam_import_review)

    command = sub.add_parser("exam-revision-request", help="Create a revision prompt for one section")
    command.add_argument("exam_id")
    command.add_argument("section", choices=["Q1", "Q2", "Q3", "Q4", "Q5"])
    command.set_defaults(func=cmd_exam_revision_request)

    command = sub.add_parser("exam-release-check", help="Show full-exam release gates")
    command.add_argument("exam_id")
    command.set_defaults(func=cmd_exam_release_check)

    command = sub.add_parser("exam-approve", help="Approve a full exam only when every gate passes")
    command.add_argument("exam_id")
    command.set_defaults(func=cmd_exam_approve)

    command = sub.add_parser("exam-render", help="Render one continuous Q1-Q5 booklet")
    command.add_argument("exam_id")
    command.add_argument("--compile", action="store_true")
    command.set_defaults(func=cmd_exam_render)

    command = sub.add_parser("new-item", help="Create a manual ChatGPT request for legacy Q4-only use")
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

    command = sub.add_parser("import-response", help="Import generated Q4 JSON as a canonical draft")
    command.add_argument("file")
    command.set_defaults(func=cmd_import)

    command = sub.add_parser("validate", help="Validate a Q4 item JSON")
    command.add_argument("file")
    command.set_defaults(func=cmd_validate)

    command = sub.add_parser("review-request", help="Create a fingerprint-bound Q4 blind-review prompt")
    command.add_argument("file")
    command.set_defaults(func=cmd_review_request)

    command = sub.add_parser("import-review", help="Verify fingerprint and save a Q4 review JSON")
    command.add_argument("file")
    command.set_defaults(func=cmd_import_review)

    command = sub.add_parser("review-check", help="Compare Q4 blind-review answers with the answer key")
    command.add_argument("--item", required=True)
    command.add_argument("--review", required=True)
    command.set_defaults(func=cmd_review_check)

    command = sub.add_parser("revision-request", help="Create a Q4 revision prompt from item + review")
    command.add_argument("--item", required=True)
    command.add_argument("--review", required=True)
    command.set_defaults(func=cmd_revision_request)

    command = sub.add_parser("similarity", help="Compare a Q4 item with the approved bank")
    command.add_argument("file")
    command.set_defaults(func=cmd_similarity)

    command = sub.add_parser("release-check", help="Show all Q4 release gates")
    command.add_argument("file")
    command.set_defaults(func=cmd_release_check)

    command = sub.add_parser("approve", help="Approve Q4 only after persisted release gates pass")
    command.add_argument("file")
    command.set_defaults(func=cmd_approve)

    command = sub.add_parser("render", help="Render Q4 student/teacher LaTeX files")
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

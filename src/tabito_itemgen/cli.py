from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from .generate_request import create_q4_request, create_review_request, create_revision_request
from .io import load_json
from .models import Item, Review
from .paths import find_project_root
from .render import compile_xelatex, render_item_tex
from .validate import validate_item_file


def cmd_new_item(args: argparse.Namespace) -> int:
    root = find_project_root()
    item_id, request_path, spec_path = create_q4_request(
        root,
        topic=args.topic,
        difficulty=args.difficulty,
        domain=args.domain,
        question_count=args.questions,
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
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"imported draft: {target}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file).resolve()
    item, errors, warnings = validate_item_file(path)
    if errors:
        print("FAIL")
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print("PASS")
    if item:
        print(f"item_id: {item.item_id}")
        print(f"questions: {len(item.questions)}")
    for w in warnings:
        print(f"WARNING: {w}")
    return 0


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
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(target)
    return 0


def cmd_revision_request(args: argparse.Namespace) -> int:
    root = find_project_root()
    out = create_revision_request(
        root,
        Path(args.item).resolve(),
        Path(args.review).resolve(),
    )
    print(out)
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    root = find_project_root()
    source = Path(args.file).resolve()
    item, errors, warnings = validate_item_file(source)
    if errors or item is None:
        print("Cannot approve: validation failed")
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    target = root / "item_bank" / "approved" / f"{item.item_id}.json"
    shutil.copy2(source, target)
    print(f"approved: {target}")
    for w in warnings:
        print(f"WARNING: {w}")
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
    p = argparse.ArgumentParser(prog="tabito-itemgen")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("new-item", help="Create a manual ChatGPT request for a new Q4 item")
    s.add_argument("--topic", required=True)
    s.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    s.add_argument("--domain", default="school_life")
    s.add_argument("--questions", type=int, default=6)
    s.set_defaults(func=cmd_new_item)

    s = sub.add_parser("import-response", help="Validate and import a generated item JSON")
    s.add_argument("file")
    s.set_defaults(func=cmd_import)

    s = sub.add_parser("validate", help="Validate an item JSON")
    s.add_argument("file")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("review-request", help="Create an independent-review prompt")
    s.add_argument("file")
    s.set_defaults(func=cmd_review_request)

    s = sub.add_parser("import-review", help="Validate and save a review JSON")
    s.add_argument("file")
    s.set_defaults(func=cmd_import_review)

    s = sub.add_parser("revision-request", help="Create a revision prompt from item + review")
    s.add_argument("--item", required=True)
    s.add_argument("--review", required=True)
    s.set_defaults(func=cmd_revision_request)

    s = sub.add_parser("approve", help="Move a validated item into approved bank")
    s.add_argument("file")
    s.set_defaults(func=cmd_approve)

    s = sub.add_parser("render", help="Render student/teacher LaTeX files")
    s.add_argument("file")
    s.add_argument("--compile", action="store_true")
    s.set_defaults(func=cmd_render)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))

if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from .io import load_yaml


def create_q4_request(
    root: Path,
    topic: str,
    difficulty: str = "medium",
    domain: str = "school_life",
    question_count: int = 6,
) -> tuple[str, Path, Path]:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    item_id = f"TABITO-CN-Q4-{stamp}"
    spec = {
        "item_id": item_id,
        "section": "Q4",
        "topic": topic,
        "difficulty": difficulty,
        "domain": domain,
        "question_count": question_count,
        "generation_mode": "manual_chat",
    }

    spec_path = root / "workspace" / "requests" / f"{item_id}.spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    blueprint_path = root / "blueprints" / "common_test_chinese.yaml"
    template_path = root / "templates" / "q4.yaml"
    prompt_path = root / "prompts" / "generate_q4.md"

    prompt = Template(prompt_path.read_text(encoding="utf-8")).render(
        blueprint_yaml=blueprint_path.read_text(encoding="utf-8"),
        template_yaml=template_path.read_text(encoding="utf-8"),
        item_spec_json=json.dumps(spec, ensure_ascii=False, indent=2),
    )
    request_path = root / "workspace" / "requests" / f"{item_id}.request.md"
    request_path.write_text(prompt, encoding="utf-8")
    return item_id, request_path, spec_path


def create_review_request(root: Path, item_path: Path) -> Path:
    item_json = item_path.read_text(encoding="utf-8")
    prompt_path = root / "prompts" / "review_q4.md"
    prompt = Template(prompt_path.read_text(encoding="utf-8")).render(item_json=item_json)
    item_id = json.loads(item_json)["item_id"]
    out = root / "workspace" / "reviews" / f"{item_id}.review_request.md"
    out.write_text(prompt, encoding="utf-8")
    return out


def create_revision_request(root: Path, item_path: Path, review_path: Path) -> Path:
    item_json = item_path.read_text(encoding="utf-8")
    review_json = review_path.read_text(encoding="utf-8")
    prompt_path = root / "prompts" / "revise_q4.md"
    prompt = Template(prompt_path.read_text(encoding="utf-8")).render(
        item_json=item_json,
        review_json=review_json,
    )
    item_id = json.loads(item_json)["item_id"]
    out = root / "workspace" / "reviews" / f"{item_id}.revision_request.md"
    out.write_text(prompt, encoding="utf-8")
    return out

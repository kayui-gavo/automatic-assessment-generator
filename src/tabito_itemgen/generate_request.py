from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from .blind_surface import blind_section_dict
from .io import load_json
from .models import Item
from .production import item_fingerprint

BLUEPRINT_VERSION = "R8-2026-main-tsui-v4"


def _reference_context(root: Path) -> dict[str, str]:
    """Generation-safe context kept for backward compatibility with older callers."""

    return {
        "generation_profile_yaml": (
            root / "blueprints" / "q4_2026_generation_profile.yaml"
        ).read_text(encoding="utf-8"),
        "template_yaml": (root / "templates" / "q4.yaml").read_text(encoding="utf-8"),
    }


def _review_reference_context(root: Path) -> dict[str, str]:
    context = _reference_context(root)
    context["reference_patterns_yaml"] = (
        root / "blueprints" / "q4_2026_reference_patterns.yaml"
    ).read_text(encoding="utf-8")
    return context


def create_q4_request(
    root: Path,
    topic: str,
    difficulty: str = "official_like",
    domain: str = "auto",
    scope: str = "full",
    notes: str | None = None,
    surface_family: str = "main_2026",
) -> tuple[str, Path, Path]:
    if surface_family not in {"main_2026", "makeup_2026"}:
        raise ValueError("surface_family must be main_2026 or makeup_2026")

    # Milliseconds prevent accidental collisions from repeated UI clicks while
    # keeping item IDs readable in filenames and review logs.
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
    item_id = f"TABITO-CN-Q4-{stamp}"
    spec = {
        "item_id": item_id,
        "schema_version": "0.2",
        "section": "Q4",
        "scope": scope,
        "topic": topic,
        "difficulty": difficulty,
        "domain": domain,
        "surface_family": surface_family,
        "notes": notes or "",
        "generation_mode": "manual_chat",
        "blueprint_version": BLUEPRINT_VERSION,
    }

    requests = root / "workspace" / "requests"
    requests.mkdir(parents=True, exist_ok=True)
    spec_path = requests / f"{item_id}.spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    prompt_path = root / "prompts" / "generate_q4.md"
    prompt = Template(prompt_path.read_text(encoding="utf-8")).render(
        **_reference_context(root),
        item_spec_json=json.dumps(spec, ensure_ascii=False, indent=2),
    )
    request_path = requests / f"{item_id}.request.md"
    request_path.write_text(prompt, encoding="utf-8")
    return item_id, request_path, spec_path


def _blind_item_dict(item: Item) -> dict:
    """Backward-compatible wrapper around the shared student-visible scrubber."""

    return blind_section_dict(item)


def create_review_request(root: Path, item_path: Path) -> Path:
    item = Item.model_validate(load_json(item_path))
    blind_json = json.dumps(_blind_item_dict(item), ensure_ascii=False, indent=2)
    fingerprint = item_fingerprint(item)
    prompt_path = root / "prompts" / "review_q4.md"
    prompt = Template(prompt_path.read_text(encoding="utf-8")).render(
        **_review_reference_context(root),
        item_id=item.item_id,
        item_json=blind_json,
        candidate_fingerprint=fingerprint,
    )
    reviews = root / "workspace" / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    out = reviews / f"{item.item_id}.review_request.md"
    out.write_text(prompt, encoding="utf-8")
    return out


def create_revision_request(root: Path, item_path: Path, review_path: Path) -> Path:
    item_json = item_path.read_text(encoding="utf-8")
    review_json = review_path.read_text(encoding="utf-8")
    prompt_path = root / "prompts" / "revise_q4.md"
    prompt = Template(prompt_path.read_text(encoding="utf-8")).render(
        **_reference_context(root),
        item_json=item_json,
        review_json=review_json,
    )
    item_id = json.loads(item_json)["item_id"]
    reviews = root / "workspace" / "reviews"
    reviews.mkdir(parents=True, exist_ok=True)
    out = reviews / f"{item_id}.revision_request.md"
    out.write_text(prompt, encoding="utf-8")
    return out

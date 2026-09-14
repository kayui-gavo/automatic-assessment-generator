from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Template

from .blind_surface import blind_section_dict
from .exam_models import ExamManifest, Q1Section, Q2Section, Q3Section, Q5Section
from .exam_production import exam_workspace_dir, load_manifest, manifest_path
from .exam_review_models import SectionReview
from .model_policy import execution_protocol
from .models import Item
from .section_io import load_section, section_fingerprint


SECTION_MODELS = {
    "Q1": Q1Section,
    "Q2": Q2Section,
    "Q3": Q3Section,
    "Q4": Item,
    "Q5": Q5Section,
}

Q4_BLUEPRINT_VERSION = "R8-2026-main-tsui-v4"


def _blueprint_path(root: Path, manifest: ExamManifest, section: str) -> Path:
    if section == "Q1":
        return root / "blueprints" / "q1_2026.yaml"
    if section == "Q2":
        return root / "blueprints" / "q2_2026.yaml"
    if section == "Q3":
        return root / "blueprints" / "q3_2026.yaml"
    if section == "Q5":
        return root / "blueprints" / f"q5_2026_{'main' if manifest.exam_family == 'main_2026' else 'makeup'}.yaml"
    raise ValueError(f"no simple blueprint path for {section}")


def _q4_context(root: Path) -> dict[str, str]:
    """Generation-safe production context for Q4 authoring.

    Detailed observed reference patterns are intentionally reviewer-only. The author
    receives the production profile plus output template, which preserves the current
    family grammar without encouraging slot-by-slot reskinning of an official paper.
    """

    return {
        "generation_profile_yaml": (
            root / "blueprints" / "q4_2026_generation_profile.yaml"
        ).read_text(encoding="utf-8"),
        "template_yaml": (root / "templates" / "q4.yaml").read_text(encoding="utf-8"),
    }


def _q4_review_contract(root: Path) -> str:
    """Return detailed Q4 surface references only to reviewer models."""

    profile = (root / "blueprints" / "q4_2026_generation_profile.yaml").read_text(
        encoding="utf-8"
    )
    patterns = (root / "blueprints" / "q4_2026_reference_patterns.yaml").read_text(
        encoding="utf-8"
    )
    return (
        "# Q4 Production Profile — authoritative contract\n"
        + profile
        + "\n\n# Q4 Reference Patterns — reviewer-only observed surface\n"
        + patterns
    )


def _section_spec(manifest: ExamManifest, section: str) -> dict:
    ref = next(ref for ref in manifest.sections if ref.section == section)
    base = {
        "exam_id": manifest.exam_id,
        "exam_family": manifest.exam_family,
        "section": section,
        "section_id": ref.section_id,
        "score": ref.expected_score,
        "answer_start": ref.answer_start,
        "answer_end": ref.answer_end,
        "generation_mode": "manual_chat",
        "blueprint_version": "R8-2026-full-v1",
    }
    if section == "Q4":
        base.update(
            {
                "item_id": ref.section_id,
                "schema_version": "0.2",
                "scope": "full",
                "surface_family": manifest.exam_family,
                "topic": manifest.q4_topic_request or "原创・自動選定",
                "difficulty": "official_like",
                "domain": "auto",
                "notes": manifest.notes,
                "blueprint_version": Q4_BLUEPRINT_VERSION,
            }
        )
    elif section == "Q5":
        base.update(
            {
                "surface_family": manifest.exam_family,
                "topic_request": manifest.q5_topic_request or "原创・自動選定",
                "notes": manifest.notes,
            }
        )
    else:
        base["notes"] = manifest.notes
    return base


def _with_execution_protocol(stage: str, section: str, prompt: str) -> str:
    return execution_protocol(stage, section) + "\n\n---\n\n" + prompt


def create_exam_section_request(root: Path, exam_id: str, section: str) -> tuple[Path, Path]:
    manifest = load_manifest(manifest_path(root, exam_id))
    if section not in SECTION_MODELS:
        raise ValueError("section must be Q1..Q5")
    spec = _section_spec(manifest, section)
    request_dir = exam_workspace_dir(root, exam_id) / "requests"
    request_dir.mkdir(parents=True, exist_ok=True)
    spec_path = request_dir / f"{section.lower()}.spec.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if section == "Q4":
        template = Template((root / "prompts" / "generate_q4.md").read_text(encoding="utf-8"))
        prompt = template.render(
            **_q4_context(root),
            item_spec_json=json.dumps(spec, ensure_ascii=False, indent=2),
        )
    else:
        template = Template(
            (root / "prompts" / f"generate_{section.lower()}.md").read_text(encoding="utf-8")
        )
        blueprint = _blueprint_path(root, manifest, section).read_text(encoding="utf-8")
        prompt = template.render(
            item_spec_json=json.dumps(spec, ensure_ascii=False, indent=2),
            section_blueprint=blueprint,
            json_schema=json.dumps(
                SECTION_MODELS[section].model_json_schema(), ensure_ascii=False, indent=2
            ),
        )

    prompt = _with_execution_protocol("generate", section, prompt)
    request_path = request_dir / f"{section.lower()}.request.md"
    request_path.write_text(prompt, encoding="utf-8")
    return request_path, spec_path


def create_all_section_requests(root: Path, exam_id: str) -> dict[str, Path]:
    return {
        section: create_exam_section_request(root, exam_id, section)[0]
        for section in ("Q1", "Q2", "Q3", "Q4", "Q5")
    }


def create_section_review_request(root: Path, exam_id: str, section: str) -> Path:
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section)
    if not ref.path:
        raise ValueError(f"{section} has not been generated")
    section_data = load_section(manifest_path(root, exam_id).parent / ref.path)
    if section == "Q4":
        blueprint = _q4_review_contract(root)
    else:
        blueprint = _blueprint_path(root, manifest, section).read_text(encoding="utf-8")
    template = Template((root / "prompts" / "review_section.md").read_text(encoding="utf-8"))
    prompt = template.render(
        candidate_fingerprint=section_fingerprint(section_data),
        section_blueprint=blueprint,
        blind_json=json.dumps(blind_section_dict(section_data), ensure_ascii=False, indent=2),
        review_schema=json.dumps(SectionReview.model_json_schema(), ensure_ascii=False, indent=2),
    )
    prompt = _with_execution_protocol("review", section, prompt)
    out = exam_workspace_dir(root, exam_id) / "reviews" / f"{section.lower()}.review_request.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prompt, encoding="utf-8")
    return out


def create_section_revision_request(root: Path, exam_id: str, section: str) -> Path:
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section)
    if not ref.path:
        raise ValueError(f"{section} has not been generated")
    section_path = manifest_path(root, exam_id).parent / ref.path
    review_path = exam_workspace_dir(root, exam_id) / "reviews" / f"{section.lower()}.review.json"
    if not review_path.exists():
        raise ValueError("review JSON is missing")
    if section == "Q4":
        blueprint = _q4_context(root)["generation_profile_yaml"]
    else:
        blueprint = _blueprint_path(root, manifest, section).read_text(encoding="utf-8")
    template = Template((root / "prompts" / "revise_section.md").read_text(encoding="utf-8"))
    prompt = template.render(
        section_blueprint=blueprint,
        item_json=section_path.read_text(encoding="utf-8"),
        review_json=review_path.read_text(encoding="utf-8"),
        json_schema=json.dumps(
            SECTION_MODELS[section].model_json_schema(), ensure_ascii=False, indent=2
        ),
    )
    prompt = _with_execution_protocol("revision", section, prompt)
    out = exam_workspace_dir(root, exam_id) / "reviews" / f"{section.lower()}.revision_request.md"
    out.write_text(prompt, encoding="utf-8")
    return out

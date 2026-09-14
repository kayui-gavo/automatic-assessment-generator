from __future__ import annotations

from pathlib import Path

from tabito_itemgen.exam_models import ExamHumanQA, ExamQAChecks
from tabito_itemgen.exam_production import (
    approve_exam,
    import_section_response,
    load_manifest,
    manifest_path,
    save_exam_human_qa,
    save_section_human_qa,
    section_author_answers,
)
from tabito_itemgen.exam_review_models import (
    SECTION_SPECIFIC_QA,
    SectionHumanQA,
    SectionQAChecks,
    SectionQATiming,
    SectionReview,
)
from tabito_itemgen.section_io import load_section, section_fingerprint

from tests.artifact_factory import write_clean_artifacts
from tests.full_exam_factory import build_exam


def _bind_section_release_evidence(root: Path, exam_id: str, section_name: str) -> None:
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    section = load_section(manifest_path(root, exam_id).parent / ref.path)
    fingerprint = section_fingerprint(section)

    from tabito_itemgen.exam_production import import_section_review

    review = SectionReview(
        section=section_name,
        section_id=ref.section_id,
        candidate_fingerprint=fingerprint,
        verdict="pass",
        independent_answers=section_author_answers(section),
        issues=[],
        overall_comment_ja="pass",
    )
    import_section_review(
        root,
        exam_id,
        section_name,
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
    )
    qa = SectionHumanQA(
        section=section_name,
        section_id=ref.section_id,
        candidate_fingerprint=fingerprint,
        reviewer="TABITO QA",
        disposition="approve",
        checks=SectionQAChecks(**{name: True for name in SectionQAChecks.model_fields}),
        section_specific_checks={name: True for name in SECTION_SPECIFIC_QA[section_name]},
        timing=SectionQATiming(
            first_read_minutes=3,
            language_edit_minutes=2,
            item_edit_minutes=1,
            layout_edit_minutes=1,
        ),
        biggest_rework_cause="none",
    )
    save_section_human_qa(root, exam_id, section_name, qa)


def test_reimporting_revised_section_changes_fingerprint_and_invalidates_old_evidence(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    _bind_section_release_evidence(tmp_path, manifest.exam_id, "Q3")

    current = load_manifest(manifest_path(tmp_path, manifest.exam_id))
    ref = next(ref for ref in current.sections if ref.section == "Q3")
    section_path = manifest_path(tmp_path, manifest.exam_id).parent / ref.path
    section = load_section(section_path)
    old_fingerprint = section_fingerprint(section)

    section.tasks[0].rationale_ja += " 修訂版。"
    import_section_response(tmp_path, manifest.exam_id, "Q3", section.model_dump_json())

    current = load_manifest(manifest_path(tmp_path, manifest.exam_id))
    ref = next(ref for ref in current.sections if ref.section == "Q3")
    revised = load_section(manifest_path(tmp_path, manifest.exam_id).parent / ref.path)
    assert section_fingerprint(revised) != old_fingerprint
    assert ref.state == "draft"


def test_section_qa_timing_is_persisted(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    _bind_section_release_evidence(tmp_path, manifest.exam_id, "Q1")

    from tabito_itemgen.exam_production import section_qa_path
    from tabito_itemgen.io import load_json

    qa = load_json(section_qa_path(tmp_path, manifest.exam_id, "Q1"))
    assert qa["timing"] == {
        "first_read_minutes": 3,
        "language_edit_minutes": 2,
        "item_edit_minutes": 1,
        "layout_edit_minutes": 1,
    }
    assert qa["biggest_rework_cause"] == "none"


def test_approved_exam_remains_renderable_but_draft_manifest_is_removed(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    for section_name in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        _bind_section_release_evidence(tmp_path, manifest.exam_id, section_name)

    write_clean_artifacts(tmp_path, manifest.exam_id)
    qa = ExamHumanQA(
        exam_id=manifest.exam_id,
        reviewer="Final QA",
        disposition="approve",
        checks=ExamQAChecks(**{name: True for name in ExamQAChecks.model_fields}),
    )
    save_exam_human_qa(tmp_path, manifest.exam_id, qa)
    approved_dir, _ = approve_exam(tmp_path, manifest.exam_id)

    assert approved_dir.exists()
    assert not manifest_path(tmp_path, manifest.exam_id).exists()
    approved_manifest = load_manifest(approved_dir / "exam.json")
    assert approved_manifest.workflow.state == "approved"
    assert all(ref.state == "approved" for ref in approved_manifest.sections)
    assert (approved_dir / "artifacts" / "student.pdf").exists()

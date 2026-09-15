import pytest

from tabito_itemgen.exam_production import (
    load_manifest,
    manifest_path,
    save_section_human_qa,
)
from tabito_itemgen.exam_review_models import (
    SECTION_SPECIFIC_QA,
    SectionHumanQA,
    SectionQAChecks,
)
from tabito_itemgen.section_io import load_section, section_fingerprint

from tests.full_exam_factory import build_exam


def _qa(root, exam_id, section_name, disposition):
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    section = load_section(manifest_path(root, exam_id).parent / ref.path)
    return SectionHumanQA(
        section=section_name,
        section_id=ref.section_id,
        candidate_fingerprint=section_fingerprint(section),
        reviewer="QA",
        disposition=disposition,
        checks=SectionQAChecks(**{name: True for name in SectionQAChecks.model_fields}),
        section_specific_checks={name: True for name in SECTION_SPECIFIC_QA[section_name]},
    )


def test_human_qa_cannot_approve_before_current_blind_review_passes(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    qa = _qa(tmp_path, manifest.exam_id, "Q2", "approve")

    with pytest.raises(ValueError, match="requires a current passing Blind Review"):
        save_section_human_qa(tmp_path, manifest.exam_id, "Q2", qa)


def test_human_qa_can_record_revise_before_blind_review_passes(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    qa = _qa(tmp_path, manifest.exam_id, "Q2", "revise")

    path = save_section_human_qa(tmp_path, manifest.exam_id, "Q2", qa)
    assert path.exists()

from tabito_itemgen.exam_models import ExamHumanQA, ExamQAChecks
from tabito_itemgen.exam_production import (
    exam_fingerprint,
    import_section_review,
    load_manifest,
    manifest_path,
    save_exam_human_qa,
    save_section_human_qa,
    section_author_answers,
    section_release_readiness,
)
from tabito_itemgen.exam_review_models import SECTION_SPECIFIC_QA, SectionHumanQA, SectionQAChecks, SectionReview
from tabito_itemgen.io import dump_json
from tabito_itemgen.section_io import load_section, section_fingerprint

from tests.full_exam_factory import build_exam


def _approve_section_evidence(root, exam_id, section_name):
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    section = load_section(manifest_path(root, exam_id).parent / ref.path)
    fingerprint = section_fingerprint(section)
    review = SectionReview(
        section=section_name,
        section_id=ref.section_id,
        candidate_fingerprint=fingerprint,
        verdict="pass",
        independent_answers=section_author_answers(section),
        issues=[],
        overall_comment_ja="独立解答は著者キーと一致した。",
    )
    import_section_review(root, exam_id, section_name, review.model_dump_json())
    qa = SectionHumanQA(
        section=section_name,
        section_id=ref.section_id,
        candidate_fingerprint=fingerprint,
        reviewer="QA",
        disposition="approve",
        checks=SectionQAChecks(**{name: True for name in SectionQAChecks.model_fields}),
        section_specific_checks={name: True for name in SECTION_SPECIFIC_QA[section_name]},
    )
    save_section_human_qa(root, exam_id, section_name, qa)


def test_changing_q3_invalidates_q3_and_exam_qa_but_not_other_sections(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    for section_name in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        _approve_section_evidence(tmp_path, manifest.exam_id, section_name)

    exam_qa = ExamHumanQA(
        exam_id=manifest.exam_id,
        reviewer="Exam QA",
        disposition="approve",
        checks=ExamQAChecks(**{name: True for name in ExamQAChecks.model_fields}),
    )
    save_exam_human_qa(tmp_path, manifest.exam_id, exam_qa)
    before = exam_fingerprint(tmp_path, manifest.exam_id)

    current = load_manifest(manifest_path(tmp_path, manifest.exam_id))
    q3_ref = next(ref for ref in current.sections if ref.section == "Q3")
    q3_path = manifest_path(tmp_path, manifest.exam_id).parent / q3_ref.path
    q3 = load_section(q3_path)
    q3.tasks[0].source_text += "（修正版）"
    dump_json(q3_path, q3.model_dump())

    after = exam_fingerprint(tmp_path, manifest.exam_id)
    assert after != before
    assert not section_release_readiness(tmp_path, manifest.exam_id, "Q3").ready
    assert section_release_readiness(tmp_path, manifest.exam_id, "Q1").ready
    assert section_release_readiness(tmp_path, manifest.exam_id, "Q2").ready
    assert section_release_readiness(tmp_path, manifest.exam_id, "Q4").ready
    assert section_release_readiness(tmp_path, manifest.exam_id, "Q5").ready

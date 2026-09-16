import pytest

from tabito_itemgen.exam_models import ExamHumanQA, ExamQAChecks
from tabito_itemgen.exam_production import (
    approve_exam,
    exam_release_readiness,
    exam_release_record_path,
    import_section_review,
    load_manifest,
    manifest_path,
    save_exam_human_qa,
    save_section_human_qa,
    section_author_answers,
    section_release_readiness,
)
from tabito_itemgen.exam_review_models import (
    SECTION_SPECIFIC_QA,
    SectionHumanQA,
    SectionQAChecks,
    SectionReview,
)
from tabito_itemgen.io import load_json
from tabito_itemgen.section_io import load_section, section_fingerprint

from tests.artifact_factory import write_clean_artifacts
from tests.full_exam_factory import build_exam


ISOLATED_CONTEXT = "non_personalized_temporary_chat"


def _review_for(root, exam_id, section_name) -> SectionReview:
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    section = load_section(manifest_path(root, exam_id).parent / ref.path)
    return SectionReview(
        section=section_name,
        section_id=ref.section_id,
        candidate_fingerprint=section_fingerprint(section),
        verdict="pass",
        independent_answers=section_author_answers(section),
        issues=[],
        overall_comment_ja="pass",
    )


def _complete_section_qa(root, exam_id, section_name):
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    section = load_section(manifest_path(root, exam_id).parent / ref.path)
    fingerprint = section_fingerprint(section)
    review = _review_for(root, exam_id, section_name)
    import_section_review(
        root,
        exam_id,
        section_name,
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED_CONTEXT,
    )
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


def test_ordered_multislot_review_does_not_accept_reversed_q2_answers(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    ref = next(ref for ref in manifest.sections if ref.section == "Q2")
    section = load_section(manifest_path(tmp_path, manifest.exam_id).parent / ref.path)
    answers = section_author_answers(section)
    ordered_task = next(task_id for task_id, values in answers.items() if len(values) == 2)
    answers[ordered_task] = list(reversed(answers[ordered_task]))
    review = SectionReview(
        section="Q2",
        section_id=ref.section_id,
        candidate_fingerprint=section_fingerprint(section),
        verdict="pass",
        independent_answers=answers,
        issues=[],
        overall_comment_ja="reversed on purpose",
    )
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q2",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED_CONTEXT,
    )
    readiness = section_release_readiness(tmp_path, manifest.exam_id, "Q2")
    blind = next(gate for gate in readiness.gates if gate.name == "blind review")
    assert not blind.passed
    assert ordered_task in blind.detail


def test_blind_review_requires_confirmed_independent_context(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review_for(tmp_path, manifest.exam_id, "Q1")

    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q1",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=False,
        context_mode=ISOLATED_CONTEXT,
    )
    readiness = section_release_readiness(tmp_path, manifest.exam_id, "Q1")
    blind = next(gate for gate in readiness.gates if gate.name == "blind review")
    assert not blind.passed
    assert "independent context" in blind.detail

    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q1",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED_CONTEXT,
    )
    readiness = section_release_readiness(tmp_path, manifest.exam_id, "Q1")
    blind = next(gate for gate in readiness.gates if gate.name == "blind review")
    assert blind.passed


def test_blind_review_rejects_fresh_but_nonisolated_context(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review_for(tmp_path, manifest.exam_id, "Q3")
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q3",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode="unknown",
    )
    readiness = section_release_readiness(tmp_path, manifest.exam_id, "Q3")
    blind = next(gate for gate in readiness.gates if gate.name == "blind review")
    assert not blind.passed
    assert "memory-isolated" in blind.detail


def test_blind_review_rejects_below_production_reasoning(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review_for(tmp_path, manifest.exam_id, "Q5")
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q5",
        review.model_dump_json(),
        reasoning_level="medium",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED_CONTEXT,
    )
    readiness = section_release_readiness(tmp_path, manifest.exam_id, "Q5")
    blind = next(gate for gate in readiness.gates if gate.name == "blind review")
    assert not blind.passed
    assert "below production grade" in blind.detail


def test_final_exam_qa_requires_current_preflighted_artifact(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    qa = ExamHumanQA(
        exam_id=manifest.exam_id,
        reviewer="Exam QA",
        disposition="approve",
        checks=ExamQAChecks(**{name: True for name in ExamQAChecks.model_fields}),
    )
    with pytest.raises(ValueError, match="preflighted PDFs"):
        save_exam_human_qa(tmp_path, manifest.exam_id, qa)


def test_exam_release_requires_sections_artifacts_and_final_exam_qa(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    readiness = exam_release_readiness(tmp_path, manifest.exam_id)
    assert not readiness.ready

    for section_name in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        _complete_section_qa(tmp_path, manifest.exam_id, section_name)
    assert not exam_release_readiness(tmp_path, manifest.exam_id).ready

    artifact_path = write_clean_artifacts(tmp_path, manifest.exam_id)
    assert artifact_path.exists()
    assert not exam_release_readiness(tmp_path, manifest.exam_id).ready

    final_qa = ExamHumanQA(
        exam_id=manifest.exam_id,
        reviewer="Exam QA",
        disposition="approve",
        checks=ExamQAChecks(**{name: True for name in ExamQAChecks.model_fields}),
    )
    save_exam_human_qa(tmp_path, manifest.exam_id, final_qa)
    assert exam_release_readiness(tmp_path, manifest.exam_id).ready

    target, release = approve_exam(tmp_path, manifest.exam_id)
    assert release.ready
    assert target.exists()
    assert not manifest_path(tmp_path, manifest.exam_id).exists()
    approved_manifest = load_json(target / "exam.json")
    assert approved_manifest["workflow"]["state"] == "approved"
    assert all(ref["state"] == "approved" for ref in approved_manifest["sections"])
    assert (target / "artifacts" / "student.pdf").exists()
    assert (target / "artifacts" / "teacher.pdf").exists()
    assert (target / "artifacts" / "answer_sheet.pdf").exists()
    assert (target / "artifacts" / "answer_key.json").exists()
    record = load_json(exam_release_record_path(tmp_path, manifest.exam_id))
    assert record["exam_fingerprint"] == release.fingerprint
    assert record["artifact_manifest_sha256"]
    assert record["model_policy_version"]
    assert set(record["section_review_execution"]) == {"Q1", "Q2", "Q3", "Q4", "Q5"}
    assert all(
        execution["context_mode"] == ISOLATED_CONTEXT
        for execution in record["section_review_execution"].values()
    )


def test_artifact_change_invalidates_final_exam_qa(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    for section_name in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        _complete_section_qa(tmp_path, manifest.exam_id, section_name)
    write_clean_artifacts(tmp_path, manifest.exam_id)

    final_qa = ExamHumanQA(
        exam_id=manifest.exam_id,
        reviewer="Exam QA",
        disposition="approve",
        checks=ExamQAChecks(**{name: True for name in ExamQAChecks.model_fields}),
    )
    save_exam_human_qa(tmp_path, manifest.exam_id, final_qa)
    assert exam_release_readiness(tmp_path, manifest.exam_id).ready

    student_pdf = tmp_path / "output" / manifest.exam_id / "student.pdf"
    student_pdf.write_bytes(student_pdf.read_bytes() + b"changed")
    readiness = exam_release_readiness(tmp_path, manifest.exam_id)
    assert not readiness.ready
    artifact_gate = next(gate for gate in readiness.gates if gate.name == "artifact preflight")
    assert "changed after preflight" in artifact_gate.detail


def test_answer_key_change_invalidates_artifact_gate(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    write_clean_artifacts(tmp_path, manifest.exam_id)

    answer_key = tmp_path / "output" / manifest.exam_id / "answer_key.json"
    answer_key.write_text('{"1": 4}\n', encoding="utf-8")

    readiness = exam_release_readiness(tmp_path, manifest.exam_id)
    artifact_gate = next(gate for gate in readiness.gates if gate.name == "artifact preflight")
    assert not artifact_gate.passed
    assert "answer_key.json changed after preflight" in artifact_gate.detail

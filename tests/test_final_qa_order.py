import pytest

from tabito_itemgen.exam_models import ExamHumanQA, ExamQAChecks
from tabito_itemgen.exam_production import save_exam_human_qa

from tests.artifact_factory import write_clean_artifacts
from tests.full_exam_factory import build_exam


def _exam_qa(exam_id: str, disposition: str) -> ExamHumanQA:
    return ExamHumanQA(
        exam_id=exam_id,
        reviewer="Final QA",
        disposition=disposition,
        checks=ExamQAChecks(**{name: True for name in ExamQAChecks.model_fields}),
    )


def test_final_exam_qa_model_rejects_approve_with_incomplete_checks():
    with pytest.raises(ValueError, match="required checks are incomplete"):
        ExamHumanQA(
            exam_id="EXAM-1",
            reviewer="Final QA",
            disposition="approve",
            checks=ExamQAChecks(),
        )


def test_final_exam_qa_model_allows_revise_with_incomplete_checks():
    qa = ExamHumanQA(
        exam_id="EXAM-1",
        reviewer="Final QA",
        disposition="revise",
        checks=ExamQAChecks(),
    )
    assert qa.disposition == "revise"


def test_final_exam_qa_cannot_approve_before_all_sections_are_ready(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    write_clean_artifacts(tmp_path, manifest.exam_id)

    with pytest.raises(ValueError, match="every section to be Ready"):
        save_exam_human_qa(
            tmp_path,
            manifest.exam_id,
            _exam_qa(manifest.exam_id, "approve"),
        )


def test_final_exam_qa_can_record_revise_before_sections_are_ready(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    write_clean_artifacts(tmp_path, manifest.exam_id)

    path = save_exam_human_qa(
        tmp_path,
        manifest.exam_id,
        _exam_qa(manifest.exam_id, "revise"),
    )
    assert path.exists()

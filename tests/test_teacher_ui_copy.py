import pytest

from tabito_itemgen.exam_models import ExamHumanQA, ExamQAChecks
from tabito_itemgen.exam_review_models import (
    SECTION_SPECIFIC_QA,
    SectionHumanQA,
    SectionQAChecks,
)
from tabito_itemgen.exam_ui import (
    COMMON_QA_LABELS,
    EXAM_QA_LABELS,
    SPECIFIC_QA_LABELS,
    STATUS_COPY,
)
from tabito_itemgen.exam_ui_entrypoint import _guarded_save_exam_human_qa


def test_teacher_ui_has_human_labels_for_every_qa_check():
    assert set(COMMON_QA_LABELS) == set(SectionQAChecks.model_fields)
    assert set(EXAM_QA_LABELS) == set(ExamQAChecks.model_fields)

    required_specific = {
        field
        for fields in SECTION_SPECIFIC_QA.values()
        for field in fields
    }
    assert required_specific <= set(SPECIFIC_QA_LABELS)


def test_teacher_ui_statuses_do_not_expose_pipeline_jargon():
    visible = {label for label, _ in STATUS_COPY.values()}
    assert visible == {
        "未出题",
        "需修正",
        "草稿",
        "待独立审题",
        "需要返修",
        "不采用",
        "待教师确认",
        "已就绪",
        "已定稿",
    }


def test_section_qa_cannot_claim_approve_with_unchecked_requirements():
    with pytest.raises(ValueError, match="cannot be approved"):
        SectionHumanQA(
            section="Q1",
            section_id="Q1-test",
            candidate_fingerprint="a" * 64,
            reviewer="TABITO 教研",
            disposition="approve",
            checks=SectionQAChecks(),
            section_specific_checks={},
        )

    # Incomplete checks are meaningful evidence for a revision decision, so
    # revise/reject remain saveable rather than forcing teachers to tick boxes.
    qa = SectionHumanQA(
        section="Q1",
        section_id="Q1-test",
        candidate_fingerprint="a" * 64,
        reviewer="TABITO 教研",
        disposition="revise",
        checks=SectionQAChecks(),
        section_specific_checks={},
    )
    assert qa.disposition == "revise"


def test_final_exam_qa_guard_blocks_approve_with_unchecked_requirements(tmp_path):
    qa = ExamHumanQA(
        exam_id="EXAM-test",
        reviewer="TABITO 教研",
        disposition="approve",
        checks=ExamQAChecks(),
    )
    with pytest.raises(ValueError, match="整卷不能标记为「通过」"):
        _guarded_save_exam_human_qa(tmp_path, qa.exam_id, qa)

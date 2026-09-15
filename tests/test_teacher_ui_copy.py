from tabito_itemgen.exam_models import ExamQAChecks
from tabito_itemgen.exam_review_models import SECTION_SPECIFIC_QA, SectionQAChecks
from tabito_itemgen.exam_ui import (
    COMMON_QA_LABELS,
    EXAM_QA_LABELS,
    SPECIFIC_QA_LABELS,
    STATUS_COPY,
)


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
        "审题未通过",
        "待教师确认",
        "已就绪",
        "已定稿",
    }

import pytest

from tabito_itemgen.section_io import save_section_draft

from tests.full_exam_factory import q2, q5


def test_q2_ordering_answer_boxes_must_run_left_to_right(tmp_path):
    section = q2("Q2-surface-test")
    task = next(task for task in section.tasks if task.task_id == "Q2-C1")

    # This is internally solvable and can be made Pydantic-consistent, but it
    # would render answer box 9 to the right of answer box 10.
    task.answer_positions = [4, 2]
    task.answer_slots[0].correct_option = task.correct_sequence[3]
    task.answer_slots[1].correct_option = task.correct_sequence[1]

    with pytest.raises(ValueError, match="left-to-right ascending"):
        save_section_draft(tmp_path, section)


def test_q2_ordering_answer_numbers_must_run_left_to_right(tmp_path):
    section = q2("Q2-surface-test")
    task = next(task for task in section.tasks if task.task_id == "Q2-C1")
    task.answer_slots = list(reversed(task.answer_slots))
    task.answer_slots[0].correct_option = task.correct_sequence[task.answer_positions[0] - 1]
    task.answer_slots[1].correct_option = task.correct_sequence[task.answer_positions[1] - 1]

    with pytest.raises(ValueError, match="answer slot numbers must be left-to-right ascending"):
        save_section_draft(tmp_path, section)


def test_q5_underlined_anchor_requires_explicit_excerpt(tmp_path):
    section = q5("Q5-surface-test", "main_2026")
    section.anchors[0].source_excerpt = None

    with pytest.raises(ValueError, match="require an explicit source_excerpt"):
        save_section_draft(tmp_path, section)


def test_q5_underlined_excerpt_must_start_at_its_visible_marker(tmp_path):
    section = q5("Q5-surface-test", "main_2026")
    anchor = section.anchors[0]
    # The text exists in P1 but does not start immediately after 〔下線部1〕.
    anchor.source_excerpt = "这种做法很有意思。"

    with pytest.raises(ValueError, match="must begin immediately after visible marker"):
        save_section_draft(tmp_path, section)


def test_q5_visible_anchor_marker_must_be_unique_in_its_paragraph(tmp_path):
    section = q5("Q5-surface-test", "main_2026")
    section.anchors[1].paragraph_id = "P1"
    section.anchors[1].marker_label = "下線部1"

    with pytest.raises(ValueError, match="duplicated"):
        save_section_draft(tmp_path, section)

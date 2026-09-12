from __future__ import annotations

from pathlib import Path

from tabito_itemgen.exam_validation import validate_section_file
from tabito_itemgen.section_io import load_section

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "exam_001"


def test_pilot_exam_001_q1_q2_q3_q5_are_schema_valid():
    for filename in ("q1_v1.json", "q2_v1.json", "q3_v1.json", "q5_v1.json"):
        result = validate_section_file(PILOT / filename)
        assert result.errors == (), f"{filename}: {result.errors}"


def test_pilot_exam_001_q3_correct_positions_are_balanced():
    section = load_section(PILOT / "q3_v1.json")
    answers = [task.answer_slot.correct_option for task in section.tasks]
    assert sorted(answers) == [1, 1, 2, 2, 3, 3, 4, 4]


def test_pilot_exam_001_q5_anchors_are_visible_and_answer_range_is_complete():
    section = load_section(PILOT / "q5_v1.json")
    paragraphs = {paragraph.paragraph_id: paragraph.text_zh for paragraph in section.paragraphs}
    for anchor in section.anchors:
        text = paragraphs[anchor.paragraph_id]
        assert anchor.marker_label and anchor.marker_label in text
        if anchor.source_excerpt:
            assert anchor.source_excerpt in text
    numbers = sorted(slot.answer_number for task in section.tasks for slot in task.answer_slots)
    assert numbers == list(range(37, 51))

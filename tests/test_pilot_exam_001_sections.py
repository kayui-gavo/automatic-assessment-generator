from __future__ import annotations

from pathlib import Path

from tabito_itemgen.exam_validation import validate_section_file
from tabito_itemgen.section_io import load_section

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "exam_001"


def test_pilot_exam_001_q1_q2_q3_are_schema_valid():
    for filename in ("q1_v1.json", "q2_v1.json", "q3_v1.json"):
        result = validate_section_file(PILOT / filename)
        assert result.errors == (), f"{filename}: {result.errors}"


def test_pilot_exam_001_q3_correct_positions_are_balanced():
    section = load_section(PILOT / "q3_v1.json")
    answers = [task.answer_slot.correct_option for task in section.tasks]
    assert sorted(answers) == [1, 1, 2, 2, 3, 3, 4, 4]

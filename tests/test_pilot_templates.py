import csv
from pathlib import Path

from tabito_itemgen.pilot_analysis import ANSWER_COLUMNS, SECTION_COLUMNS


ROOT = Path(__file__).resolve().parents[1]


def _header(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return set(next(reader))


def test_student_answer_template_matches_analyzer_schema():
    path = ROOT / "pilots" / "exam_001" / "student_trial_answers_template.csv"
    assert _header(path) == ANSWER_COLUMNS


def test_student_section_template_matches_analyzer_schema():
    path = ROOT / "pilots" / "exam_001" / "student_trial_sections_template.csv"
    assert _header(path) == SECTION_COLUMNS

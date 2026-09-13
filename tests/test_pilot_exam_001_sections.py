from __future__ import annotations

import json
from pathlib import Path

from tabito_itemgen.exam_validation import validate_exam, validate_section_file
from tabito_itemgen.section_io import load_section

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "exam_001"


def test_pilot_exam_001_active_sections_are_schema_valid():
    for filename in ("q1_v1.json", "q2_v2.json", "q3_v3.json", "q4_v2.json", "q5_v3.json"):
        result = validate_section_file(PILOT / filename)
        assert result.errors == (), f"{filename}: {result.errors}"


def test_pilot_exam_001_whole_exam_validates():
    result = validate_exam(PILOT / "exam.json")
    assert result.errors == (), result.errors


def test_pilot_exam_001_q3_correct_positions_are_balanced():
    section = load_section(PILOT / "q3_v3.json")
    answers = [task.answer_slot.correct_option for task in section.tasks]
    assert sorted(answers) == [1, 1, 2, 2, 3, 3, 4, 4]


def test_pilot_exam_001_q5_anchors_are_visible_and_answer_range_is_complete():
    section = load_section(PILOT / "q5_v3.json")
    paragraphs = {paragraph.paragraph_id: paragraph.text_zh for paragraph in section.paragraphs}
    for anchor in section.anchors:
        text = paragraphs[anchor.paragraph_id]
        assert anchor.marker_label and anchor.marker_label in text
        if anchor.source_excerpt:
            assert anchor.source_excerpt in text
    numbers = sorted(slot.answer_number for task in section.tasks for slot in task.answer_slots)
    assert numbers == list(range(37, 51))


def test_pilot_exam_001_manifest_uses_current_revisions():
    manifest = json.loads((PILOT / "exam.json").read_text(encoding="utf-8"))
    paths = {ref["section"]: ref["path"] for ref in manifest["sections"]}
    assert paths == {
        "Q1": "q1_v1.json",
        "Q2": "q2_v2.json",
        "Q3": "q3_v3.json",
        "Q4": "q4_v2.json",
        "Q5": "q5_v3.json",
    }


def test_pilot_exam_001_q5_v3_uses_natural_relationship_wording():
    section = load_section(PILOT / "q5_v3.json")
    paragraphs = {paragraph.paragraph_id: paragraph.text_zh for paragraph in section.paragraphs}

    assert "自己和店里人的关系越来越〔空欄A〕" in paragraphs["P2"]
    assert "四处打听订单进度的时间" in paragraphs["P4"]
    assert "店里的人离自己越来越〔空欄A〕" not in paragraphs["P2"]

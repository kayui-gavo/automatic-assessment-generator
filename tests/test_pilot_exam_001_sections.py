from __future__ import annotations

import json
from pathlib import Path

from tabito_itemgen.exam_validation import validate_exam, validate_section_file
from tabito_itemgen.section_io import load_section

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "exam_001"


def test_pilot_exam_001_active_sections_are_schema_valid():
    for filename in ("q1_v2.json", "q2_v3.json", "q3_v3.json", "q4_v3.json", "q5_v3.json"):
        result = validate_section_file(PILOT / filename)
        assert result.errors == (), f"{filename}: {result.errors}"


def test_pilot_exam_001_whole_exam_validates():
    result = validate_exam(PILOT / "exam.json")
    assert result.errors == (), result.errors


def test_pilot_exam_001_q1_v2_preserves_dialogue_timeline():
    section = load_section(PILOT / "q1_v2.json")
    task = next(task for task in section.tasks if task.task_id == "Q1-D2")
    lines = [line.pinyin for line in task.lines]

    assert any("yào mǎi de dōngxi yǒu diǎn duō" in line for line in lines)
    assert all("língshí yǒu diǎn duō" not in line for line in lines)
    assert task.answer_slot.correct_option == 2


def test_pilot_exam_001_q2_v3_removes_obvious_garbage_distractors():
    section = load_section(PILOT / "q2_v3.json")
    tasks = {task.task_id: task for task in section.tasks}

    assert tasks["Q2-A"].options == ["核对", "承认", "证明", "保证"]
    assert tasks["Q2-B"].options == ["确认", "核对", "说明", "怀疑"]
    assert "把" not in tasks["Q2-B"].options

    c1 = {token.text_zh for token in tasks["Q2-C1"].token_pool}
    assert {"虽然", "但是", "已经", "才"}.issubset(c1)
    assert "被" not in c1

    c2 = {token.text_zh for token in tasks["Q2-C2"].token_pool}
    assert {"在到车站以前", "我只看了一遍", "朋友刚发来的地图", "就找到入口"}.issubset(c2)
    assert "被朋友" not in c2
    assert "虽然入口" not in c2


def test_pilot_exam_001_q3_correct_positions_are_balanced():
    section = load_section(PILOT / "q3_v3.json")
    answers = [task.answer_slot.correct_option for task in section.tasks]
    assert sorted(answers) == [1, 1, 2, 2, 3, 3, 4, 4]


def test_pilot_exam_001_q4_v3_uses_japanese_prompts_and_real_cross_source_reasoning():
    section = load_section(PILOT / "q4_v3.json")
    tasks = {task.task_id: task for task in section.tasks}

    assert tasks["A2b"].prompt_ja == "グラフの内容と一致するものを一つ選べ。"
    assert tasks["A2c"].prompt_ja == "二つのグラフから読み取れることとして、最も適当なものを一つ選べ。"
    assert tasks["B3a"].prompt_ja == "フローチャートが示す判断の原則として、最も適当なものを一つ選べ。"

    integrative = tasks["A2c"]
    assert integrative.dependency_mode == "cross_source"
    assert {item.material_id for item in integrative.evidence} == {"A-M4", "A-M5"}
    correct = integrative.options[integrative.answer_slots[0].correct_option - 1]
    assert "不知道活动内容是最常见的不参加原因" in correct
    assert "四个项目的报名人数都增加了" in correct


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
        "Q1": "q1_v2.json",
        "Q2": "q2_v3.json",
        "Q3": "q3_v3.json",
        "Q4": "q4_v3.json",
        "Q5": "q5_v3.json",
    }


def test_pilot_exam_001_q5_v3_uses_natural_relationship_wording():
    section = load_section(PILOT / "q5_v3.json")
    paragraphs = {paragraph.paragraph_id: paragraph.text_zh for paragraph in section.paragraphs}

    assert "自己和店里人的关系越来越〔空欄A〕" in paragraphs["P2"]
    assert "四处打听订单进度的时间" in paragraphs["P4"]
    assert "店里的人离自己越来越〔空欄A〕" not in paragraphs["P2"]

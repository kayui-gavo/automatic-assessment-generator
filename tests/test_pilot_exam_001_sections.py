from __future__ import annotations

import json
from pathlib import Path

from tabito_itemgen.exam_validation import validate_exam, validate_section_file
from tabito_itemgen.section_io import load_section

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "exam_001"


def test_pilot_exam_001_active_sections_are_schema_valid():
    for filename in ("q1_v4.json", "q2_v4.json", "q3_v5.json", "q4_v3.json", "q5_v4.json"):
        result = validate_section_file(PILOT / filename)
        assert result.errors == (), f"{filename}: {result.errors}"


def test_pilot_exam_001_whole_exam_validates():
    result = validate_exam(PILOT / "exam.json")
    assert result.errors == (), result.errors


def test_pilot_exam_001_q1_v4_uses_target_characters_and_neutral_tone():
    section = load_section(PILOT / "q1_v4.json")
    tasks = {task.task_id: task for task in section.tasks}

    for task_id in ("Q1-A", "Q1-B"):
        task = tasks[task_id]
        for word in [task.headword, *task.candidates]:
            assert len(word.hanzi) >= 2
            assert word.target_index is not None
            assert 1 <= word.target_index <= len(word.hanzi)

    assert tasks["Q1-A"].headword.hanzi == "条件"
    assert tasks["Q1-A"].headword.target_index == 2
    assert tasks["Q1-A"].answer_slot.correct_option == 3
    assert tasks["Q1-B"].answer_slot.correct_option == 2

    c2 = tasks["Q1-C2"]
    assert c2.headword.pinyin == "zhīshi"
    assert [word.pinyin for word in c2.candidates] == ["yīfu", "dōngxi", "tōngzhī", "guānxì"]
    assert c2.answer_slot.correct_option == 2


def test_pilot_exam_001_q1_v4_dialogues_require_combined_evidence():
    section = load_section(PILOT / "q1_v4.json")
    tasks = {task.task_id: task for task in section.tasks}

    d1 = tasks["Q1-D1"]
    lines = [line.pinyin for line in d1.lines]
    assert any("sì diǎn yǐhòu" in line for line in lines)
    assert any("sì diǎn bàn" in line and "sìshí fēnzhōng" in line for line in lines)
    assert d1.answer_slot.correct_option == 3

    d2 = tasks["Q1-D2"]
    assert any("yǎnjing róngyì lèi" in line.pinyin for line in d2.lines)
    assert any("wǎngshàng mǎi kěnéng láibují" in line.pinyin for line in d2.lines)
    assert d2.answer_slot.correct_option == 2


def test_pilot_exam_001_q2_v4_uses_syntax_level_ordering():
    section = load_section(PILOT / "q2_v4.json")
    tasks = {task.task_id: task for task in section.tasks}

    assert tasks["Q2-A"].options == ["推测", "断定", "证明", "保证"]
    assert tasks["Q2-B"].options == ["产生", "造成", "带来", "发挥"]

    c1 = {token.text_zh for token in tasks["Q2-C1"].token_pool}
    assert {"惊讶得", "好一会儿", "都", "说不出话来"}.issubset(c1)
    assert {"过了一会儿", "才", "能够", "说出话来"}.issubset(c1)

    c2 = {token.text_zh for token in tasks["Q2-C2"].token_pool}
    assert {"得", "先", "做完作业", "才能"}.issubset(c2)
    assert {"可以", "不做作业", "就", "马上"}.issubset(c2)

    for task_id in ("Q2-C1", "Q2-C2"):
        task = tasks[task_id]
        long_tokens = [token for token in task.token_pool if len(token.text_zh) >= 6]
        assert len(long_tokens) < 3


def test_pilot_exam_001_q3_v5_uses_balanced_near_miss_answers():
    section = load_section(PILOT / "q3_v5.json")
    answers = [task.answer_slot.correct_option for task in section.tasks]
    assert sorted(answers) == [1, 1, 2, 2, 3, 3, 4, 4]

    tasks = {task.task_id: task for task in section.tasks}
    assert "bù yídìng" in tasks["Q3-A3"].options[0]
    assert "yídìng bùnéng" in tasks["Q3-A3"].options[2]
    assert tasks["Q3-B2"].source_text.startswith("Zhè jiàn shì bú shì")
    assert tasks["Q3-B3"].source_text.count("bú shì") == 1
    assert tasks["Q3-B2"].answer_slot.correct_option == 4
    assert all(tasks["Q3-B2"].distractor_error_types.values())


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


def test_pilot_exam_001_q5_v4_anchors_are_visible_and_answer_range_is_complete():
    section = load_section(PILOT / "q5_v4.json")
    paragraphs = {paragraph.paragraph_id: paragraph.text_zh for paragraph in section.paragraphs}
    for anchor in section.anchors:
        text = paragraphs[anchor.paragraph_id]
        assert anchor.marker_label and anchor.marker_label in text
        if anchor.source_excerpt:
            assert anchor.source_excerpt in text
    numbers = sorted(slot.answer_number for task in section.tasks for slot in task.answer_slots)
    assert numbers == list(range(37, 51))


def test_pilot_exam_001_q5_v4_removes_giveaway_lexical_item_and_diversifies_late_questions():
    section = load_section(PILOT / "q5_v4.json")
    tasks = {task.task_id: task for task in section.tasks}

    q4 = tasks["Q5-Q4"]
    assert q4.options == [
        "请把你的电话号码留给我。",
        "毕业以后，他决定留在这座城市工作。",
        "桌上还留着一张没有署名的纸条。",
        "我们特意给晚到的客人留了两个座位。",
    ]
    assert q4.answer_slots[0].correct_option == 2
    assert "永远" not in q4.options

    assert tasks["Q5-Q9"].answer_slots[0].correct_option == 2
    assert tasks["Q5-Q10"].anchor_refs == ["A3", "A4"]
    assert tasks["Q5-Q11"].operation == "whole_text_consistency"
    assert tasks["Q5-Q10"].prompt_ja != tasks["Q5-Q9"].prompt_ja


def test_pilot_exam_001_manifest_uses_current_revisions():
    manifest = json.loads((PILOT / "exam.json").read_text(encoding="utf-8"))
    paths = {ref["section"]: ref["path"] for ref in manifest["sections"]}
    assert paths == {
        "Q1": "q1_v4.json",
        "Q2": "q2_v4.json",
        "Q3": "q3_v5.json",
        "Q4": "q4_v3.json",
        "Q5": "q5_v4.json",
    }


def test_pilot_exam_001_q5_v4_uses_natural_relationship_wording():
    section = load_section(PILOT / "q5_v4.json")
    paragraphs = {paragraph.paragraph_id: paragraph.text_zh for paragraph in section.paragraphs}

    assert "自己和店里人的关系越来越〔空欄A〕" in paragraphs["P2"]
    assert "四处打听订单进度的时间" in paragraphs["P4"]
    assert "店里的人离自己越来越〔空欄A〕" not in paragraphs["P2"]

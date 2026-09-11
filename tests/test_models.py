from tabito_itemgen.models import Item


def sample_item():
    return {
        "item_id": "TABITO-CN-Q4-TEST",
        "section": "Q4",
        "title_ja": "文化祭の企画",
        "topic": "学校文化祭",
        "difficulty": "medium",
        "materials": [
            {"material_id": "A", "type": "dialogue", "content": "我们下午两点以后都有时间。"},
            {"material_id": "B", "type": "timetable", "content": "书法 14:30\n舞蹈 13:00"},
        ],
        "questions": [
            {
                "question_id": "Q1",
                "prompt_ja": "二人が参加できる活動として最も適当なものを選べ。",
                "options": ["书法", "舞蹈", "午餐", "晨会"],
                "correct_option": 1,
                "operation": "integrate",
                "evidence": {"material_ids": ["A", "B"], "explanation_ja": "会話の条件と時間表を照合する。"},
                "rationale_ja": "14時以降という条件を満たす。",
                "distractor_rationales_ja": {"2": "開始時刻が早い。", "3": "資料にない。", "4": "資料にない。"},
            },
            {
                "question_id": "Q2",
                "prompt_ja": "資料Bについて正しいものを選べ。",
                "options": ["书法比舞蹈晚开始", "舞蹈比书法晚开始", "两者同时开始", "无法判断"],
                "correct_option": 1,
                "operation": "compare",
                "evidence": {"material_ids": ["B"], "explanation_ja": "開始時刻を比較する。"},
                "rationale_ja": "14:30 は 13:00 より遅い。",
                "distractor_rationales_ja": {"2": "順序が逆。", "3": "同時ではない。", "4": "判断可能。"},
            },
            {
                "question_id": "Q3",
                "prompt_ja": "会話から分かることを選べ。",
                "options": ["下午有时间", "上午有时间", "整天没时间", "晚上没时间"],
                "correct_option": 1,
                "operation": "extract",
                "evidence": {"material_ids": ["A"], "explanation_ja": "会話の明示情報。"},
                "rationale_ja": "午後2時以降に時間がある。",
                "distractor_rationales_ja": {"2": "述べていない。", "3": "逆。", "4": "述べていない。"},
            },
            {
                "question_id": "Q4",
                "prompt_ja": "条件に合う時刻を選べ。",
                "options": ["12:00", "13:00", "14:30", "10:00"],
                "correct_option": 3,
                "operation": "condition_match",
                "evidence": {"material_ids": ["A", "B"], "explanation_ja": "14時以降の条件。"},
                "rationale_ja": "14:30 が条件を満たす。",
                "distractor_rationales_ja": {"1": "早すぎる。", "2": "早すぎる。", "4": "早すぎる。"},
            },
        ],
        "quality_notes": {
            "ambiguity_risk": "low",
            "originality_note": "test fixture",
            "language_note": "test fixture",
        },
    }


def test_item_validates():
    item = Item.model_validate(sample_item())
    assert item.section == "Q4"

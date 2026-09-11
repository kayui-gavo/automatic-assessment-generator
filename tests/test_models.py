import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from tabito_itemgen.models import Item, Material, Review

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "q4_example_response.json"


def test_full_example_is_valid_and_has_16_slots():
    item = Item.model_validate(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    numbers = [slot.answer_number for task in item.tasks for slot in task.answer_slots]
    assert numbers == list(range(21, 37))
    assert {m.subsection for m in item.materials} == {"A", "B"}


def test_full_item_rejects_missing_answer_number():
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["tasks"][-1]["answer_slots"][0]["answer_number"] = 37
    with pytest.raises(ValidationError):
        Item.model_validate(data)


def test_review_schema_accepts_multi_slot_answers():
    review = Review.model_validate(
        {
            "schema_version": "0.2",
            "item_id": "X",
            "verdict": "pass",
            "independent_answers": {"A1": [1, 5], "B2": [3, 1, 4]},
            "issues": [],
            "overall_comment_ja": "問題なし",
        }
    )
    assert review.independent_answers["B2"] == [3, 1, 4]


def test_official_like_difficulty_is_supported():
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["difficulty"] = "official_like"
    item = Item.model_validate(data)
    assert item.difficulty == "official_like"


def test_social_feed_material_parses():
    adapter = TypeAdapter(Material)
    material = adapter.validate_python(
        {
            "type": "social_feed",
            "material_id": "B-M1",
            "subsection": "B",
            "order": 1,
            "title": "運行情報",
            "posts": [
                {"date_label": "9月12日", "author": "運営", "body": "午後は混雑します。"},
                {"date_label": "9月13日", "author": "運営", "body": "雨天時は時刻が変わります。"},
            ],
        }
    )
    assert material.type == "social_feed"
    assert len(material.posts) == 2


def test_schematic_map_material_parses():
    adapter = TypeAdapter(Material)
    material = adapter.validate_python(
        {
            "type": "schematic_map",
            "material_id": "B-M2",
            "subsection": "B",
            "order": 2,
            "title": "会場略図",
            "nodes": [
                {"node_id": "A", "label": "駅", "x": 0, "y": 0},
                {"node_id": "B", "label": "会場", "x": 5, "y": 0},
            ],
            "edges": [{"source": "A", "target": "B", "label": "徒歩10分"}],
        }
    )
    assert material.type == "schematic_map"
    assert material.edges[0].label == "徒歩10分"

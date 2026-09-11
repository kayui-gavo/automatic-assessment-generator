import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tabito_itemgen.models import Item, Review

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

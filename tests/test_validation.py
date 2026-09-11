import json
from pathlib import Path

from tabito_itemgen.models import Item, Review
from tabito_itemgen.validate import compare_review, similarity, validate_item_file

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "q4_example_response.json"


def test_example_passes_validation():
    item, errors, warnings = validate_item_file(EXAMPLE)
    assert item is not None
    assert errors == []


def test_blind_review_comparison_detects_wrong_answer():
    item = Item.model_validate(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    answers = {task.task_id: [slot.correct_option for slot in task.answer_slots] for task in item.tasks}
    answers["A3"] = [1]
    review = Review.model_validate(
        {
            "schema_version": "0.2",
            "item_id": item.item_id,
            "verdict": "pass",
            "independent_answers": answers,
            "issues": [],
            "overall_comment_ja": "",
        }
    )
    errors, _ = compare_review(item, review)
    assert any("A3" in error for error in errors)


def test_similarity_is_one_for_same_item():
    item = Item.model_validate(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    assert similarity(item, item) == 1.0

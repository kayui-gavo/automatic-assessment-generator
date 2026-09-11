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


def test_cross_source_mode_rejects_single_evidence_material(tmp_path):
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["workflow"]["blueprint_version"] = "R8-2026-main-tsui-v2"
    data["tasks"][0]["dependency_mode"] = "cross_source"
    assert len(data["tasks"][0]["evidence"]) == 1
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _, errors, _ = validate_item_file(path)
    assert any("cross_source requires at least two materials" in error for error in errors)


def test_within_compound_accepts_shared_bundle(tmp_path):
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["workflow"]["blueprint_version"] = "R8-2026-main-tsui-v2"
    data["materials"][0]["bundle_id"] = "A-BUNDLE"
    data["materials"][1]["bundle_id"] = "A-BUNDLE"
    data["tasks"][1]["dependency_mode"] = "within_compound"
    path = tmp_path / "compound.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _, errors, _ = validate_item_file(path)
    assert not any("within_compound" in error for error in errors)


def test_old_blueprint_version_is_warning_not_error():
    item, errors, warnings = validate_item_file(EXAMPLE)
    assert item is not None
    assert errors == []
    assert any("blueprint_version" in warning for warning in warnings)

import json
from pathlib import Path

import pytest

from tabito_itemgen.io import load_json
from tabito_itemgen.models import HumanQA, HumanQAChecks, HumanQATiming, Item, Review
from tabito_itemgen.production import (
    approve_item,
    human_qa_errors,
    import_item_response,
    import_review_response,
    parse_chat_json,
    release_readiness,
    save_draft,
    save_human_qa,
)

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "q4_pilot_002_library_study_main2026.json"


def _root(tmp_path: Path) -> Path:
    for relative in [
        "workspace/responses",
        "workspace/reviews",
        "workspace/human_qa",
        "item_bank/draft",
        "item_bank/approved",
    ]:
        (tmp_path / relative).mkdir(parents=True, exist_ok=True)
    return tmp_path


def _item() -> Item:
    return Item.model_validate(load_json(PILOT))


def _review(item: Item) -> Review:
    return Review(
        item_id=item.item_id,
        verdict="pass",
        independent_answers={
            task.task_id: [slot.correct_option for slot in task.answer_slots]
            for task in item.tasks
        },
        issues=[],
        overall_comment_ja="独立解答と正答は一致し、重大な問題はない。",
    )


def _qa(item: Item, **overrides) -> HumanQA:
    data = {
        "item_id": item.item_id,
        "reviewer": "QA reviewer",
        "disposition": "approve",
        "checks": HumanQAChecks(**{name: True for name in HumanQAChecks.model_fields}),
        "timing": HumanQATiming(first_read_minutes=8, item_edit_minutes=5),
    }
    data.update(overrides)
    return HumanQA(**data)


def test_parse_chat_json_accepts_plain_or_single_json_fence():
    assert parse_chat_json('{"x": 1}') == {"x": 1}
    assert parse_chat_json('```json\n{"x": 1}\n```') == {"x": 1}


def test_parse_chat_json_rejects_surrounding_commentary():
    with pytest.raises(json.JSONDecodeError):
        parse_chat_json('Here is the JSON:\n{"x": 1}')


def test_import_item_and_review_are_persisted(tmp_path):
    root = _root(tmp_path)
    text = PILOT.read_text(encoding="utf-8")
    item, response_path, draft_path, errors, _ = import_item_response(root, text)
    assert response_path.exists()
    assert draft_path.exists()
    assert draft_path.name == f"{item.item_id}.json"
    assert not errors

    review = _review(item)
    imported_review, review_path = import_review_response(
        root, json.dumps(review.model_dump(), ensure_ascii=False)
    )
    assert imported_review.item_id == item.item_id
    assert review_path.exists()


def test_human_qa_blocks_release_when_required_check_fails():
    item = _item()
    checks = {name: True for name in HumanQAChecks.model_fields}
    checks["answer_uniqueness"] = False
    qa = _qa(item, checks=HumanQAChecks(**checks))
    errors = human_qa_errors(item, qa)
    assert any("answer_uniqueness" in error for error in errors)


def test_release_requires_review_and_human_qa(tmp_path):
    root = _root(tmp_path)
    item_path = save_draft(root, _item())
    item = Item.model_validate(load_json(item_path))

    readiness = release_readiness(root, item_path)
    assert not readiness.ready
    assert {gate.name for gate in readiness.gates if not gate.passed} == {
        "blind review",
        "human QA",
    }

    import_review_response(
        root, json.dumps(_review(item).model_dump(), ensure_ascii=False)
    )
    save_human_qa(root, _qa(item))
    readiness = release_readiness(root, item_path)
    assert readiness.ready


def test_approve_writes_canonical_approved_state(tmp_path):
    root = _root(tmp_path)
    item_path = save_draft(root, _item())
    item = Item.model_validate(load_json(item_path))
    import_review_response(
        root, json.dumps(_review(item).model_dump(), ensure_ascii=False)
    )
    save_human_qa(root, _qa(item))

    target, readiness = approve_item(root, item_path)
    assert readiness.ready
    approved = Item.model_validate(load_json(target))
    assert approved.workflow.state == "approved"
    assert target.parent == root / "item_bank" / "approved"

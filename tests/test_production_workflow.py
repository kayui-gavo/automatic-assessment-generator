import json
from pathlib import Path

import pytest

from tabito_itemgen.io import dump_json, load_json
from tabito_itemgen.models import HumanQA, HumanQAChecks, Item, Review
from tabito_itemgen.production import (
    approve_item,
    import_item_response,
    import_review_response,
    item_fingerprint,
    parse_chat_json,
    release_readiness,
    release_record_path,
    save_draft,
    save_human_qa,
)

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "q4_pilot_002_library_study_main2026.json"


def _item() -> Item:
    return Item.model_validate(json.loads(PILOT.read_text(encoding="utf-8")))


def _review(item: Item) -> Review:
    return Review(
        item_id=item.item_id,
        verdict="pass",
        independent_answers={
            task.task_id: [slot.correct_option for slot in task.answer_slots]
            for task in item.tasks
        },
        issues=[],
        overall_comment_ja="独立解答は著者キーと一致した。",
    )


def _qa(item: Item) -> HumanQA:
    checks = {name: True for name in HumanQAChecks.model_fields}
    return HumanQA(
        item_id=item.item_id,
        reviewer="QA Reviewer",
        disposition="approve",
        checks=HumanQAChecks(**checks),
    )


def test_parse_chat_json_accepts_one_code_fence_but_rejects_surrounding_prose():
    assert parse_chat_json('```json\n{"x": 1}\n```') == {"x": 1}
    with pytest.raises(json.JSONDecodeError):
        parse_chat_json('Here you go:\n```json\n{"x": 1}\n```')


def test_import_response_is_bound_to_request_and_forces_draft_state(tmp_path: Path):
    item = _item()
    item.workflow.state = "approved"
    text = item.model_dump_json()

    imported, response_path, draft_path, _, _ = import_item_response(
        tmp_path,
        text,
        expected_item_id=item.item_id,
        expected_surface_family=item.surface_family,
        expected_blueprint_version=item.workflow.blueprint_version,
    )

    assert imported.workflow.state == "draft"
    assert response_path.exists()
    assert draft_path.exists()
    assert load_json(draft_path)["workflow"]["state"] == "draft"

    with pytest.raises(ValueError, match="item_id"):
        import_item_response(tmp_path, text, expected_item_id="WRONG-ID")


def test_fingerprint_ignores_state_but_tracks_blueprint_and_content():
    item = _item()
    baseline = item_fingerprint(item)

    state_only = item.model_copy(deep=True)
    state_only.workflow.state = "approved"
    assert item_fingerprint(state_only) == baseline

    blueprint_changed = item.model_copy(deep=True)
    blueprint_changed.workflow.blueprint_version += "-changed"
    assert item_fingerprint(blueprint_changed) != baseline

    wording_changed = item.model_copy(deep=True)
    wording_changed.tasks[0].prompt_ja += "（改）"
    assert item_fingerprint(wording_changed) != baseline


def test_review_and_human_qa_become_stale_after_candidate_edit(tmp_path: Path):
    item = _item()
    draft_path = save_draft(tmp_path, item)
    current = Item.model_validate(load_json(draft_path))

    import_review_response(tmp_path, _review(current).model_dump_json(), item=current)
    save_human_qa(tmp_path, _qa(current), item=current)

    ready = release_readiness(tmp_path, draft_path)
    assert ready.ready

    changed = current.model_copy(deep=True)
    changed.tasks[0].prompt_ja += "（修正版）"
    changed_path = tmp_path / "changed.json"
    dump_json(changed_path, changed.model_dump())

    stale = release_readiness(tmp_path, changed_path)
    gates = {gate.name: gate for gate in stale.gates}
    assert not gates["blind review"].passed
    assert "changed after blind review" in gates["blind review"].detail
    assert not gates["human QA"].passed
    assert "changed after human QA" in gates["human QA"].detail


def test_approve_is_a_release_transaction(tmp_path: Path):
    item = _item()
    draft_path = save_draft(tmp_path, item)
    current = Item.model_validate(load_json(draft_path))
    import_review_response(tmp_path, _review(current).model_dump_json(), item=current)
    save_human_qa(tmp_path, _qa(current), item=current)

    target, readiness = approve_item(tmp_path, draft_path)

    assert readiness.ready
    assert target.exists()
    approved = Item.model_validate(load_json(target))
    assert approved.workflow.state == "approved"
    assert not draft_path.exists()

    record_path = release_record_path(tmp_path, item.item_id)
    assert record_path.exists()
    record = load_json(record_path)
    assert record["item_fingerprint"] == item_fingerprint(approved)
    assert all(gate["passed"] for gate in record["gates"])

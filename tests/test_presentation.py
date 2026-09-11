import json
from pathlib import Path

from tabito_itemgen.models import Item
from tabito_itemgen.presentation import (
    question_number,
    slot_group_summary,
    subsection_intro,
    task_groups,
)

ROOT = Path(__file__).resolve().parents[1]
MAIN_PILOT = ROOT / "pilots" / "q4_pilot_002_library_study_main2026.json"
MAKEUP_PILOT = ROOT / "pilots" / "q4_pilot_003_stargazing_makeup2026_v2.json"


def _load(path: Path) -> Item:
    return Item.model_validate(json.loads(path.read_text(encoding="utf-8")))


def test_surface_family_survives_model_roundtrip():
    item = _load(MAIN_PILOT)
    assert item.surface_family == "main_2026"
    assert item.model_dump()["surface_family"] == "main_2026"


def test_current_workflow_default_is_v3():
    data = json.loads(MAIN_PILOT.read_text(encoding="utf-8"))
    data.pop("workflow", None)
    item = Item.model_validate(data)
    assert item.workflow.blueprint_version == "R8-2026-main-tsui-v3"


def test_main_booklet_question_groups_match_2026_surface():
    item = _load(MAIN_PILOT)
    a = task_groups(item, "A")
    b = task_groups(item, "B")
    assert [[sorted(slot.answer_number for slot in task.answer_slots) for task in a[q]] for q in (1, 2, 3)] == [
        [[21, 22]],
        [[23, 24], [25], [26]],
        [[27, 28]],
    ]
    assert [[sorted(slot.answer_number for slot in task.answer_slots) for task in b[q]] for q in (1, 2, 3)] == [
        [[29, 30]],
        [[31, 32], [33]],
        [[34], [35, 36]],
    ]


def test_makeup_booklet_question_groups_match_2026_surface():
    item = _load(MAKEUP_PILOT)
    a = task_groups(item, "A")
    b = task_groups(item, "B")
    assert [[sorted(slot.answer_number for slot in task.answer_slots) for task in a[q]] for q in (1, 2, 3)] == [
        [[21, 22]],
        [[23, 24], [25, 26]],
        [[27, 28]],
    ]
    assert [[sorted(slot.answer_number for slot in task.answer_slots) for task in b[q]] for q in (1, 2, 3)] == [
        [[29, 30]],
        [[31, 32], [33, 34]],
        [[35, 36]],
    ]


def test_intro_fallback_is_human_readable_for_legacy_pilots():
    item = _load(MAIN_PILOT)
    assert "問1～3" in subsection_intro(item, "A")
    assert item.title_ja in subsection_intro(item, "A")
    assert "別の場面" in subsection_intro(item, "B")


def test_slot_summary_is_readable():
    item = _load(MAIN_PILOT)
    summary = slot_group_summary(item)
    assert "A 問1: 21-22" in summary
    assert "B 問3: 34 / 35-36" in summary


def test_question_number_is_derived_from_surface_family():
    item = _load(MAKEUP_PILOT)
    task = next(task for task in item.tasks if task.task_id == "B2b")
    assert question_number(item.surface_family, "B", task) == 2

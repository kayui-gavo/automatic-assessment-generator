from pathlib import Path

from tabito_itemgen.validate import validate_item_file

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "q4_pilot_002_library_study_main2026.json"


def test_pilot_002_passes_v3_main_surface_validation():
    item, errors, warnings = validate_item_file(PILOT)
    assert item is not None
    assert errors == []
    assert item.workflow.blueprint_version == "R8-2026-main-tsui-v3"
    assert sum(len(task.answer_slots) for task in item.tasks) == 16


def test_pilot_002_exact_main_slot_groups():
    item, errors, _ = validate_item_file(PILOT)
    assert item is not None and errors == []
    groups = {
        frozenset(slot.answer_number for slot in task.answer_slots)
        for task in item.tasks
    }
    assert groups == {
        frozenset({21, 22}),
        frozenset({23, 24}),
        frozenset({25}),
        frozenset({26}),
        frozenset({27, 28}),
        frozenset({29, 30}),
        frozenset({31, 32}),
        frozenset({33}),
        frozenset({34}),
        frozenset({35, 36}),
    }

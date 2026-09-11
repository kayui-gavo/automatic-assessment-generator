from pathlib import Path

from tabito_itemgen.validate import validate_item_file

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "q4_pilot_003_stargazing_makeup2026.json"


def test_pilot_003_passes_v3_surface_validation():
    item, errors, warnings = validate_item_file(PILOT)
    assert item is not None
    assert errors == []
    assert sum(len(task.answer_slots) for task in item.tasks) == 16


def test_pilot_003_matches_makeup_2026_slot_groups():
    item, errors, _ = validate_item_file(PILOT)
    assert item is not None and errors == []

    a_groups = {
        frozenset(slot.answer_number for slot in task.answer_slots)
        for task in item.tasks
        if task.subsection == "A"
    }
    b_groups = {
        frozenset(slot.answer_number for slot in task.answer_slots)
        for task in item.tasks
        if task.subsection == "B"
    }

    assert a_groups == {
        frozenset({21, 22}),
        frozenset({23, 24}),
        frozenset({25, 26}),
        frozenset({27, 28}),
    }
    assert b_groups == {
        frozenset({29, 30}),
        frozenset({31, 32}),
        frozenset({33, 34}),
        frozenset({35, 36}),
    }


def test_pilot_003_contains_makeup_operational_and_reflection_sources():
    item, errors, _ = validate_item_file(PILOT)
    assert item is not None and errors == []
    types = {material.type for material in item.materials}
    assert "social_feed" in types
    assert "schematic_map" in types
    assert "annotated_diagram" in types
    assert "reflection" in types

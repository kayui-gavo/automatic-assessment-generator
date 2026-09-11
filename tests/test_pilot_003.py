import re
from pathlib import Path

from tabito_itemgen.validate import validate_item_file

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "q4_pilot_003_stargazing_makeup2026_v2.json"
KANA_RE = re.compile(r"[\u3040-\u30ff]")


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


def test_pilot_003_option_language_matches_makeup_exam_face():
    item, errors, _ = validate_item_file(PILOT)
    assert item is not None and errors == []
    by_slots = {
        tuple(slot.answer_number for slot in task.answer_slots): task
        for task in item.tasks
    }

    # 23-24 is the conspicuous Chinese graph-verification block in the 2026 makeup paper.
    assert not any(KANA_RE.search(option) for option in by_slots[(23, 24)].options)

    # The surrounding meaning-verification blocks use Japanese options in the actual paper.
    for slots in [(21, 22), (25, 26), (27, 28), (31, 32), (33, 34), (35, 36)]:
        assert all(KANA_RE.search(option) for option in by_slots[slots].options)

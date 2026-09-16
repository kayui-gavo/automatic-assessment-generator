from pathlib import Path

import yaml

from tabito_itemgen.scoring import SCORING_VERSION, scoring_scheme

ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = ROOT / "blueprints" / "scoring_2026.yaml"


def _rule_groups(rule: dict) -> list[tuple[str, tuple[int, ...], int, str, str]]:
    section = rule["section"]
    numbers = tuple(int(value) for value in rule["answer_numbers"])
    mode = rule["mode"]

    if mode == "independent":
        points_each = int(rule["points_per_correct"])
        return [
            (section, (number,), points_each, "all_or_nothing", "ordered")
            for number in numbers
        ]
    if mode == "ordered_all_or_nothing":
        return [
            (section, numbers, int(rule["max_points"]), "all_or_nothing", "ordered")
        ]
    if mode == "unordered_all_or_nothing":
        return [(section, numbers, int(rule["max_points"]), "all_or_nothing", "set")]
    if mode == "unordered_per_correct":
        return [(section, numbers, int(rule["max_points"]), "per_choice", "set")]
    raise AssertionError(f"unknown scoring blueprint mode: {mode}")


def _blueprint_groups(payload: dict, family: str):
    groups = []
    for rule in payload["shared_rules"]:
        groups.extend(_rule_groups(rule))
    for rule in payload["families"][family]["rules"]:
        groups.extend(_rule_groups(rule))
    return sorted(groups, key=lambda row: row[1])


def _engine_groups(family: str):
    return sorted(
        [
            (
                group.section,
                group.answer_numbers,
                group.points,
                group.award_mode,
                group.comparison_mode,
            )
            for group in scoring_scheme(family).groups
        ],
        key=lambda row: row[1],
    )


def test_scoring_blueprint_and_engine_are_exactly_aligned() -> None:
    payload = yaml.safe_load(BLUEPRINT.read_text(encoding="utf-8"))
    assert payload["scoring_version"] == SCORING_VERSION
    assert payload["total_score"] == 200
    assert payload["section_totals"] == {
        "Q1": 24,
        "Q2": 16,
        "Q3": 40,
        "Q4": 60,
        "Q5": 60,
    }

    for family in ("main_2026", "makeup_2026"):
        assert _blueprint_groups(payload, family) == _engine_groups(family)

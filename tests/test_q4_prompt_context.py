from pathlib import Path

import yaml

from tabito_itemgen.exam_generate import Q4_BLUEPRINT_VERSION, _q4_context
from tabito_itemgen.generate_request import BLUEPRINT_VERSION, _reference_context

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = "R8-2026-main-tsui-v4"


def test_current_q4_production_sources_share_one_baseline_version():
    assert Q4_BLUEPRINT_VERSION == EXPECTED
    assert BLUEPRINT_VERSION == EXPECTED

    assert yaml.safe_load(
        (ROOT / "blueprints" / "common_test_chinese.yaml").read_text(encoding="utf-8")
    )["exam"]["blueprint_version"] == EXPECTED
    assert yaml.safe_load(
        (ROOT / "blueprints" / "q4_2026_generation_profile.yaml").read_text(
            encoding="utf-8"
        )
    )["baseline_version"] == EXPECTED
    assert yaml.safe_load(
        (ROOT / "blueprints" / "q4_2026_reference_patterns.yaml").read_text(
            encoding="utf-8"
        )
    )["baseline_version"] == EXPECTED
    assert yaml.safe_load(
        (ROOT / "templates" / "q4.yaml").read_text(encoding="utf-8")
    )["baseline"] == EXPECTED


def test_q4_authoring_context_is_compact_and_generation_safe():
    expected_keys = {"generation_profile_yaml", "template_yaml"}
    assert set(_q4_context(ROOT)) == expected_keys
    assert set(_reference_context(ROOT)) == expected_keys


def test_q4_generation_prompt_uses_safe_profile_not_detailed_official_sequence():
    prompt = (ROOT / "prompts" / "generate_q4.md").read_text(encoding="utf-8")

    assert "{{ generation_profile_yaml }}" in prompt
    assert "{{ template_yaml }}" in prompt
    assert "{{ item_spec_json }}" in prompt

    assert "{{ reference_patterns_yaml }}" not in prompt
    assert "{{ blueprint_yaml }}" not in prompt
    assert "{{ surface_grammar }}" not in prompt
    assert "{{ item_writing_direction }}" not in prompt
    assert "R8-2026-main-tsui-v3" not in prompt


def test_detailed_reference_patterns_are_reviewer_only():
    generation = (ROOT / "prompts" / "generate_q4.md").read_text(encoding="utf-8")
    revision = (ROOT / "prompts" / "revise_q4.md").read_text(encoding="utf-8")
    review = (ROOT / "prompts" / "review_q4.md").read_text(encoding="utf-8")

    assert "{{ reference_patterns_yaml }}" not in generation
    assert "{{ reference_patterns_yaml }}" not in revision
    assert "{{ reference_patterns_yaml }}" in review

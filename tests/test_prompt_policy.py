from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_generation_prompt_uses_generation_safe_profile_not_detailed_sequence():
    text = (ROOT / "prompts" / "generate_q4.md").read_text(encoding="utf-8")
    assert "{{ generation_profile_yaml }}" in text
    assert "{{ reference_patterns_yaml }}" not in text


def test_revision_prompt_uses_generation_safe_profile_not_detailed_sequence():
    text = (ROOT / "prompts" / "revise_q4.md").read_text(encoding="utf-8")
    assert "{{ generation_profile_yaml }}" in text
    assert "{{ reference_patterns_yaml }}" not in text


def test_blind_review_can_use_detailed_reference_patterns_for_audit():
    text = (ROOT / "prompts" / "review_q4.md").read_text(encoding="utf-8")
    assert "{{ reference_patterns_yaml }}" in text

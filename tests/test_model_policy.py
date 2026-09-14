from tabito_itemgen.model_policy import (
    MIN_REASONING_LEVEL,
    POLICY_VERSION,
    PREFERRED_MODEL,
    execution_protocol,
    profile_for,
    reasoning_is_review_grade,
)


def test_production_policy_uses_sol_high():
    assert POLICY_VERSION
    assert PREFERRED_MODEL == "GPT-5.6 Sol"
    assert MIN_REASONING_LEVEL == "high"
    for stage in ("generate", "review", "revision"):
        profile = profile_for(stage)
        assert profile.model_label == PREFERRED_MODEL
        assert profile.reasoning_level == "high"


def test_blind_review_requires_fresh_chat_but_generation_revision_only_recommend_it():
    assert profile_for("review").fresh_chat == "required"
    assert profile_for("generate").fresh_chat == "recommended"
    assert profile_for("revision").fresh_chat == "recommended"

    protocol = execution_protocol("review", "Q4")
    assert "MUST use a fresh chat" in protocol
    assert "Do not use Instant / low-effort mode" in protocol
    assert "answer keys" in protocol


def test_only_high_or_stronger_reasoning_is_review_grade():
    assert not reasoning_is_review_grade("instant")
    assert not reasoning_is_review_grade("medium")
    assert not reasoning_is_review_grade("unknown")
    assert reasoning_is_review_grade("high")
    assert reasoning_is_review_grade("extra_high")
    assert reasoning_is_review_grade("pro")

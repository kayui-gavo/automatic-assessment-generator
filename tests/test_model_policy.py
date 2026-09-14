from tabito_itemgen.model_policy import (
    MIN_REASONING_LEVEL,
    POLICY_VERSION,
    PREFERRED_MODEL,
    context_is_memory_isolated,
    execution_is_review_grade,
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


def test_blind_review_requires_memory_isolated_context():
    assert profile_for("review").fresh_chat == "required"
    assert profile_for("generate").fresh_chat == "recommended"
    assert profile_for("revision").fresh_chat == "recommended"

    protocol = execution_protocol("review", "Q4")
    assert "MUST use an independent context" in protocol
    assert "non-personalized Temporary Chat" in protocol
    assert "ordinary new chat is not sufficient" in protocol
    assert "Do not use Instant / low-effort mode" in protocol
    assert "answer keys" in protocol

    assert context_is_memory_isolated("non_personalized_temporary_chat")
    assert context_is_memory_isolated("stateless_api")
    assert context_is_memory_isolated("other_memory_isolated")
    assert not context_is_memory_isolated("unknown")


def test_only_high_or_stronger_reasoning_is_review_grade():
    assert not reasoning_is_review_grade("instant")
    assert not reasoning_is_review_grade("medium")
    assert not reasoning_is_review_grade("unknown")
    assert reasoning_is_review_grade("high")
    assert reasoning_is_review_grade("extra_high")
    assert reasoning_is_review_grade("pro")


def test_review_grade_requires_an_allowed_model_reasoning_pair():
    assert execution_is_review_grade("GPT-5.6 Sol", "high")
    assert execution_is_review_grade("GPT-5.6 Sol", "extra_high")
    assert execution_is_review_grade("GPT-5.6 Sol Pro", "pro")
    assert execution_is_review_grade("GPT-6 Pro", "pro")

    assert not execution_is_review_grade("GPT-5.6 Sol", "medium")
    assert not execution_is_review_grade("GPT-5.6 Sol", "pro")
    assert not execution_is_review_grade("GPT-5.6 Luna", "high")
    assert not execution_is_review_grade("unknown-model", "high")

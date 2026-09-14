from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Stage = Literal["generate", "review", "revision"]

POLICY_VERSION = "manual-chat-sol-high-2026-09-v1"
PREFERRED_MODEL = "GPT-5.6 Sol"
MIN_REASONING_LEVEL = "high"
ACCEPTED_REVIEW_REASONING = frozenset({"high", "extra_high", "pro"})
REVIEW_MODEL_REASONING: dict[str, frozenset[str]] = {
    "GPT-5.6 Sol": frozenset({"high", "extra_high"}),
    "GPT-5.6 Sol Pro": frozenset({"pro"}),
    "GPT-6 Pro": frozenset({"pro"}),
}


@dataclass(frozen=True)
class ExecutionProfile:
    stage: Stage
    model_label: str
    reasoning_level: str
    fresh_chat: Literal["required", "recommended"]
    context_rule: str


PROFILES: dict[Stage, ExecutionProfile] = {
    "generate": ExecutionProfile(
        stage="generate",
        model_label=PREFERRED_MODEL,
        reasoning_level=MIN_REASONING_LEVEL,
        fresh_chat="recommended",
        context_rule=(
            "Use a clean authoring chat when practical. Never reuse the authoring chat as the "
            "blind-review chat for the same candidate."
        ),
    ),
    "review": ExecutionProfile(
        stage="review",
        model_label=PREFERRED_MODEL,
        reasoning_level=MIN_REASONING_LEVEL,
        fresh_chat="required",
        context_rule=(
            "Run this request in a new chat that has not seen generation, revision, answer keys, "
            "rationales, or teacher annotations for this candidate."
        ),
    ),
    "revision": ExecutionProfile(
        stage="revision",
        model_label=PREFERRED_MODEL,
        reasoning_level=MIN_REASONING_LEVEL,
        fresh_chat="recommended",
        context_rule=(
            "Prefer a fresh revision chat containing only the current candidate, the blind-review "
            "result, and the revision request. Do not reuse the revision chat for the next blind review."
        ),
    ),
}


def profile_for(stage: Stage) -> ExecutionProfile:
    return PROFILES[stage]


def reasoning_is_review_grade(reasoning_level: str) -> bool:
    return reasoning_level.strip().lower() in ACCEPTED_REVIEW_REASONING


def execution_is_review_grade(model_label: str, reasoning_level: str) -> bool:
    allowed = REVIEW_MODEL_REASONING.get(model_label.strip())
    return allowed is not None and reasoning_level.strip().lower() in allowed


def execution_protocol(stage: Stage, section: str) -> str:
    profile = profile_for(stage)
    freshness = "MUST" if profile.fresh_chat == "required" else "SHOULD"
    return "\n".join(
        [
            "# Operator execution protocol",
            "",
            f"- policy: `{POLICY_VERSION}`",
            f"- stage: `{stage}` · section: `{section}`",
            f"- preferred model: **{profile.model_label}**",
            f"- reasoning: **{profile.reasoning_level.title()} or stronger**",
            f"- chat isolation: **{freshness} use a fresh chat**",
            f"- context rule: {profile.context_rule}",
            "- Do not use Instant / low-effort mode for production generation, review, or revision.",
            "",
            "For Blind Review, the saved model/reasoning combination must satisfy the current "
            "production policy. Model strength does not replace deterministic validation, blind "
            "solving, Human QA, or PDF preflight.",
        ]
    )

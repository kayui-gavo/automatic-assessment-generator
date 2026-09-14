from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .exam_models import SectionKind
from .models import ReviewIssue


class SectionReview(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    section: SectionKind
    section_id: str
    candidate_fingerprint: str = Field(min_length=64, max_length=64)
    verdict: Literal["pass", "revise", "reject"]
    independent_answers: dict[str, list[int]]
    issues: list[ReviewIssue] = Field(default_factory=list)
    overall_comment_ja: str


class ReviewExecution(BaseModel):
    """Operator-recorded provenance for one blind-review run.

    The reviewer model cannot prove that it ran in a fresh chat, so this record is
    intentionally saved by the production workflow rather than emitted by the model.
    """

    schema_version: Literal["0.1"] = "0.1"
    section: SectionKind
    section_id: str
    candidate_fingerprint: str = Field(min_length=64, max_length=64)
    policy_version: str = Field(min_length=1)
    model_label: str = Field(min_length=1)
    reasoning_level: Literal["instant", "medium", "high", "extra_high", "pro", "unknown"]
    fresh_chat_confirmed: bool = False
    authoring_context_seen: bool = False


class SectionQAChecks(BaseModel):
    chinese_naturalness: bool = False
    japanese_instruction_naturalness: bool = False
    answer_uniqueness: bool = False
    distractors_plausible: bool = False
    surface_fidelity_2026: bool = False
    official_difficulty_calibrated: bool = False
    shortcut_resistance: bool = False
    originality_ok: bool = False
    layout_readable: bool = False
    no_solution_leak: bool = False


class SectionQATiming(BaseModel):
    first_read_minutes: int = Field(default=0, ge=0, le=600)
    language_edit_minutes: int = Field(default=0, ge=0, le=600)
    item_edit_minutes: int = Field(default=0, ge=0, le=600)
    layout_edit_minutes: int = Field(default=0, ge=0, le=600)


class SectionHumanQA(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    section: SectionKind
    section_id: str
    candidate_fingerprint: str = Field(min_length=64, max_length=64)
    reviewer: str = Field(min_length=1)
    disposition: Literal["approve", "revise", "reject"]
    checks: SectionQAChecks
    section_specific_checks: dict[str, bool] = Field(default_factory=dict)
    defects: list[str] = Field(default_factory=list)
    timing: SectionQATiming = Field(default_factory=SectionQATiming)
    biggest_rework_cause: str = ""
    note: str = ""


SECTION_SPECIFIC_QA: dict[str, tuple[str, ...]] = {
    "Q1": (
        "pinyin_correctness",
        "initial_final_analysis_correctness",
        "target_character_underlining_correct",
        "pinyin_hidden_in_student_a_b_c",
        "tone_correctness",
        "yi_bu_tone_sandhi_handling",
        "polyphone_context_unambiguous",
        "pinyin_diacritic_layout",
        "dialogue_naturalness",
        "lexical_load_official_like",
        "phonetic_confusability_sufficient",
        "no_visual_counting_shortcut",
    ),
    "Q2": (
        "lexical_usage_correct",
        "inappropriate_rule_unambiguous",
        "ordering_unique",
        "token_pool_natural",
        "ordering_token_granularity",
        "ordering_requires_syntax",
        "distractor_tokens_locally_plausible",
    ),
    "Q3": (
        "pinyin_correctness",
        "translation_semantics_correct",
        "distractor_error_taxonomy_correct",
        "not_word_for_word_only",
        "near_miss_distractors",
        "no_keyword_shortcut",
        "semantic_operation_diversity",
    ),
    "Q4": (
        "information_journey",
        "visual_materials_necessary",
        "source_integrity_ok",
        "surface_family_correct",
        "cross_source_dependency_real",
        "cognitive_operation_diversity",
        "template_repetition_risk_checked",
    ),
    "Q5": (
        "article_naturalness",
        "paragraph_coherence",
        "anchor_accuracy",
        "whole_text_reasoning_quality",
        "lexical_distractor_strength",
        "local_options_compete",
        "late_question_operation_diversity",
        "copyright_originality_check",
        "long_text_pagination_readable",
    ),
}

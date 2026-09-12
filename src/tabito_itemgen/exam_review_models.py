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


class SectionQAChecks(BaseModel):
    chinese_naturalness: bool = False
    japanese_instruction_naturalness: bool = False
    answer_uniqueness: bool = False
    distractors_plausible: bool = False
    surface_fidelity_2026: bool = False
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
        "tone_correctness",
        "yi_bu_tone_sandhi_handling",
        "polyphone_context_unambiguous",
        "pinyin_diacritic_layout",
        "dialogue_naturalness",
    ),
    "Q2": (
        "lexical_usage_correct",
        "inappropriate_rule_unambiguous",
        "ordering_unique",
        "token_pool_natural",
    ),
    "Q3": (
        "pinyin_correctness",
        "translation_semantics_correct",
        "distractor_error_taxonomy_correct",
        "not_word_for_word_only",
    ),
    "Q4": (
        "information_journey",
        "visual_materials_necessary",
        "source_integrity_ok",
        "surface_family_correct",
    ),
    "Q5": (
        "article_naturalness",
        "paragraph_coherence",
        "anchor_accuracy",
        "whole_text_reasoning_quality",
        "copyright_originality_check",
        "long_text_pagination_readable",
    ),
}

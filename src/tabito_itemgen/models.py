from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator

Difficulty = Literal["easy", "medium", "hard"]
Operation = Literal["extract", "compare", "condition_match", "integrate", "infer", "sequence"]


class Material(BaseModel):
    material_id: str
    type: str
    title: str | None = None
    content: str


class Evidence(BaseModel):
    material_ids: list[str] = Field(min_length=1)
    explanation_ja: str


class Question(BaseModel):
    question_id: str
    prompt_ja: str
    options: list[str] = Field(min_length=4, max_length=5)
    correct_option: int = Field(ge=1, le=5)
    operation: Operation
    evidence: Evidence
    rationale_ja: str
    distractor_rationales_ja: dict[str, str]

    @model_validator(mode="after")
    def validate_correct_option(self) -> "Question":
        if self.correct_option > len(self.options):
            raise ValueError("correct_option exceeds number of options")
        if len(set(self.options)) != len(self.options):
            raise ValueError("duplicate options are not allowed")
        return self


class QualityNotes(BaseModel):
    ambiguity_risk: str
    originality_note: str
    language_note: str


class Item(BaseModel):
    item_id: str
    section: Literal["Q4"]
    title_ja: str
    topic: str
    difficulty: Difficulty
    materials: list[Material] = Field(min_length=2, max_length=4)
    questions: list[Question] = Field(min_length=4, max_length=10)
    quality_notes: QualityNotes

    @model_validator(mode="after")
    def validate_ids_and_evidence(self) -> "Item":
        material_ids = [m.material_id for m in self.materials]
        if len(material_ids) != len(set(material_ids)):
            raise ValueError("material_id values must be unique")
        question_ids = [q.question_id for q in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("question_id values must be unique")
        known = set(material_ids)
        for q in self.questions:
            missing = set(q.evidence.material_ids) - known
            if missing:
                raise ValueError(f"{q.question_id}: unknown evidence material ids: {sorted(missing)}")
        return self


class ReviewIssue(BaseModel):
    severity: Literal["high", "medium", "low"]
    question_id: str | None = None
    category: str
    description: str
    suggested_fix: str


class Review(BaseModel):
    item_id: str
    verdict: Literal["pass", "revise", "reject"]
    independent_answers: dict[str, int]
    issues: list[ReviewIssue]
    overall_comment_ja: str

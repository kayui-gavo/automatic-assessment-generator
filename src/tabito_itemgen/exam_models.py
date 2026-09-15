from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from .models import AnswerSlot, Item, WorkflowMeta

SectionKind = Literal["Q1", "Q2", "Q3", "Q4", "Q5"]
ExamFamily = Literal["main_2026", "makeup_2026"]
SectionState = Literal["not_generated", "draft", "reviewed", "ready", "approved"]

SECTION_SPECS: dict[str, tuple[int, int, int]] = {
    "Q1": (24, 1, 6),
    "Q2": (16, 7, 12),
    "Q3": (40, 13, 20),
    "Q4": (60, 21, 36),
    "Q5": (60, 37, 50),
}


class SectionWorkflowMeta(BaseModel):
    state: Literal["draft", "reviewed", "approved"] = "draft"
    generation_mode: Literal["manual_chat"] = "manual_chat"
    blueprint_version: str = "R8-2026-full-v1"


class PinyinWord(BaseModel):
    label: str
    hanzi: str
    pinyin: str
    # 1-based character position underlined on the student booklet for Q1 A/B.
    # C compares the tone pattern of the whole word and normally leaves this null.
    target_index: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_target_index(self) -> PinyinWord:
        if self.target_index is not None and self.target_index > len(self.hanzi):
            raise ValueError("PinyinWord target_index exceeds hanzi length")
        return self


class Q1PhoneticCountTask(BaseModel):
    task_type: Literal["phonetic_count"] = "phonetic_count"
    task_id: str
    subsection: Literal["A", "B", "C"]
    order: int = Field(ge=1)
    target: Literal["initial", "final", "tone_pattern"]
    prompt_ja: str
    headword: PinyinWord
    candidates: list[PinyinWord] = Field(min_length=4, max_length=4)
    options: list[str] = Field(default_factory=lambda: ["一つ", "二つ", "三つ", "四つ", "なし"], min_length=5, max_length=5)
    answer_slot: AnswerSlot
    rationale_ja: str
    distractor_rationales_ja: dict[str, str] = Field(default_factory=dict)


class PinyinDialogueLine(BaseModel):
    speaker: str
    pinyin: str


class Q1DialogueTask(BaseModel):
    task_type: Literal["pinyin_dialogue"] = "pinyin_dialogue"
    task_id: str
    subsection: Literal["D"] = "D"
    order: int = Field(ge=1)
    lines: list[PinyinDialogueLine] = Field(min_length=2, max_length=12)
    prompt_ja: str
    options: list[str] = Field(min_length=4, max_length=6)
    answer_slot: AnswerSlot
    rationale_ja: str
    distractor_rationales_ja: dict[str, str] = Field(default_factory=dict)


Q1Task = Annotated[Q1PhoneticCountTask | Q1DialogueTask, Field(discriminator="task_type")]


class Q1Section(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    section: Literal["Q1"] = "Q1"
    section_id: str
    title_ja: str = "発音・ピンイン"
    score: Literal[24] = 24
    tasks: list[Q1Task] = Field(min_length=6, max_length=6)
    workflow: SectionWorkflowMeta = Field(default_factory=SectionWorkflowMeta)

    @model_validator(mode="after")
    def validate_surface(self) -> Q1Section:
        numbers = sorted(task.answer_slot.answer_number for task in self.tasks)
        if numbers != list(range(1, 7)):
            raise ValueError("Q1 must use answer numbers 1 through 6 exactly once")
        expected = [
            ("A", "phonetic_count", "initial"),
            ("B", "phonetic_count", "final"),
            ("C", "phonetic_count", "tone_pattern"),
            ("C", "phonetic_count", "tone_pattern"),
            ("D", "pinyin_dialogue", None),
            ("D", "pinyin_dialogue", None),
        ]
        ordered = sorted(self.tasks, key=lambda task: task.answer_slot.answer_number)
        for task, (subsection, task_type, target) in zip(ordered, expected, strict=True):
            if task.subsection != subsection or task.task_type != task_type:
                raise ValueError("Q1 task sequence must be A, B, C1, C2, D1, D2")
            if target is not None and getattr(task, "target", None) != target:
                raise ValueError(f"Q1 {subsection} has wrong phonetic target")
        return self


class Q2FillTask(BaseModel):
    task_type: Literal["fill_choice"] = "fill_choice"
    task_id: str
    subsection: Literal["A", "B"]
    order: int = Field(ge=1)
    selection_rule: Literal["appropriate", "inappropriate"]
    sentence_zh: str
    blank_marker: str = "＿＿＿"
    prompt_ja: str
    options: list[str] = Field(min_length=4, max_length=4)
    answer_slot: AnswerSlot
    rationale_ja: str
    distractor_rationales_ja: dict[str, str] = Field(default_factory=dict)


class OrderingToken(BaseModel):
    token_id: int = Field(ge=1, le=8)
    text_zh: str


class Q2OrderingTask(BaseModel):
    task_type: Literal["ordering"] = "ordering"
    task_id: str
    subsection: Literal["C"] = "C"
    order: int = Field(ge=1)
    source_ja: str
    sentence_frame_zh: str
    prompt_ja: str
    token_pool: list[OrderingToken] = Field(min_length=8, max_length=8)
    correct_sequence: list[int] = Field(min_length=4, max_length=4)
    answer_positions: list[int] = Field(min_length=2, max_length=2)
    answer_slots: list[AnswerSlot] = Field(min_length=2, max_length=2)
    rationale_ja: str
    token_rationales_ja: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ordering(self) -> Q2OrderingTask:
        ids = [token.token_id for token in self.token_pool]
        if sorted(ids) != list(range(1, 9)):
            raise ValueError("Q2 ordering token_pool must use token_id 1 through 8 exactly once")
        if len(set(self.correct_sequence)) != 4 or any(token not in ids for token in self.correct_sequence):
            raise ValueError("Q2 ordering correct_sequence must contain four distinct token ids")
        if len(set(self.answer_positions)) != 2 or any(pos < 1 or pos > 4 for pos in self.answer_positions):
            raise ValueError("Q2 ordering answer_positions must be two distinct positions in 1..4")
        expected = [self.correct_sequence[pos - 1] for pos in self.answer_positions]
        actual = [slot.correct_option for slot in self.answer_slots]
        if actual != expected:
            raise ValueError("Q2 ordering answer_slots must encode token ids at answer_positions")
        return self


Q2Task = Annotated[Q2FillTask | Q2OrderingTask, Field(discriminator="task_type")]


class Q2Section(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    section: Literal["Q2"] = "Q2"
    section_id: str
    title_ja: str = "語句"
    score: Literal[16] = 16
    tasks: list[Q2Task] = Field(min_length=4, max_length=4)
    workflow: SectionWorkflowMeta = Field(default_factory=SectionWorkflowMeta)

    @model_validator(mode="after")
    def validate_surface(self) -> Q2Section:
        slots: list[AnswerSlot] = []
        for task in self.tasks:
            slots.extend(task.answer_slots if isinstance(task, Q2OrderingTask) else [task.answer_slot])
        numbers = sorted(slot.answer_number for slot in slots)
        if numbers != list(range(7, 13)):
            raise ValueError("Q2 must use answer numbers 7 through 12 exactly once")
        fill_a = [task for task in self.tasks if isinstance(task, Q2FillTask) and task.subsection == "A"]
        fill_b = [task for task in self.tasks if isinstance(task, Q2FillTask) and task.subsection == "B"]
        ordering = [task for task in self.tasks if isinstance(task, Q2OrderingTask)]
        if len(fill_a) != 1 or fill_a[0].selection_rule != "appropriate":
            raise ValueError("Q2-A must be one appropriate fill-choice task")
        if len(fill_b) != 1 or fill_b[0].selection_rule != "inappropriate":
            raise ValueError("Q2-B must be one inappropriate fill-choice task")
        if len(ordering) != 2:
            raise ValueError("Q2-C must contain exactly two ordering tasks")
        groups = sorted(sorted(slot.answer_number for slot in task.answer_slots) for task in ordering)
        if groups != [[9, 10], [11, 12]]:
            raise ValueError("Q2-C answer groups must be 9-10 and 11-12")
        return self


Q3ErrorType = Literal[
    "scope",
    "subject_object",
    "aspect",
    "modality",
    "lexical_meaning",
    "causal_relation",
    "pragmatic_force",
    "overtranslation",
    "undertranslation",
]


class Q3TranslationTask(BaseModel):
    task_type: Literal["translation_choice"] = "translation_choice"
    task_id: str
    subsection: Literal["A", "B"]
    order: int = Field(ge=1)
    direction: Literal["ja_to_zh", "zh_to_ja"]
    source_text: str
    prompt_ja: str
    options: list[str] = Field(min_length=4, max_length=4)
    answer_slot: AnswerSlot
    rationale_ja: str
    distractor_error_types: dict[str, list[Q3ErrorType]] = Field(default_factory=dict)
    distractor_rationales_ja: dict[str, str] = Field(default_factory=dict)


class Q3Section(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    section: Literal["Q3"] = "Q3"
    section_id: str
    title_ja: str = "表現力"
    score: Literal[40] = 40
    tasks: list[Q3TranslationTask] = Field(min_length=8, max_length=8)
    workflow: SectionWorkflowMeta = Field(default_factory=SectionWorkflowMeta)

    @model_validator(mode="after")
    def validate_surface(self) -> Q3Section:
        ordered = sorted(self.tasks, key=lambda task: task.answer_slot.answer_number)
        numbers = [task.answer_slot.answer_number for task in ordered]
        if numbers != list(range(13, 21)):
            raise ValueError("Q3 must use answer numbers 13 through 20 exactly once")
        for task in ordered[:4]:
            if task.subsection != "A" or task.direction != "ja_to_zh":
                raise ValueError("Q3 13-16 must be A / ja_to_zh")
        for task in ordered[4:]:
            if task.subsection != "B" or task.direction != "zh_to_ja":
                raise ValueError("Q3 17-20 must be B / zh_to_ja")
        return self


class ArticleParagraph(BaseModel):
    paragraph_id: str
    text_zh: str


class ArticleAnchor(BaseModel):
    anchor_id: str
    paragraph_id: str
    kind: Literal["blank", "underline", "phrase", "sentence", "time_marker"]
    marker_label: str | None = None
    source_excerpt: str | None = None


class Q5AnswerSlot(BaseModel):
    slot_id: str
    answer_number: int = Field(ge=37, le=50)
    correct_option: int = Field(ge=1, le=10)


class Q5Task(BaseModel):
    task_id: str
    question_no: int = Field(ge=1, le=11)
    order: int = Field(ge=1)
    prompt_ja: str
    options: list[str] = Field(min_length=4, max_length=10)
    response_mode: Literal["single_choice", "multi_select", "multi_slot_choice"]
    answer_slots: list[Q5AnswerSlot] = Field(min_length=1, max_length=3)
    option_reuse: Literal["allowed", "forbidden"] = "forbidden"
    anchor_refs: list[str] = Field(default_factory=list)
    operation: Literal[
        "lexical_choice",
        "sentence_choice",
        "interpret",
        "reason",
        "reference",
        "discourse_connector",
        "chronology",
        "content_understanding",
        "whole_text_consistency",
    ]
    rationale_ja: str
    distractor_rationales_ja: dict[str, str] = Field(default_factory=dict)
    slot_distractor_rationales_ja: dict[str, dict[str, str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_answers(self) -> Q5Task:
        if any(slot.correct_option > len(self.options) for slot in self.answer_slots):
            raise ValueError("Q5 correct_option exceeds number of options")
        if self.response_mode == "single_choice" and len(self.answer_slots) != 1:
            raise ValueError("Q5 single_choice requires one answer slot")
        if self.response_mode == "multi_select" and len(self.answer_slots) < 2:
            raise ValueError("Q5 multi_select requires at least two answer slots")
        answers = [slot.correct_option for slot in self.answer_slots]
        if self.option_reuse == "forbidden" and len(answers) != len(set(answers)):
            raise ValueError("Q5 answer options may not repeat when option_reuse=forbidden")
        return self


class Q5Section(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    section: Literal["Q5"] = "Q5"
    section_id: str
    surface_family: ExamFamily
    title_ja: str = "長文読解"
    topic: str
    score: Literal[60] = 60
    paragraphs: list[ArticleParagraph] = Field(min_length=3, max_length=30)
    anchors: list[ArticleAnchor] = Field(default_factory=list)
    tasks: list[Q5Task] = Field(min_length=10, max_length=11)
    originality_statement: str = Field(min_length=10)
    workflow: SectionWorkflowMeta = Field(default_factory=SectionWorkflowMeta)

    @model_validator(mode="after")
    def validate_surface(self) -> Q5Section:
        paragraph_ids = [paragraph.paragraph_id for paragraph in self.paragraphs]
        if len(paragraph_ids) != len(set(paragraph_ids)):
            raise ValueError("Q5 paragraph_id values must be unique")
        anchor_ids = [anchor.anchor_id for anchor in self.anchors]
        if len(anchor_ids) != len(set(anchor_ids)):
            raise ValueError("Q5 anchor_id values must be unique")
        known_paragraphs = set(paragraph_ids)
        known_anchors = set(anchor_ids)
        for anchor in self.anchors:
            if anchor.paragraph_id not in known_paragraphs:
                raise ValueError(f"Q5 anchor {anchor.anchor_id} references unknown paragraph")
        for task in self.tasks:
            unknown = set(task.anchor_refs) - known_anchors
            if unknown:
                raise ValueError(f"Q5 task {task.task_id} references unknown anchors {sorted(unknown)}")

        answer_numbers = sorted(slot.answer_number for task in self.tasks for slot in task.answer_slots)
        if answer_numbers != list(range(37, 51)):
            raise ValueError("Q5 must use answer numbers 37 through 50 exactly once")
        qnos = sorted(task.question_no for task in self.tasks)
        expected_qnos = list(range(1, 12 if self.surface_family == "main_2026" else 11))
        if qnos != expected_qnos:
            raise ValueError(
                f"Q5 {self.surface_family} must use question numbers {expected_qnos} exactly once"
            )

        groups = {
            task.question_no: sorted(slot.answer_number for slot in task.answer_slots)
            for task in self.tasks
        }
        if self.surface_family == "main_2026":
            known = {
                3: [40], 4: [41], 5: [42], 6: [43], 7: [44], 8: [45],
                9: [46], 10: [47, 48], 11: [49, 50],
            }
            first_two = sorted(groups.get(1, []) + groups.get(2, []))
            if first_two != [37, 38, 39]:
                raise ValueError("Q5 main Q1-Q2 must jointly occupy answer numbers 37-39")
        else:
            known = {
                1: [37], 2: [38], 3: [39], 4: [40, 41], 5: [42], 6: [43],
                7: [44], 8: [45, 46], 9: [47, 48], 10: [49, 50],
            }
        for qno, expected in known.items():
            if groups.get(qno) != expected:
                raise ValueError(
                    f"Q5 {self.surface_family} question {qno} must use answer numbers {expected}"
                )
        return self


SectionData = Annotated[Q1Section | Q2Section | Q3Section | Item | Q5Section, Field(discriminator="section")]


class SectionRef(BaseModel):
    section: SectionKind
    section_id: str
    path: str | None = None
    expected_score: int
    answer_start: int
    answer_end: int
    state: SectionState = "not_generated"
    fingerprint: str | None = None

    @model_validator(mode="after")
    def validate_spec(self) -> SectionRef:
        score, start, end = SECTION_SPECS[self.section]
        if (self.expected_score, self.answer_start, self.answer_end) != (score, start, end):
            raise ValueError(f"{self.section} section reference does not match official 2026 allocation")
        return self


class ExamWorkflowMeta(BaseModel):
    state: Literal["draft", "reviewed", "approved"] = "draft"
    generation_mode: Literal["manual_chat"] = "manual_chat"


class ExamManifest(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    exam_id: str
    blueprint_version: Literal["R8-2026-full-v1"] = "R8-2026-full-v1"
    exam_family: ExamFamily
    title_ja: str
    duration_minutes: Literal[80] = 80
    total_score: Literal[200] = 200
    answer_range: tuple[Literal[1], Literal[50]] = (1, 50)
    notes: str = ""
    q4_topic_request: str = ""
    q5_topic_request: str = ""
    sections: list[SectionRef] = Field(min_length=5, max_length=5)
    workflow: ExamWorkflowMeta = Field(default_factory=ExamWorkflowMeta)

    @model_validator(mode="after")
    def validate_sections(self) -> ExamManifest:
        names = [ref.section for ref in self.sections]
        if sorted(names) != ["Q1", "Q2", "Q3", "Q4", "Q5"]:
            raise ValueError("ExamManifest must contain exactly Q1 through Q5")
        if len({ref.section_id for ref in self.sections}) != 5:
            raise ValueError("ExamManifest section_id values must be unique")
        return self


class ExamQAChecks(BaseModel):
    timing_feasible_80_minutes: bool = False
    score_structure_200_complete: bool = False
    answer_numbers_1_to_50_continuous: bool = False
    q1_to_q5_visual_hierarchy: bool = False
    difficulty_rhythm_reasonable: bool = False
    q4_q5_topics_distinct: bool = False
    no_cross_section_solution_leak: bool = False
    pinyin_style_consistent: bool = False
    simplified_chinese_consistent: bool = False
    japanese_instruction_style_consistent: bool = False
    numbers_punctuation_options_consistent: bool = False
    pagination_readable: bool = False
    charts_readable: bool = False
    long_text_pagination_readable: bool = False
    booklet_readable: bool = False


class ExamQATiming(BaseModel):
    full_exam_first_read_minutes: int = Field(default=0, ge=0, le=600)
    layout_fix_minutes: int = Field(default=0, ge=0, le=600)
    cross_section_fix_minutes: int = Field(default=0, ge=0, le=600)


class ExamHumanQA(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    exam_id: str
    reviewer: str = Field(min_length=1)
    disposition: Literal["approve", "revise", "reject"]
    checks: ExamQAChecks
    timing: ExamQATiming = Field(default_factory=ExamQATiming)
    defects: list[str] = Field(default_factory=list)
    biggest_rework_cause: str = ""
    note: str = ""

    @model_validator(mode="after")
    def approve_requires_completed_checks(self) -> ExamHumanQA:
        if self.disposition != "approve":
            return self
        failed = [name for name, value in self.checks.model_dump().items() if not value]
        if failed:
            raise ValueError(
                "Exam Human QA cannot be approved while required checks are incomplete ("
                + ", ".join(failed)
                + ")"
            )
        return self

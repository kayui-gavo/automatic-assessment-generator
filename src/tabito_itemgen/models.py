from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

Difficulty = Literal["easy", "medium", "hard"]
Scope = Literal["full", "mini"]
Subsection = Literal["A", "B"]
Operation = Literal[
    "extract",
    "compare",
    "condition_match",
    "integrate",
    "infer",
    "sequence",
    "evaluate",
]
ResponseMode = Literal["single_choice", "multi_select", "multi_slot_choice"]


class TextMaterial(BaseModel):
    type: Literal[
        "dialogue",
        "notice",
        "poster",
        "short_explanatory_text",
        "profile",
        "checklist",
    ]
    material_id: str
    subsection: Subsection
    order: int = Field(ge=1)
    title: str | None = None
    body: str
    glosses: dict[str, str] = Field(default_factory=dict)


class TableMaterial(BaseModel):
    type: Literal["table", "timetable"]
    material_id: str
    subsection: Subsection
    order: int = Field(ge=1)
    title: str | None = None
    columns: list[str] = Field(min_length=2, max_length=10)
    rows: list[list[str]] = Field(min_length=1)
    footnotes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_width(self) -> "TableMaterial":
        width = len(self.columns)
        if any(len(row) != width for row in self.rows):
            raise ValueError("every table row must match the column count")
        return self


class ChartSeries(BaseModel):
    name: str
    values: list[float]


class ChartMaterial(BaseModel):
    type: Literal["chart"]
    material_id: str
    subsection: Subsection
    order: int = Field(ge=1)
    title: str | None = None
    chart_kind: Literal["bar", "line"]
    categories: list[str] = Field(min_length=2, max_length=12)
    series: list[ChartSeries] = Field(min_length=1, max_length=4)
    y_label: str | None = None
    footnotes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_series_lengths(self) -> "ChartMaterial":
        n = len(self.categories)
        if any(len(series.values) != n for series in self.series):
            raise ValueError("chart series length must match category count")
        return self


class FlowNode(BaseModel):
    node_id: str
    label: str


class FlowEdge(BaseModel):
    source: str
    target: str
    label: str | None = None


class FlowchartMaterial(BaseModel):
    type: Literal["flowchart"]
    material_id: str
    subsection: Subsection
    order: int = Field(ge=1)
    title: str | None = None
    nodes: list[FlowNode] = Field(min_length=2, max_length=16)
    edges: list[FlowEdge] = Field(min_length=1, max_length=24)
    footnotes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_edges(self) -> "FlowchartMaterial":
        node_ids = {node.node_id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("flowchart node_id values must be unique")
        for edge in self.edges:
            if edge.source not in node_ids or edge.target not in node_ids:
                raise ValueError("flowchart edge references an unknown node")
        return self


Material = Annotated[
    TextMaterial | TableMaterial | ChartMaterial | FlowchartMaterial,
    Field(discriminator="type"),
]


class EvidenceRef(BaseModel):
    material_id: str
    locator: str
    explanation_ja: str


class AnswerSlot(BaseModel):
    slot_id: str
    answer_number: int = Field(ge=1, le=99)
    correct_option: int = Field(ge=1, le=10)


class Task(BaseModel):
    task_id: str
    subsection: Subsection
    order: int = Field(ge=1)
    prompt_ja: str
    options: list[str] = Field(min_length=4, max_length=8)
    response_mode: ResponseMode
    answer_slots: list[AnswerSlot] = Field(min_length=1, max_length=3)
    option_reuse: Literal["allowed", "forbidden"] = "forbidden"
    operations: list[Operation] = Field(min_length=1, max_length=3)
    evidence: list[EvidenceRef] = Field(min_length=1)
    rationale_ja: str
    distractor_rationales_ja: dict[str, str]

    @model_validator(mode="after")
    def validate_answers(self) -> "Task":
        if len(set(self.options)) != len(self.options):
            raise ValueError("duplicate options are not allowed")
        if any(slot.correct_option > len(self.options) for slot in self.answer_slots):
            raise ValueError("correct_option exceeds number of options")
        if self.response_mode == "single_choice" and len(self.answer_slots) != 1:
            raise ValueError("single_choice requires exactly one answer slot")
        if self.response_mode == "multi_select":
            answers = [slot.correct_option for slot in self.answer_slots]
            if len(answers) < 2:
                raise ValueError("multi_select requires at least two answer slots")
            if len(set(answers)) != len(answers):
                raise ValueError("multi_select correct options must be distinct")
        if self.option_reuse == "forbidden":
            answers = [slot.correct_option for slot in self.answer_slots]
            if len(set(answers)) != len(answers):
                raise ValueError("answer options cannot be reused when option_reuse=forbidden")
        return self


class QualityNotes(BaseModel):
    ambiguity_risk: Literal["low", "medium", "high"]
    originality_note: str
    language_note: str
    difficulty_note: str


class WorkflowMeta(BaseModel):
    state: Literal["draft", "reviewed", "approved"] = "draft"
    generation_mode: Literal["manual_chat"] = "manual_chat"
    blueprint_version: str = "R8-2026-v1"


class Item(BaseModel):
    schema_version: Literal["0.2"] = "0.2"
    item_id: str
    section: Literal["Q4"]
    scope: Scope = "full"
    title_ja: str
    topic: str
    scenario_summary_ja: str
    difficulty: Difficulty
    materials: list[Material] = Field(min_length=2, max_length=12)
    tasks: list[Task] = Field(min_length=2, max_length=14)
    quality_notes: QualityNotes
    workflow: WorkflowMeta = Field(default_factory=WorkflowMeta)

    @model_validator(mode="after")
    def validate_structure(self) -> "Item":
        material_ids = [m.material_id for m in self.materials]
        if len(material_ids) != len(set(material_ids)):
            raise ValueError("material_id values must be unique")
        task_ids = [task.task_id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task_id values must be unique")
        slot_ids = [slot.slot_id for task in self.tasks for slot in task.answer_slots]
        if len(slot_ids) != len(set(slot_ids)):
            raise ValueError("slot_id values must be unique")
        answer_numbers = [slot.answer_number for task in self.tasks for slot in task.answer_slots]
        if len(answer_numbers) != len(set(answer_numbers)):
            raise ValueError("answer_number values must be unique")

        known = set(material_ids)
        for task in self.tasks:
            for evidence in task.evidence:
                if evidence.material_id not in known:
                    raise ValueError(f"{task.task_id}: unknown evidence material id {evidence.material_id}")

        block_orders = [(m.subsection, m.order) for m in self.materials] + [
            (task.subsection, task.order) for task in self.tasks
        ]
        if len(block_orders) != len(set(block_orders)):
            raise ValueError("material/task order values must be unique within each subsection")

        if self.scope == "full":
            if sorted(answer_numbers) != list(range(21, 37)):
                raise ValueError("full Q4 must use answer numbers 21 through 36 exactly once")
            for subsection in ("A", "B"):
                if not any(m.subsection == subsection for m in self.materials):
                    raise ValueError(f"full Q4 requires materials in subsection {subsection}")
                if not any(task.subsection == subsection for task in self.tasks):
                    raise ValueError(f"full Q4 requires tasks in subsection {subsection}")
        return self


class ReviewIssue(BaseModel):
    severity: Literal["high", "medium", "low"]
    task_id: str | None = None
    category: str
    description: str
    suggested_fix: str


class Review(BaseModel):
    schema_version: Literal["0.2"] = "0.2"
    item_id: str
    verdict: Literal["pass", "revise", "reject"]
    independent_answers: dict[str, list[int]]
    issues: list[ReviewIssue]
    overall_comment_ja: str

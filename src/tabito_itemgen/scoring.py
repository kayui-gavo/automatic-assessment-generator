from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .exam_models import ExamFamily, SectionKind

SCORING_VERSION = "R8-2026-scoring-v1"
AwardMode = Literal["all_or_nothing", "per_choice"]
ComparisonMode = Literal["ordered", "set"]

SECTION_TOTALS: dict[SectionKind, int] = {
    "Q1": 24,
    "Q2": 16,
    "Q3": 40,
    "Q4": 60,
    "Q5": 60,
}


def _section_for_answer(answer_number: int) -> SectionKind:
    if answer_number <= 6:
        return "Q1"
    if answer_number <= 12:
        return "Q2"
    if answer_number <= 20:
        return "Q3"
    if answer_number <= 36:
        return "Q4"
    return "Q5"


class ScoringGroup(BaseModel):
    """One official scoring unit.

    The 2026 Chinese answer tables use two independent conventions:

    - ``＊`` means the linked answers earn the group's points only when every
      answer in that group is correct.
    - a hyphen joining answer numbers / correct answers means order is ignored.

    Those conventions must not be conflated. A starred pair without a hyphen is
    still order-sensitive.
    """

    group_id: str
    section: SectionKind
    answer_numbers: tuple[int, ...] = Field(min_length=1)
    points: int = Field(gt=0)
    award_mode: AwardMode = "all_or_nothing"
    comparison_mode: ComparisonMode = "ordered"

    @model_validator(mode="after")
    def validate_group(self) -> ScoringGroup:
        if len(self.answer_numbers) != len(set(self.answer_numbers)):
            raise ValueError("scoring group answer_numbers must be unique")
        for number in self.answer_numbers:
            if not 1 <= number <= 50:
                raise ValueError("scoring group answer_numbers must be in 1..50")
            if _section_for_answer(number) != self.section:
                raise ValueError(
                    f"scoring group {self.group_id} assigns answer {number} to wrong section"
                )
        if self.award_mode == "per_choice" and self.points % len(self.answer_numbers) != 0:
            raise ValueError("per_choice group points must divide evenly across answer numbers")
        return self

    @property
    def points_each(self) -> int | None:
        if self.award_mode != "per_choice":
            return None
        return self.points // len(self.answer_numbers)


class ScoringScheme(BaseModel):
    scoring_version: Literal[SCORING_VERSION] = SCORING_VERSION
    family: ExamFamily
    total_points: Literal[200] = 200
    groups: tuple[ScoringGroup, ...]

    @model_validator(mode="after")
    def validate_scheme(self) -> ScoringScheme:
        numbers = [number for group in self.groups for number in group.answer_numbers]
        if sorted(numbers) != list(range(1, 51)):
            raise ValueError("scoring scheme must cover answer numbers 1 through 50 exactly once")
        if len(numbers) != len(set(numbers)):
            raise ValueError("scoring scheme contains duplicated answer numbers")
        if sum(group.points for group in self.groups) != self.total_points:
            raise ValueError("scoring groups must sum to 200 points")

        section_points: dict[SectionKind, int] = defaultdict(int)
        for group in self.groups:
            section_points[group.section] += group.points
        if dict(section_points) != SECTION_TOTALS:
            raise ValueError(
                f"section scoring totals must be {SECTION_TOTALS}, got {dict(section_points)}"
            )
        return self


class GroupScore(BaseModel):
    group_id: str
    answer_numbers: tuple[int, ...]
    earned: int
    possible: int


class ScoreResult(BaseModel):
    scoring_version: Literal[SCORING_VERSION] = SCORING_VERSION
    family: ExamFamily
    earned: int
    possible: Literal[200] = 200
    groups: tuple[GroupScore, ...]


def _single(section: SectionKind, number: int, points: int) -> ScoringGroup:
    return ScoringGroup(
        group_id=f"{section}-{number}",
        section=section,
        answer_numbers=(number,),
        points=points,
    )


def _group(
    section: SectionKind,
    numbers: tuple[int, ...],
    points: int,
    *,
    award: AwardMode,
    comparison: ComparisonMode,
) -> ScoringGroup:
    joined = "-".join(str(value) for value in numbers)
    return ScoringGroup(
        group_id=f"{section}-{joined}",
        section=section,
        answer_numbers=numbers,
        points=points,
        award_mode=award,
        comparison_mode=comparison,
    )


def _common_q1_q3() -> list[ScoringGroup]:
    groups: list[ScoringGroup] = []
    groups.extend(_single("Q1", number, 4) for number in range(1, 7))
    groups.extend(
        [
            _single("Q2", 7, 4),
            _single("Q2", 8, 4),
            _group("Q2", (9, 10), 4, award="all_or_nothing", comparison="ordered"),
            _group("Q2", (11, 12), 4, award="all_or_nothing", comparison="ordered"),
        ]
    )
    groups.extend(_single("Q3", number, 5) for number in range(13, 21))
    return groups


def _main_groups() -> tuple[ScoringGroup, ...]:
    groups = _common_q1_q3()
    groups.extend(
        [
            _group("Q4", (21, 22), 10, award="per_choice", comparison="set"),
            # Starred, but the answer numbers are not hyphen-joined in the
            # official table: all correct is required and order still matters.
            _group("Q4", (23, 24), 5, award="all_or_nothing", comparison="ordered"),
            _single("Q4", 25, 5),
            _single("Q4", 26, 5),
            _group("Q4", (27, 28), 5, award="all_or_nothing", comparison="set"),
            _group("Q4", (29, 30), 10, award="per_choice", comparison="set"),
            _group("Q4", (31, 32), 5, award="all_or_nothing", comparison="ordered"),
            _single("Q4", 33, 5),
            _single("Q4", 34, 5),
            _group("Q4", (35, 36), 5, award="all_or_nothing", comparison="ordered"),
            _single("Q5", 37, 5),
            _group("Q5", (38, 39), 5, award="all_or_nothing", comparison="ordered"),
            _single("Q5", 40, 5),
            _single("Q5", 41, 5),
            _single("Q5", 42, 5),
            _single("Q5", 43, 5),
            _single("Q5", 44, 5),
            _single("Q5", 45, 5),
            _single("Q5", 46, 5),
            _group("Q5", (47, 48), 5, award="all_or_nothing", comparison="set"),
            _group("Q5", (49, 50), 10, award="per_choice", comparison="set"),
        ]
    )
    return tuple(groups)


def _makeup_groups() -> tuple[ScoringGroup, ...]:
    groups = _common_q1_q3()
    groups.extend(
        [
            _group("Q4", (21, 22), 5, award="all_or_nothing", comparison="set"),
            _group("Q4", (23, 24), 5, award="all_or_nothing", comparison="set"),
            _group("Q4", (25, 26), 10, award="per_choice", comparison="set"),
            _group("Q4", (27, 28), 10, award="per_choice", comparison="set"),
            _group("Q4", (29, 30), 5, award="all_or_nothing", comparison="set"),
            _group("Q4", (31, 32), 10, award="per_choice", comparison="set"),
            _group("Q4", (33, 34), 10, award="per_choice", comparison="set"),
            _group("Q4", (35, 36), 5, award="all_or_nothing", comparison="set"),
            _single("Q5", 37, 5),
            _single("Q5", 38, 5),
            _single("Q5", 39, 5),
            _group("Q5", (40, 41), 5, award="all_or_nothing", comparison="set"),
            _single("Q5", 42, 5),
            _single("Q5", 43, 5),
            _single("Q5", 44, 5),
            _group("Q5", (45, 46), 10, award="per_choice", comparison="set"),
            # Starred pair without an answer-number hyphen: order-sensitive.
            _group("Q5", (47, 48), 5, award="all_or_nothing", comparison="ordered"),
            _group("Q5", (49, 50), 10, award="per_choice", comparison="set"),
        ]
    )
    return tuple(groups)


_SCHEMES: dict[ExamFamily, ScoringScheme] = {
    "main_2026": ScoringScheme(family="main_2026", groups=_main_groups()),
    "makeup_2026": ScoringScheme(family="makeup_2026", groups=_makeup_groups()),
}


def scoring_scheme(family: ExamFamily) -> ScoringScheme:
    """Return the frozen official 2026 scoring semantics for one surface family."""

    return _SCHEMES[family].model_copy(deep=True)


def _normalize_answers(
    values: Mapping[int | str, int],
    *,
    label: str,
    require_complete: bool,
) -> dict[int, int]:
    normalized: dict[int, int] = {}
    for raw_number, raw_option in values.items():
        try:
            number = int(raw_number)
            option = int(raw_option)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{label} contains a non-integer answer mapping") from exc
        if not 1 <= number <= 50:
            raise ValueError(f"{label} answer number must be in 1..50")
        if not 1 <= option <= 10:
            raise ValueError(f"{label} option must be in 1..10")
        if number in normalized:
            raise ValueError(f"{label} contains duplicate normalized answer number {number}")
        normalized[number] = option
    if require_complete and set(normalized) != set(range(1, 51)):
        missing = sorted(set(range(1, 51)) - set(normalized))
        extra = sorted(set(normalized) - set(range(1, 51)))
        raise ValueError(
            f"{label} must contain answer numbers 1..50 exactly; missing={missing}, extra={extra}"
        )
    return normalized


def _ordered(values: Mapping[int, int], numbers: tuple[int, ...]) -> list[int | None]:
    return [values.get(number) for number in numbers]


def _group_score(
    group: ScoringGroup,
    author: Mapping[int, int],
    response: Mapping[int, int],
) -> int:
    correct = _ordered(author, group.answer_numbers)
    chosen = _ordered(response, group.answer_numbers)
    if any(value is None for value in correct):
        raise ValueError(f"author key is missing answer number in {group.group_id}")
    if group.comparison_mode == "set" and len(set(correct)) != len(correct):
        raise ValueError(f"author key contains duplicate choices in set group {group.group_id}")

    if group.award_mode == "all_or_nothing":
        if any(value is None for value in chosen):
            return 0
        if group.comparison_mode == "ordered":
            matched = chosen == correct
        else:
            matched = sorted(chosen) == sorted(correct)
        return group.points if matched else 0

    points_each = group.points_each or 0
    if group.comparison_mode == "ordered":
        return sum(
            points_each
            for selected, expected in zip(chosen, correct, strict=True)
            if selected is not None and selected == expected
        )

    correct_values = set(correct)
    selected_values = {value for value in chosen if value is not None}
    return points_each * len(correct_values & selected_values)


def score_with_scheme(
    scheme: ScoringScheme,
    author_key: Mapping[int | str, int],
    responses: Mapping[int | str, int],
) -> ScoreResult:
    """Score with an explicit immutable scheme, e.g. one stored at release time."""

    author = _normalize_answers(
        author_key,
        label="author key",
        require_complete=True,
    )
    response = _normalize_answers(
        responses,
        label="response",
        require_complete=False,
    )
    groups = tuple(
        GroupScore(
            group_id=group.group_id,
            answer_numbers=group.answer_numbers,
            earned=_group_score(group, author, response),
            possible=group.points,
        )
        for group in scheme.groups
    )
    return ScoreResult(
        scoring_version=scheme.scoring_version,
        family=scheme.family,
        earned=sum(group.earned for group in groups),
        groups=groups,
    )


def score_responses(
    family: ExamFamily,
    author_key: Mapping[int | str, int],
    responses: Mapping[int | str, int],
) -> ScoreResult:
    """Score with the current frozen scheme for the requested 2026 family."""

    return score_with_scheme(scoring_scheme(family), author_key, responses)

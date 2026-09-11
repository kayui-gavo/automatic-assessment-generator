from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from .io import load_json
from .models import Item, Review, TextMaterial


def _expected_distractor_keys(task) -> set[str]:
    correct = {slot.correct_option for slot in task.answer_slots}
    return {str(i) for i in range(1, len(task.options) + 1) if i not in correct}


def validate_item_file(path: Path) -> tuple[Item | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        item = Item.model_validate(load_json(path))
    except (ValidationError, ValueError) as exc:
        return None, [str(exc)], []

    slots = [slot for task in item.tasks for slot in task.answer_slots]
    answers = [slot.correct_option for slot in slots]
    counts = Counter(answers)
    if len(slots) >= 8 and counts and max(counts.values()) > max(4, len(slots) * 0.4):
        warnings.append(f"answer-position imbalance: {dict(sorted(counts.items()))}")

    operations = {op for task in item.tasks for op in task.operations}
    minimum_ops = 4 if item.scope == "full" else 3
    if len(operations) < minimum_ops:
        warnings.append(f"low cognitive-operation variety: {sorted(operations)}")

    cross_material = sum(1 for task in item.tasks if len({e.material_id for e in task.evidence}) >= 2)
    minimum_cross = 3 if item.scope == "full" else 1
    if cross_material < minimum_cross:
        errors.append(f"Q4 {item.scope} requires at least {minimum_cross} cross-material tasks")

    material_types = {m.type for m in item.materials}
    if item.scope == "full" and len(material_types) < 4:
        warnings.append(f"low material-type variety: {sorted(material_types)}")
    if item.scope == "full" and not material_types.intersection({"table", "timetable", "chart", "flowchart"}):
        errors.append("full Q4 requires at least one structured/visual material")

    for subsection in ("A", "B"):
        if item.scope == "full":
            subsection_slots = sum(
                len(task.answer_slots) for task in item.tasks if task.subsection == subsection
            )
            if subsection_slots < 5:
                warnings.append(f"subsection {subsection} has only {subsection_slots} answer slots")

    for task in item.tasks:
        distractor_keys = set(task.distractor_rationales_ja.keys())
        expected = _expected_distractor_keys(task)
        if distractor_keys != expected:
            warnings.append(
                f"{task.task_id}: distractor rationale keys {sorted(distractor_keys)} "
                f"!= expected {sorted(expected)}"
            )
        if any(not evidence.locator.strip() for evidence in task.evidence):
            errors.append(f"{task.task_id}: evidence locator must not be empty")
        if task.response_mode == "multi_select" and len(task.options) < 6:
            warnings.append(f"{task.task_id}: multi_select has fewer than 6 options")

    if item.quality_notes.ambiguity_risk == "high":
        errors.append("ambiguity_risk=high cannot pass validation")

    return item, errors, warnings


def compare_review(item: Item, review: Review) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if review.item_id != item.item_id:
        errors.append("review item_id does not match item")
        return errors, warnings

    task_map = {task.task_id: task for task in item.tasks}
    for task_id, task in task_map.items():
        if task_id not in review.independent_answers:
            errors.append(f"review missing independent answer for {task_id}")
            continue
        expected = [slot.correct_option for slot in task.answer_slots]
        observed = review.independent_answers[task_id]
        if task.response_mode == "multi_select":
            match = sorted(expected) == sorted(observed)
        else:
            match = expected == observed
        if not match:
            errors.append(f"{task_id}: reviewer answers {observed} != key {expected}")

    unknown = set(review.independent_answers) - set(task_map)
    if unknown:
        warnings.append(f"review contains unknown task ids: {sorted(unknown)}")
    if review.verdict != "pass":
        errors.append(f"review verdict is {review.verdict}, not pass")
    if any(issue.severity == "high" for issue in review.issues):
        errors.append("review contains high-severity issues")
    return errors, warnings


def _normalize_text(text: str) -> str:
    return re.sub(r"[^\w\u3400-\u9fff]", "", text.lower())


def _ngrams(text: str, n: int = 5) -> set[str]:
    text = _normalize_text(text)
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def item_text(item: Item) -> str:
    parts: list[str] = [item.topic, item.scenario_summary_ja]
    for material in item.materials:
        if isinstance(material, TextMaterial):
            parts.append(material.body)
        else:
            parts.append(str(material.model_dump(exclude={"material_id", "order"})))
    for task in item.tasks:
        parts.extend([task.prompt_ja, *task.options])
    return "\n".join(parts)


def similarity(a: Item, b: Item, n: int = 5) -> float:
    ga, gb = _ngrams(item_text(a), n), _ngrams(item_text(b), n)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def check_bank_similarity(item: Item, bank_dir: Path) -> list[tuple[str, float]]:
    matches: list[tuple[str, float]] = []
    if not bank_dir.exists():
        return matches
    for path in sorted(bank_dir.glob("*.json")):
        try:
            other = Item.model_validate(load_json(path))
        except Exception:
            continue
        if other.item_id == item.item_id:
            continue
        score = similarity(item, other)
        if score >= 0.18:
            matches.append((other.item_id, score))
    return sorted(matches, key=lambda pair: pair[1], reverse=True)

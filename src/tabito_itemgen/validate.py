from __future__ import annotations

from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from .io import load_json
from .models import Item


def validate_item_file(path: Path) -> tuple[Item | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        item = Item.model_validate(load_json(path))
    except (ValidationError, ValueError) as exc:
        return None, [str(exc)], []

    answers = [q.correct_option for q in item.questions]
    counts = Counter(answers)
    if answers and max(counts.values()) >= max(3, len(answers) - 1):
        warnings.append(f"answer-position imbalance: {dict(counts)}")

    operations = {q.operation for q in item.questions}
    if len(operations) < 3:
        warnings.append(f"low cognitive-operation variety: {sorted(operations)}")

    cross_material = sum(1 for q in item.questions if len(q.evidence.material_ids) >= 2)
    if cross_material < 1:
        errors.append("Q4 requires at least one cross-material question")

    for q in item.questions:
        distractor_keys = set(q.distractor_rationales_ja.keys())
        expected = {str(i) for i in range(1, len(q.options) + 1) if i != q.correct_option}
        if distractor_keys != expected:
            warnings.append(
                f"{q.question_id}: distractor rationale keys {sorted(distractor_keys)} "
                f"!= expected {sorted(expected)}"
            )

    return item, errors, warnings

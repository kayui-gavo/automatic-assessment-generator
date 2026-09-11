from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import ValidationError

from .io import load_json
from .models import Item, Review, SocialFeedMaterial, TextMaterial

CURRENT_BLUEPRINT_VERSION = "R8-2026-main-tsui-v2"


def _expected_distractor_keys(task) -> set[str]:
    correct = {slot.correct_option for slot in task.answer_slots}
    return {str(i) for i in range(1, len(task.options) + 1) if i not in correct}


def _derived_dependency_mode(task, material_map) -> str:
    if task.dependency_mode is not None:
        return task.dependency_mode
    ids = list(dict.fromkeys(e.material_id for e in task.evidence))
    if len(ids) <= 1:
        return "single_source"
    bundle_ids = [material_map[mid].bundle_id for mid in ids]
    if bundle_ids and bundle_ids[0] is not None and len(set(bundle_ids)) == 1:
        return "within_compound"
    return "cross_source"


def _validate_dependency_mode(task, material_map) -> list[str]:
    errors: list[str] = []
    ids = list(dict.fromkeys(e.material_id for e in task.evidence))
    if task.dependency_mode == "single_source" and len(ids) != 1:
        errors.append(f"{task.task_id}: dependency_mode=single_source but evidence uses {len(ids)} materials")
    elif task.dependency_mode == "cross_source":
        if len(ids) < 2:
            errors.append(f"{task.task_id}: dependency_mode=cross_source requires at least two materials")
        else:
            bundle_ids = [material_map[mid].bundle_id for mid in ids]
            non_null = [bundle for bundle in bundle_ids if bundle is not None]
            if non_null and len(non_null) == len(ids) and len(set(non_null)) == 1:
                errors.append(
                    f"{task.task_id}: evidence belongs to one bundle; use dependency_mode=within_compound"
                )
    elif task.dependency_mode == "within_compound":
        if len(ids) >= 2:
            bundle_ids = [material_map[mid].bundle_id for mid in ids]
            if any(bundle is None for bundle in bundle_ids) or len(set(bundle_ids)) != 1:
                errors.append(
                    f"{task.task_id}: within_compound with multiple materials requires one shared bundle_id"
                )
        elif len(ids) == 1:
            material = material_map[ids[0]]
            if not isinstance(material, SocialFeedMaterial) and material.type not in {
                "flowchart",
                "schematic_map",
                "annotated_diagram",
            }:
                errors.append(
                    f"{task.task_id}: within_compound with one material is reserved for internally compound material types"
                )
    return errors


def validate_item_file(path: Path) -> tuple[Item | None, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        item = Item.model_validate(load_json(path))
    except (ValidationError, ValueError) as exc:
        return None, [str(exc)], []

    material_map = {m.material_id: m for m in item.materials}

    if item.workflow.blueprint_version != CURRENT_BLUEPRINT_VERSION:
        warnings.append(
            f"item blueprint_version={item.workflow.blueprint_version!r}; current generation baseline is {CURRENT_BLUEPRINT_VERSION!r}"
        )

    slots = [slot for task in item.tasks for slot in task.answer_slots]
    answers = [slot.correct_option for slot in slots]
    counts = Counter(answers)
    if len(slots) >= 8 and counts and max(counts.values()) > max(4, len(slots) * 0.4):
        warnings.append(f"answer-position imbalance: {dict(sorted(counts.items()))}")

    operations = {op for task in item.tasks for op in task.operations}
    minimum_ops = 4 if item.scope == "full" else 3
    if len(operations) < minimum_ops:
        warnings.append(f"low cognitive-operation variety: {sorted(operations)}")

    for task in item.tasks:
        errors.extend(_validate_dependency_mode(task, material_map))

    if item.scope == "full":
        integrative_modes = {"within_compound", "cross_source", "scenario_plus_source"}
        for subsection in ("A", "B"):
            subsection_tasks = [task for task in item.tasks if task.subsection == subsection]
            if not any(_derived_dependency_mode(task, material_map) in integrative_modes for task in subsection_tasks):
                errors.append(
                    f"full Q4 subsection {subsection} requires at least one genuinely integrative task"
                )

    material_types = {m.type for m in item.materials}
    if item.scope == "full" and len(material_types) < 3:
        warnings.append(f"low material-type variety: {sorted(material_types)}")
    if item.scope == "full" and not material_types.intersection(
        {"table", "timetable", "chart", "flowchart", "social_feed", "schematic_map", "annotated_diagram"}
    ):
        errors.append("full Q4 requires structured or visual information, as in both 2026 Tier-1 papers")

    bundle_subsections: dict[str, set[str]] = defaultdict(set)
    for material in item.materials:
        if material.bundle_id:
            bundle_subsections[material.bundle_id].add(material.subsection)
    for bundle_id, subsections in bundle_subsections.items():
        if len(subsections) > 1:
            errors.append(f"bundle_id {bundle_id!r} spans subsections {sorted(subsections)}")

    referenced_materials = {
        evidence.material_id for task in item.tasks for evidence in task.evidence
    }
    unused_materials = [m.material_id for m in item.materials if m.material_id not in referenced_materials]
    if unused_materials:
        warnings.append(f"materials not referenced by task evidence: {unused_materials}")
        if item.scope == "full" and len(unused_materials) > max(2, len(item.materials) // 3):
            errors.append("too many materials appear decorative or unused")

    if item.scope == "full":
        multi_select_tasks = [task for task in item.tasks if task.response_mode == "multi_select"]
        if not multi_select_tasks:
            errors.append("full 2026-style Q4 should include multi_select; both Tier-1 papers use it substantially")
        for subsection in ("A", "B"):
            if not any(task.response_mode == "multi_select" and task.subsection == subsection for task in item.tasks):
                warnings.append(
                    f"subsection {subsection} has no multi_select task despite its prominence in both 2026 Tier-1 papers"
                )

    extraction_slots = sum(
        len(task.answer_slots)
        for task in item.tasks
        if set(task.operations).issubset({"extract"})
    )
    if slots and extraction_slots / len(slots) > 0.5:
        warnings.append(
            f"direct-extraction tasks account for {extraction_slots}/{len(slots)} answer slots; Q4 may be too shallow"
        )

    for subsection in ("A", "B"):
        if item.scope == "full":
            subsection_slots = sum(
                len(task.answer_slots) for task in item.tasks if task.subsection == subsection
            )
            if subsection_slots < 4:
                warnings.append(f"subsection {subsection} has only {subsection_slots} answer slots")

    for task in item.tasks:
        if task.response_mode == "multi_slot_choice":
            slot_ids = {slot.slot_id for slot in task.answer_slots}
            rationale_slot_ids = set(task.slot_distractor_rationales_ja)
            if rationale_slot_ids != slot_ids:
                warnings.append(
                    f"{task.task_id}: slot distractor rationale ids {sorted(rationale_slot_ids)} "
                    f"!= expected {sorted(slot_ids)}"
                )
            for slot in task.answer_slots:
                keys = set(task.slot_distractor_rationales_ja.get(slot.slot_id, {}))
                expected = {
                    str(i) for i in range(1, len(task.options) + 1) if i != slot.correct_option
                }
                if keys != expected:
                    warnings.append(
                        f"{task.task_id}/{slot.slot_id}: distractor rationale keys {sorted(keys)} "
                        f"!= expected {sorted(expected)}"
                    )
        else:
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
        if task.dependency_mode is None:
            warnings.append(
                f"{task.task_id}: dependency_mode omitted; inferred as {_derived_dependency_mode(task, material_map)}"
            )

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

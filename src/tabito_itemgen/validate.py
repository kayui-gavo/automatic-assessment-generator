from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import ValidationError

from .io import load_json
from .models import Item, Review, SocialFeedMaterial, TextMaterial

CURRENT_BLUEPRINT_VERSION = "R8-2026-main-tsui-v3"


def _expected_distractor_keys(task) -> set[str]:
    correct = {slot.correct_option for slot in task.answer_slots}
    return {str(i) for i in range(1, len(task.options) + 1) if i not in correct}


def _task_answer_set(task) -> frozenset[int]:
    return frozenset(slot.answer_number for slot in task.answer_slots)


def _task_slot_groups(item: Item, subsection: str) -> set[frozenset[int]]:
    return {_task_answer_set(task) for task in item.tasks if task.subsection == subsection}


def _task_for_slots(item: Item, slots: set[int]):
    target = frozenset(slots)
    return next((task for task in item.tasks if _task_answer_set(task) == target), None)


def _validate_2026_surface_grammar(item: Item, raw: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if item.scope != "full":
        return errors, warnings

    family = raw.get("surface_family")
    if family not in {"main_2026", "makeup_2026"}:
        errors.append(
            "full Q4 requires surface_family='main_2026' or 'makeup_2026'; "
            "generic multi-source Q4s are no longer accepted"
        )
        return errors, warnings

    a_numbers = sorted(
        slot.answer_number
        for task in item.tasks
        if task.subsection == "A"
        for slot in task.answer_slots
    )
    b_numbers = sorted(
        slot.answer_number
        for task in item.tasks
        if task.subsection == "B"
        for slot in task.answer_slots
    )
    if a_numbers != list(range(21, 29)):
        errors.append(f"2026 Q4 surface grammar requires A=21..28 exactly; got {a_numbers}")
    if b_numbers != list(range(29, 37)):
        errors.append(f"2026 Q4 surface grammar requires B=29..36 exactly; got {b_numbers}")

    a_groups = _task_slot_groups(item, "A")
    common_a_required = {frozenset({21, 22}), frozenset({27, 28})}
    missing_common = common_a_required - a_groups
    if missing_common:
        errors.append(
            "2026 A requires one dialogue task for 21-22 and one lecture/memo task for 27-28; "
            f"missing groups: {sorted(map(sorted, missing_common))}"
        )

    if family == "main_2026":
        expected_a = {
            frozenset({21, 22}),
            frozenset({23, 24}),
            frozenset({25}),
            frozenset({26}),
            frozenset({27, 28}),
        }
        expected_b = {
            frozenset({29, 30}),
            frozenset({31, 32}),
            frozenset({33}),
            frozenset({34}),
            frozenset({35, 36}),
        }
    else:
        expected_a = {
            frozenset({21, 22}),
            frozenset({23, 24}),
            frozenset({25, 26}),
            frozenset({27, 28}),
        }
        expected_b = {
            frozenset({29, 30}),
            frozenset({31, 32}),
            frozenset({33, 34}),
            frozenset({35, 36}),
        }

    if a_groups != expected_a:
        errors.append(
            f"{family} A task-slot grouping mismatch: expected "
            f"{sorted(map(sorted, expected_a))}, got {sorted(map(sorted, a_groups))}"
        )
    b_groups = _task_slot_groups(item, "B")
    if b_groups != expected_b:
        errors.append(
            f"{family} B task-slot grouping mismatch: expected "
            f"{sorted(map(sorted, expected_b))}, got {sorted(map(sorted, b_groups))}"
        )

    q1 = _task_for_slots(item, {21, 22})
    if q1:
        evidence_types = {
            next((m.type for m in item.materials if m.material_id == evidence.material_id), None)
            for evidence in q1.evidence
        }
        if "dialogue" not in evidence_types:
            errors.append("2026 A Q1 (21-22) must be based on a Chinese dialogue material")
        if q1.response_mode != "multi_select":
            errors.append("2026 A Q1 (21-22) should be a two-answer multi_select")

    q3 = _task_for_slots(item, {27, 28})
    if q3 and q3.response_mode != "multi_select":
        errors.append("2026 A Q3 (27-28) should be a two-answer multi_select")

    if family == "main_2026":
        b1 = _task_for_slots(item, {29, 30})
        b_match = _task_for_slots(item, {31, 32})
        b_flow = _task_for_slots(item, {35, 36})
        if b1 and b1.response_mode != "multi_select":
            warnings.append("main_2026 B Q1 (29-30) is expected to be a choose-two task")
        if b_match:
            evidence_types = {
                next((m.type for m in item.materials if m.material_id == evidence.material_id), None)
                for evidence in b_match.evidence
            }
            if not evidence_types.intersection({"profile", "table", "checklist"}):
                warnings.append("main_2026 B Q2 (31-32) should visibly involve profile/candidate matching")
        if b_flow:
            evidence_types = {
                next((m.type for m in item.materials if m.material_id == evidence.material_id), None)
                for evidence in b_flow.evidence
            }
            if "flowchart" not in evidence_types:
                warnings.append("main_2026 B Q3 case application (35-36) normally requires a rule/flow structure")
    else:
        b_plan = _task_for_slots(item, {29, 30})
        b_compound = _task_for_slots(item, {31, 32})
        b_reflect = _task_for_slots(item, {35, 36})
        if b_plan:
            evidence_types = {
                next((m.type for m in item.materials if m.material_id == evidence.material_id), None)
                for evidence in b_plan.evidence
            }
            if not evidence_types.intersection({"social_feed", "timetable", "notice"}):
                warnings.append("makeup_2026 B Q1 (29-30) should use chronological/operational information")
        if b_compound and len({e.material_id for e in b_compound.evidence}) < 2:
            warnings.append("makeup_2026 B Q2 (31-32) should read as a compound operational source")
        if b_reflect:
            evidence_types = {
                next((m.type for m in item.materials if m.material_id == evidence.material_id), None)
                for evidence in b_reflect.evidence
            }
            if not evidence_types.intersection({"reflection", "memo", "short_explanatory_text"}):
                warnings.append("makeup_2026 B Q3 (35-36) should close with reflection/summary-type material")

    return errors, warnings


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
                errors.append(f"{task.task_id}: evidence belongs to one bundle; use dependency_mode=within_compound")
    elif task.dependency_mode == "within_compound":
        if len(ids) >= 2:
            bundle_ids = [material_map[mid].bundle_id for mid in ids]
            if any(bundle is None for bundle in bundle_ids) or len(set(bundle_ids)) != 1:
                errors.append(f"{task.task_id}: within_compound with multiple materials requires one shared bundle_id")
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
        raw = load_json(path)
        item = Item.model_validate(raw)
    except (ValidationError, ValueError) as exc:
        return None, [str(exc)], []

    material_map = {m.material_id: m for m in item.materials}

    if item.workflow.blueprint_version != CURRENT_BLUEPRINT_VERSION:
        warnings.append(
            f"item blueprint_version={item.workflow.blueprint_version!r}; current generation baseline is {CURRENT_BLUEPRINT_VERSION!r}"
        )

    surface_errors, surface_warnings = _validate_2026_surface_grammar(item, raw)
    errors.extend(surface_errors)
    warnings.extend(surface_warnings)

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
                errors.append(f"full Q4 subsection {subsection} requires at least one genuinely integrative task")

    material_types = {m.type for m in item.materials}
    if item.scope == "full" and len(material_types) < 3:
        warnings.append(f"low material-type variety: {sorted(material_types)}")
    if item.scope == "full" and not material_types.intersection(
        {"table", "timetable", "chart", "flowchart", "social_feed", "schematic_map", "annotated_diagram"}
    ):
        errors.append("full Q4 requires structured or visual information")

    bundle_subsections: dict[str, set[str]] = defaultdict(set)
    for material in item.materials:
        if material.bundle_id:
            bundle_subsections[material.bundle_id].add(material.subsection)
    for bundle_id, subsections in bundle_subsections.items():
        if len(subsections) > 1:
            errors.append(f"bundle_id {bundle_id!r} spans subsections {sorted(subsections)}")

    referenced_materials = {evidence.material_id for task in item.tasks for evidence in task.evidence}
    unused_materials = [m.material_id for m in item.materials if m.material_id not in referenced_materials]
    if unused_materials:
        warnings.append(f"materials not referenced by task evidence: {unused_materials}")
        if item.scope == "full" and len(unused_materials) > max(2, len(item.materials) // 3):
            errors.append("too many materials appear decorative or unused")

    if item.scope == "full":
        multi_select_tasks = [task for task in item.tasks if task.response_mode == "multi_select"]
        if not multi_select_tasks:
            errors.append("full 2026-style Q4 should include multi_select substantially")

    extraction_slots = sum(
        len(task.answer_slots)
        for task in item.tasks
        if set(task.operations).issubset({"extract"})
    )
    if slots and extraction_slots / len(slots) > 0.5:
        warnings.append(
            f"direct-extraction tasks account for {extraction_slots}/{len(slots)} answer slots; Q4 may be too shallow"
        )

    for task in item.tasks:
        if task.response_mode == "multi_slot_choice":
            slot_ids = {slot.slot_id for slot in task.answer_slots}
            rationale_slot_ids = set(task.slot_distractor_rationales_ja)
            if rationale_slot_ids != slot_ids:
                warnings.append(
                    f"{task.task_id}: slot distractor rationale ids {sorted(rationale_slot_ids)} != expected {sorted(slot_ids)}"
                )
            for slot in task.answer_slots:
                keys = set(task.slot_distractor_rationales_ja.get(slot.slot_id, {}))
                expected = {str(i) for i in range(1, len(task.options) + 1) if i != slot.correct_option}
                if keys != expected:
                    warnings.append(
                        f"{task.task_id}/{slot.slot_id}: distractor rationale keys {sorted(keys)} != expected {sorted(expected)}"
                    )
        else:
            distractor_keys = set(task.distractor_rationales_ja.keys())
            expected = _expected_distractor_keys(task)
            if distractor_keys != expected:
                warnings.append(
                    f"{task.task_id}: distractor rationale keys {sorted(distractor_keys)} != expected {sorted(expected)}"
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

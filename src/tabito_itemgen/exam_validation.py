from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .exam_models import ExamManifest, Q1DialogueTask, Q1PhoneticCountTask, Q1Section, Q2OrderingTask, Q2Section, Q3Section, Q5Section
from .io import load_json
from .models import Item
from .section_io import load_section, section_answer_numbers, section_fingerprint, section_id
from .validate import validate_item_file

_TONE_MARK_RE = re.compile(r"[āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ]")


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.errors


def _has_tone_mark(text: str) -> bool:
    return bool(_TONE_MARK_RE.search(text))


def _validate_q1(section: Q1Section) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    for task in section.tasks:
        if isinstance(task, Q1PhoneticCountTask):
            words = [task.headword, *task.candidates]
            for word in words:
                if not _has_tone_mark(word.pinyin):
                    errors.append(f"{task.task_id}: pinyin for {word.label!r} has no Unicode tone mark")
        elif isinstance(task, Q1DialogueTask):
            if not any(_has_tone_mark(line.pinyin) for line in task.lines):
                errors.append(f"{task.task_id}: dialogue has no Unicode tone-marked pinyin")
        if task.answer_slot.correct_option > len(task.options):
            errors.append(f"{task.task_id}: correct option exceeds option count")
    return ValidationResult(tuple(errors), tuple(warnings))


def _validate_q2(section: Q2Section) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    for task in section.tasks:
        if isinstance(task, Q2OrderingTask):
            if len(task.token_pool) != 8 or len(task.correct_sequence) != 4:
                errors.append(f"{task.task_id}: ordering task must use 8 tokens and a 4-token answer")
        else:
            if task.answer_slot.correct_option > len(task.options):
                errors.append(f"{task.task_id}: correct option exceeds option count")
    return ValidationResult(tuple(errors), tuple(warnings))


def _validate_q3(section: Q3Section) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    for task in section.tasks:
        if task.answer_slot.correct_option > len(task.options):
            errors.append(f"{task.task_id}: correct option exceeds option count")
        wrong = {str(index) for index in range(1, len(task.options) + 1)} - {str(task.answer_slot.correct_option)}
        missing_types = wrong - set(task.distractor_error_types)
        missing_reasons = wrong - set(task.distractor_rationales_ja)
        if missing_types:
            errors.append(f"{task.task_id}: missing distractor error types for {sorted(missing_types)}")
        if missing_reasons:
            errors.append(f"{task.task_id}: missing distractor rationales for {sorted(missing_reasons)}")
        chinese_texts = task.options if task.direction == "ja_to_zh" else [task.source_text]
        if not any(_has_tone_mark(text) for text in chinese_texts):
            errors.append(f"{task.task_id}: expected tone-marked pinyin is missing")
    return ValidationResult(tuple(errors), tuple(warnings))


def _validate_q5(section: Q5Section) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if len(section.originality_statement.strip()) < 10:
        errors.append("Q5 originality_statement is too short")
    anchored = {anchor.anchor_id for anchor in section.anchors}
    referenced = {anchor for task in section.tasks for anchor in task.anchor_refs}
    unused = sorted(anchored - referenced)
    if unused:
        warnings.append(f"Q5 anchors not referenced by any task: {unused}")
    if not any(task.operation == "whole_text_consistency" for task in section.tasks):
        errors.append("Q5 requires a whole-text consistency task")
    if not any(task.operation in {"lexical_choice", "sentence_choice", "discourse_connector"} for task in section.tasks):
        errors.append("Q5 requires at least one language-form choice task")
    return ValidationResult(tuple(errors), tuple(warnings))


def validate_section_file(path: Path) -> ValidationResult:
    try:
        raw = load_json(path)
    except (ValueError, OSError) as exc:
        return ValidationResult((str(exc),), ())
    if raw.get("section") == "Q4":
        _, errors, warnings = validate_item_file(path)
        return ValidationResult(tuple(errors), tuple(warnings))
    try:
        section = load_section(path)
    except (ValidationError, ValueError) as exc:
        return ValidationResult((str(exc),), ())
    if isinstance(section, Q1Section):
        return _validate_q1(section)
    if isinstance(section, Q2Section):
        return _validate_q2(section)
    if isinstance(section, Q3Section):
        return _validate_q3(section)
    if isinstance(section, Q5Section):
        return _validate_q5(section)
    return ValidationResult((f"unsupported section type {type(section)!r}",), ())


def _correct_options(section) -> list[int]:
    if isinstance(section, Item):
        return [slot.correct_option for task in section.tasks for slot in task.answer_slots]
    if isinstance(section, Q1Section):
        return [task.answer_slot.correct_option for task in section.tasks]
    if isinstance(section, Q2Section):
        values: list[int] = []
        for task in section.tasks:
            if isinstance(task, Q2OrderingTask):
                values.extend(slot.correct_option for slot in task.answer_slots)
            else:
                values.append(task.answer_slot.correct_option)
        return values
    if isinstance(section, Q3Section):
        return [task.answer_slot.correct_option for task in section.tasks]
    if isinstance(section, Q5Section):
        return [slot.correct_option for task in section.tasks for slot in task.answer_slots]
    return []


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    normalized = re.sub(r"\s+", "", text.lower())
    if len(normalized) < n:
        return {normalized} if normalized else set()
    return {normalized[index:index + n] for index in range(len(normalized) - n + 1)}


def _topic_similarity(a: str, b: str) -> float:
    left, right = _char_ngrams(a), _char_ngrams(b)
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def validate_exam(manifest_path: Path) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = ExamManifest.model_validate(load_json(manifest_path))
    except (ValidationError, ValueError, OSError) as exc:
        return ValidationResult((str(exc),), ())

    exam_dir = manifest_path.parent
    loaded: dict[str, object] = {}
    all_numbers: list[int] = []
    all_ids: list[str] = []
    all_correct: list[int] = []

    for ref in manifest.sections:
        if not ref.path:
            errors.append(f"{ref.section}: section file is missing")
            continue
        path = exam_dir / ref.path
        if not path.exists():
            errors.append(f"{ref.section}: section file does not exist: {ref.path}")
            continue
        result = validate_section_file(path)
        errors.extend(f"{ref.section}: {message}" for message in result.errors)
        warnings.extend(f"{ref.section}: {message}" for message in result.warnings)
        try:
            section = load_section(path)
        except (ValidationError, ValueError) as exc:
            errors.append(f"{ref.section}: cannot load section after validation: {exc}")
            continue
        if section.section != ref.section:
            errors.append(f"{ref.section}: file contains section={section.section}")
        loaded[ref.section] = section
        numbers = section_answer_numbers(section)
        expected = list(range(ref.answer_start, ref.answer_end + 1))
        if numbers != expected:
            errors.append(f"{ref.section}: expected answer numbers {expected}, got {numbers}")
        all_numbers.extend(numbers)
        all_ids.append(section_id(section))
        all_correct.extend(_correct_options(section))
        fingerprint = section_fingerprint(section)
        if ref.fingerprint and ref.fingerprint != fingerprint:
            errors.append(f"{ref.section}: manifest fingerprint is stale")

    if sorted(all_numbers) != list(range(1, 51)):
        errors.append("exam must contain answer numbers 1 through 50 exactly once")
    if len(all_numbers) != len(set(all_numbers)):
        errors.append("exam contains duplicated answer numbers")
    if len(all_ids) != len(set(all_ids)):
        errors.append("exam contains duplicated section ids")

    q4 = loaded.get("Q4")
    q5 = loaded.get("Q5")
    if isinstance(q4, Item) and q4.surface_family != manifest.exam_family:
        errors.append(f"Q4 family {q4.surface_family!r} does not match exam family {manifest.exam_family!r}")
    if isinstance(q5, Q5Section) and q5.surface_family != manifest.exam_family:
        errors.append(f"Q5 family {q5.surface_family!r} does not match exam family {manifest.exam_family!r}")

    if all_correct:
        counts = Counter(all_correct)
        if max(counts.values()) > len(all_correct) * 0.35:
            warnings.append(f"exam correct-option distribution may be imbalanced: {dict(sorted(counts.items()))}")

    if isinstance(q4, Item) and isinstance(q5, Q5Section):
        similarity = _topic_similarity(q4.topic, q5.topic)
        if similarity >= 0.35:
            warnings.append(f"Q4 and Q5 topics may be too similar (character 3-gram Jaccard={similarity:.2f})")

    return ValidationResult(tuple(errors), tuple(warnings))

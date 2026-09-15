from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from pydantic import TypeAdapter

from .exam_models import (
    Q1PhoneticCountTask,
    Q1Section,
    Q2OrderingTask,
    Q2Section,
    Q3Section,
    Q5Section,
    SECTION_SPECS,
    SectionData,
)
from .io import dump_json, load_json
from .models import Item

_SECTION_ADAPTER = TypeAdapter(SectionData)


def _canonicalize_presentation(section: SectionData) -> SectionData:
    """Normalize presentation-only fields that must never be model-controlled.

    Q1 candidate markers are fixed booklet labels (a-d), not authored content.
    Older or malformed JSON may contain arbitrary ``PinyinWord.label`` values;
    normalizing them here keeps browser preview, blind review and PDF output on
    the exact same visible surface without changing legitimate question content.
    """

    if not isinstance(section, Q1Section):
        return section

    normalized = section.model_copy(deep=True)
    for task in normalized.tasks:
        if not isinstance(task, Q1PhoneticCountTask):
            continue
        for index, candidate in enumerate(task.candidates):
            candidate.label = chr(ord("a") + index)
    return normalized


def load_section(path: Path) -> SectionData:
    return _canonicalize_presentation(_SECTION_ADAPTER.validate_python(load_json(path)))


def save_section(path: Path, section: SectionData) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(path, _canonicalize_presentation(section).model_dump())
    return path


def section_id(section: SectionData) -> str:
    return section.item_id if isinstance(section, Item) else section.section_id


def section_kind(section: SectionData) -> str:
    return section.section


def section_score(section: SectionData) -> int:
    return SECTION_SPECS[section.section][0]


def section_answer_numbers(section: SectionData) -> list[int]:
    if isinstance(section, Item):
        return sorted(slot.answer_number for task in section.tasks for slot in task.answer_slots)
    if isinstance(section, Q1Section):
        return sorted(task.answer_slot.answer_number for task in section.tasks)
    if isinstance(section, Q2Section):
        numbers: list[int] = []
        for task in section.tasks:
            if isinstance(task, Q2OrderingTask):
                numbers.extend(slot.answer_number for slot in task.answer_slots)
            else:
                numbers.append(task.answer_slot.answer_number)
        return sorted(numbers)
    if isinstance(section, Q3Section):
        return sorted(task.answer_slot.answer_number for task in section.tasks)
    if isinstance(section, Q5Section):
        return sorted(slot.answer_number for task in section.tasks for slot in task.answer_slots)
    raise TypeError(f"unsupported section type: {type(section)!r}")


def section_fingerprint(section: SectionData) -> str:
    payload = _canonicalize_presentation(section).model_dump()
    workflow = payload.get("workflow")
    if isinstance(workflow, dict):
        workflow.pop("state", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _archive_previous_candidate(
    exam_dir: Path,
    path: Path,
    incoming_fingerprint: str,
) -> None:
    """Preserve the previous candidate before a content-changing overwrite.

    Revision and structure-fix imports intentionally become the current draft even
    when deterministic validation still reports issues. Without this archive a
    single bad import permanently destroyed the last usable candidate. History is
    content-addressed, so repeated imports of the same version do not create noise.
    """

    if not path.exists():
        return
    try:
        current = load_section(path)
        fingerprint = section_fingerprint(current)
        if fingerprint == incoming_fingerprint:
            return
    except Exception:
        # A corrupt existing file is still worth preserving for forensic recovery.
        fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()

    history_dir = exam_dir / "history" / path.stem
    history_dir.mkdir(parents=True, exist_ok=True)
    target = history_dir / f"{fingerprint}.json"
    if not target.exists():
        shutil.copy2(path, target)


def save_section_draft(exam_dir: Path, section: SectionData) -> Path:
    draft = _canonicalize_presentation(section).model_copy(deep=True)
    draft.workflow.state = "draft"
    path = exam_dir / "sections" / f"{draft.section.lower()}.json"
    _archive_previous_candidate(exam_dir, path, section_fingerprint(draft))
    return save_section(path, draft)

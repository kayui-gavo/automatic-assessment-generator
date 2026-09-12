from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import TypeAdapter

from .exam_models import (
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


def load_section(path: Path) -> SectionData:
    return _SECTION_ADAPTER.validate_python(load_json(path))


def save_section(path: Path, section: SectionData) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(path, section.model_dump())
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
    payload = section.model_dump()
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


def save_section_draft(exam_dir: Path, section: SectionData) -> Path:
    draft = section.model_copy(deep=True)
    draft.workflow.state = "draft"
    path = exam_dir / "sections" / f"{draft.section.lower()}.json"
    return save_section(path, draft)

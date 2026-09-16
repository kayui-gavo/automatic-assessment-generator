from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import TypeAdapter

from .exam_models import Q5Section, SectionData
from .exam_production import (
    exam_workspace_dir,
    import_section_response as _import_section_response,
    load_manifest,
    manifest_path,
)
from .io import dump_json
from .models import Item
from .production import parse_chat_json
from .section_io import _canonicalize_presentation, _validate_surface_contract

_SECTION_ADAPTER = TypeAdapter(SectionData)


def _validated_response_data(
    root: Path,
    exam_id: str,
    section_name: str,
    text: str,
) -> dict:
    """Validate identity and renderability before the mutable import path runs.

    ``exam_production.import_section_response`` intentionally accepts candidates
    that still have deterministic quality errors so teachers can repair them in
    the workbench. What must not overwrite raw-response provenance, however, is
    malformed JSON, the wrong section/exam identity, or metadata that cannot
    render the promised student surface at all.
    """

    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    data = parse_chat_json(text)

    if data.get("section") != section_name:
        raise ValueError(
            f"response section {data.get('section')!r} does not match {section_name}"
        )
    incoming_id = data.get("item_id") if section_name == "Q4" else data.get("section_id")
    if incoming_id != ref.section_id:
        raise ValueError(
            f"response section id {incoming_id!r} does not match request {ref.section_id!r}"
        )

    section = _canonicalize_presentation(_SECTION_ADAPTER.validate_python(data))
    _validate_surface_contract(section)
    if isinstance(section, (Item, Q5Section)) and section.surface_family != manifest.exam_family:
        raise ValueError(
            f"{section_name} surface family {section.surface_family!r} "
            f"does not match exam family {manifest.exam_family!r}"
        )
    return data


def _response_root(root: Path, exam_id: str) -> Path:
    return exam_workspace_dir(root, exam_id) / "responses"


def _archive_raw_response(
    root: Path,
    exam_id: str,
    section_name: str,
    data: dict,
) -> Path:
    """Store each distinct accepted model response once, keyed by content hash."""

    encoded = (
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    directory = _response_root(root, exam_id) / "history" / section_name.lower()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{digest}.json"
    if not path.exists():
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return path


def import_section_response(
    root: Path,
    exam_id: str,
    section_name: str,
    text: str,
):
    """Import a model response and preserve latest + immutable raw provenance."""

    data = _validated_response_data(root, exam_id, section_name, text)
    result = _import_section_response(root, exam_id, section_name, text)

    response_root = _response_root(root, exam_id)
    response_root.mkdir(parents=True, exist_ok=True)
    dump_json(response_root / f"{section_name.lower()}.response.json", data)
    _archive_raw_response(root, exam_id, section_name, data)
    return result

import json

import pytest

import tabito_itemgen.cli as cli
import tabito_itemgen.response_audit as response_audit
from tabito_itemgen.exam_production import (
    exam_workspace_dir,
    import_section_response as import_candidate_without_audit,
    load_manifest,
    manifest_path,
)
from tabito_itemgen.response_audit import import_section_response
from tabito_itemgen.section_io import load_section

from tests.full_exam_factory import build_exam


def _section_context(root, exam_id, section_name):
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    path = manifest_path(root, exam_id).parent / ref.path
    return ref, path, load_section(path)


def test_cli_uses_same_audited_section_import_as_teacher_ui():
    assert cli.import_section_response is response_audit.import_section_response


def test_valid_ui_import_keeps_latest_and_content_addressed_raw_history(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    ref, _, section = _section_context(tmp_path, manifest.exam_id, "Q3")
    revised = section.model_copy(deep=True)
    revised.tasks[0].source_text += "（审计版）"

    import_section_response(
        tmp_path,
        manifest.exam_id,
        "Q3",
        revised.model_dump_json(),
    )

    response_root = exam_workspace_dir(tmp_path, manifest.exam_id) / "responses"
    latest = response_root / "q3.response.json"
    history = list((response_root / "history" / "q3").glob("*.json"))

    assert latest.exists()
    assert len(history) == 1
    assert json.loads(latest.read_text(encoding="utf-8"))["section_id"] == ref.section_id
    assert json.loads(history[0].read_text(encoding="utf-8")) == json.loads(
        latest.read_text(encoding="utf-8")
    )

    # Re-importing identical model output is idempotent in audit history.
    import_section_response(
        tmp_path,
        manifest.exam_id,
        "Q3",
        revised.model_dump_json(),
    )
    assert len(list((response_root / "history" / "q3").glob("*.json"))) == 1


def test_rollback_changes_candidate_without_rewriting_model_response_provenance(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    _, _, original = _section_context(tmp_path, manifest.exam_id, "Q3")
    revised = original.model_copy(deep=True)
    revised.tasks[0].source_text += "（模型新版本）"

    import_section_response(
        tmp_path,
        manifest.exam_id,
        "Q3",
        revised.model_dump_json(),
    )
    response_root = exam_workspace_dir(tmp_path, manifest.exam_id) / "responses"
    latest = response_root / "q3.response.json"
    latest_before = latest.read_text(encoding="utf-8")
    history_before = {
        path.name: path.read_text(encoding="utf-8")
        for path in (response_root / "history" / "q3").glob("*.json")
    }

    # The UI rollback path deliberately uses the provenance-neutral core import.
    import_candidate_without_audit(
        tmp_path,
        manifest.exam_id,
        "Q3",
        original.model_dump_json(),
    )

    _, _, restored = _section_context(tmp_path, manifest.exam_id, "Q3")
    assert restored.tasks[0].source_text == original.tasks[0].source_text
    assert latest.read_text(encoding="utf-8") == latest_before
    assert {
        path.name: path.read_text(encoding="utf-8")
        for path in (response_root / "history" / "q3").glob("*.json")
    } == history_before


def test_malformed_or_unrenderable_ui_import_cannot_overwrite_latest_raw_response(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    _, _, section = _section_context(tmp_path, manifest.exam_id, "Q5")

    import_section_response(
        tmp_path,
        manifest.exam_id,
        "Q5",
        section.model_dump_json(),
    )
    response_root = exam_workspace_dir(tmp_path, manifest.exam_id) / "responses"
    latest = response_root / "q5.response.json"
    before = latest.read_text(encoding="utf-8")
    history_before = set((response_root / "history" / "q5").glob("*.json"))

    with pytest.raises(ValueError):
        import_section_response(tmp_path, manifest.exam_id, "Q5", "{not-json")
    assert latest.read_text(encoding="utf-8") == before

    broken = section.model_copy(deep=True)
    broken.anchors[0].source_excerpt = None
    with pytest.raises(ValueError, match="source_excerpt"):
        import_section_response(
            tmp_path,
            manifest.exam_id,
            "Q5",
            broken.model_dump_json(),
        )

    assert latest.read_text(encoding="utf-8") == before
    assert set((response_root / "history" / "q5").glob("*.json")) == history_before

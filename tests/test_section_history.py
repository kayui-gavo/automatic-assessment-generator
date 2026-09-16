import json

import pytest

from tabito_itemgen.exam_production import (
    import_section_response,
    load_manifest,
    manifest_path,
)
from tabito_itemgen.io import dump_json, load_json
from tabito_itemgen.section_io import load_section, save_section, section_fingerprint

from tests.full_exam_factory import build_exam


def test_section_import_archives_previous_candidate_before_overwrite(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    current = load_manifest(manifest_path(tmp_path, manifest.exam_id))
    ref = next(ref for ref in current.sections if ref.section == "Q3")
    section_path = manifest_path(tmp_path, manifest.exam_id).parent / ref.path
    before = load_section(section_path)
    before_fingerprint = section_fingerprint(before)

    revised = before.model_copy(deep=True)
    revised.tasks[0].source_text += "（改訂版）"
    import_section_response(
        tmp_path,
        manifest.exam_id,
        "Q3",
        revised.model_dump_json(),
    )

    history = (
        manifest_path(tmp_path, manifest.exam_id).parent
        / "history"
        / "q3"
        / f"{before_fingerprint}.json"
    )
    assert history.exists()
    assert section_fingerprint(load_section(history)) == before_fingerprint
    assert section_fingerprint(load_section(section_path)) != before_fingerprint


def test_identical_section_import_does_not_create_history_noise(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    current = load_manifest(manifest_path(tmp_path, manifest.exam_id))
    ref = next(ref for ref in current.sections if ref.section == "Q2")
    section_path = manifest_path(tmp_path, manifest.exam_id).parent / ref.path
    section = load_section(section_path)

    import_section_response(
        tmp_path,
        manifest.exam_id,
        "Q2",
        section.model_dump_json(),
    )

    history_dir = manifest_path(tmp_path, manifest.exam_id).parent / "history" / "q2"
    assert not history_dir.exists()


def test_invalid_import_does_not_replace_current_candidate_or_manifest_binding(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    manifest_file = manifest_path(tmp_path, manifest.exam_id)
    current = load_manifest(manifest_file)
    ref = next(ref for ref in current.sections if ref.section == "Q3")
    section_path = manifest_file.parent / ref.path
    before = load_section(section_path)
    before_fingerprint = section_fingerprint(before)
    before_ref_fingerprint = ref.fingerprint

    broken = before.model_dump()
    del broken["tasks"][0]["source_text"]
    with pytest.raises(Exception):
        import_section_response(
            tmp_path,
            manifest.exam_id,
            "Q3",
            json.dumps(broken, ensure_ascii=False),
        )

    after = load_section(section_path)
    after_manifest = load_manifest(manifest_file)
    after_ref = next(ref for ref in after_manifest.sections if ref.section == "Q3")
    assert section_fingerprint(after) == before_fingerprint
    assert after_ref.fingerprint == before_ref_fingerprint


def test_q1_candidate_labels_are_presentation_owned_not_model_owned(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    current = load_manifest(manifest_path(tmp_path, manifest.exam_id))
    ref = next(ref for ref in current.sections if ref.section == "Q1")
    section_path = manifest_path(tmp_path, manifest.exam_id).parent / ref.path

    # Simulate an older / malformed stored candidate whose authoring labels
    # contain arbitrary text. Loading the section must recover the booklet's
    # fixed a-d labels before any browser/PDF renderer can see them.
    raw = load_json(section_path)
    raw["tasks"][0]["candidates"][0]["label"] = "見出し"
    raw["tasks"][0]["candidates"][1]["label"] = "事情"
    dump_json(section_path, raw)

    q1 = load_section(section_path)
    assert [word.label for word in q1.tasks[0].candidates] == ["a", "b", "c", "d"]

    # Saving the normalized candidate also cleans the persisted representation.
    save_section(section_path, q1)
    stored = load_json(section_path)
    assert [word["label"] for word in stored["tasks"][0]["candidates"]] == [
        "a",
        "b",
        "c",
        "d",
    ]

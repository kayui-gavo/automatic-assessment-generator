from tabito_itemgen.exam_production import (
    import_section_response,
    load_manifest,
    manifest_path,
)
from tabito_itemgen.section_io import load_section, section_fingerprint

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

from pathlib import Path

from tabito_itemgen.artifact_preflight import (
    ArtifactCheck,
    ArtifactManifest,
    preflight_pdf,
    renderer_revision,
)


def _write_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4\n% synthetic test fixture\n")


def test_preflight_rejects_missing_character_and_severe_overfull(tmp_path: Path) -> None:
    tex = tmp_path / "student.tex"
    pdf = tmp_path / "student.pdf"
    log = tmp_path / "student.log"
    tex.write_text("test", encoding="utf-8")
    _write_pdf(pdf)
    log.write_text(
        "Missing character: There is no ℃ in font Liberation Serif\n"
        "Overfull \\hbox (172.9pt too wide) in paragraph at lines 1--2\n"
        "Output written on student.pdf (11 pages).\n",
        encoding="utf-8",
    )

    result = preflight_pdf(tex, pdf)
    assert not result.passed
    assert result.missing_character_count == 1
    assert result.max_overfull_pt == 172.9
    assert result.page_count == 11
    assert any("missing character" in error for error in result.errors)
    assert any("overfull" in error for error in result.errors)


def test_preflight_accepts_clean_pdf_log(tmp_path: Path) -> None:
    tex = tmp_path / "teacher.tex"
    pdf = tmp_path / "teacher.pdf"
    log = tmp_path / "teacher.log"
    tex.write_text("test", encoding="utf-8")
    _write_pdf(pdf)
    log.write_text("Output written on teacher.pdf (14 pages).\n", encoding="utf-8")

    result = preflight_pdf(tex, pdf)
    assert result.passed
    assert result.page_count == 14
    assert result.missing_character_count == 0
    assert result.max_overfull_pt == 0
    assert result.pdf_sha256


def test_preflight_warns_but_does_not_fail_for_tiny_overfull(tmp_path: Path) -> None:
    tex = tmp_path / "answer_sheet.tex"
    pdf = tmp_path / "answer_sheet.pdf"
    log = tmp_path / "answer_sheet.log"
    tex.write_text("test", encoding="utf-8")
    _write_pdf(pdf)
    log.write_text(
        "Overfull \\hbox (2.2pt too wide) in paragraph at lines 1--2\n"
        "Output written on answer_sheet.pdf (1 pages).\n",
        encoding="utf-8",
    )

    result = preflight_pdf(tex, pdf)
    assert result.passed
    assert result.warnings


def test_stale_renderer_manifest_remains_readable_and_preserves_source_revision() -> None:
    current = renderer_revision()
    stale = "renderer-sha256:" + "0" * 64
    assert current != "unknown"
    assert stale != current

    manifest = ArtifactManifest(
        exam_id="EXAM-1",
        exam_fingerprint="f" * 64,
        renderer_revision=stale,
        checks=(
            ArtifactCheck(
                name="student",
                tex_path="student.tex",
                pdf_path="student.pdf",
            ),
        ),
    )

    assert manifest.renderer_revision == "unknown"
    assert manifest.source_renderer_revision == stale


def test_current_renderer_manifest_keeps_current_revision() -> None:
    current = renderer_revision()
    manifest = ArtifactManifest(
        exam_id="EXAM-1",
        exam_fingerprint="f" * 64,
        renderer_revision=current,
        checks=(
            ArtifactCheck(
                name="student",
                tex_path="student.tex",
                pdf_path="student.pdf",
            ),
        ),
    )

    assert manifest.renderer_revision == current
    assert manifest.source_renderer_revision is None

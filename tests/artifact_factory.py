from __future__ import annotations

from pathlib import Path

from tabito_itemgen.artifact_preflight import (
    ArtifactCheck,
    ArtifactManifest,
    renderer_revision,
    sha256_file,
    write_artifact_manifest,
)
from tabito_itemgen.exam_production import exam_artifact_manifest_path, exam_fingerprint


def write_clean_artifacts(root: Path, exam_id: str) -> Path:
    """Create a synthetic but hash-bound preflight snapshot for unit tests.

    XeLaTeX compilation itself is covered by the dedicated full-exam PDF
    workflow. Production/release unit tests only need an immutable artifact
    manifest with the same integrity semantics.
    """

    out = root / "output" / exam_id
    out.mkdir(parents=True, exist_ok=True)
    checks = []
    for name in ("student", "teacher", "answer_sheet"):
        tex = out / f"{name}.tex"
        pdf = out / f"{name}.pdf"
        tex.write_text("synthetic release fixture\n", encoding="utf-8")
        pdf.write_bytes(b"%PDF-1.4\nsynthetic release fixture\n")
        checks.append(
            ArtifactCheck(
                name=name,
                tex_path=str(tex),
                pdf_path=str(pdf),
                pdf_sha256=sha256_file(pdf),
                page_count=1,
            )
        )
    artifact = ArtifactManifest(
        exam_id=exam_id,
        exam_fingerprint=exam_fingerprint(root, exam_id),
        renderer_revision=renderer_revision(root),
        checks=tuple(checks),
    )
    return write_artifact_manifest(artifact, exam_artifact_manifest_path(root, exam_id))

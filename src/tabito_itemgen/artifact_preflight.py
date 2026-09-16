from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from pydantic import BaseModel, Field

_OVERFULL_RE = re.compile(r"Overfull \\hbox \((?P<points>[0-9.]+)pt too wide\)")
_PAGE_RE = re.compile(r"Output written on .*?\((?P<pages>\d+) pages?")

# Only files that can change the generated booklet / answer sheet / canonical
# release artifacts belong here. This keeps unrelated repository commits from
# invalidating a good artifact set while guaranteeing that renderer or scoring
# fixes do.
_RENDERER_SOURCE_FILES = (
    "answer_sheet.py",
    "artifact_preflight.py",
    "exam_render.py",
    "exam_surface.py",
    "presentation.py",
    "render.py",
    "scoring.py",
)
REQUIRED_EXTRA_FILES = ("answer_key.json", "scoring_scheme.json")


class ArtifactCheck(BaseModel):
    name: str
    tex_path: str
    pdf_path: str
    pdf_sha256: str | None = None
    page_count: int | None = None
    max_overfull_pt: float = 0.0
    missing_character_count: int = 0
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return not self.errors


class ArtifactManifest(BaseModel):
    """Immutable evidence describing one rendered artifact set.

    Parsing a historical manifest must never depend on the current repository,
    renderer revision, or filesystem. Runtime freshness/integrity belongs to the
    release gate, so approved evidence remains readable even after outputs are
    cleaned up or the renderer evolves.
    """

    exam_id: str
    exam_fingerprint: str
    renderer_revision: str
    # Retained for backward compatibility with manifests written by an earlier
    # implementation that rewrote stale renderer revisions during parsing.
    source_renderer_revision: str | None = None
    checks: tuple[ArtifactCheck, ...]
    extra_files: dict[str, str] = Field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return (
            bool(self.checks)
            and all(check.passed for check in self.checks)
            and all(filename in self.extra_files for filename in REQUIRED_EXTRA_FILES)
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def renderer_revision(root: Path | None = None) -> str:
    """Fingerprint the implementation that determines canonical release artifacts.

    A Git commit is too broad (README edits would invalidate artifacts) and also
    too weak for release gating because an old artifact merely needed *some*
    known commit. Hash the actual rendering / preflight / scoring source instead.
    The optional root argument remains for API compatibility with existing callers.
    """

    del root
    package_dir = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    try:
        for filename in _RENDERER_SOURCE_FILES:
            path = package_dir / filename
            digest.update(filename.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    except OSError:
        return "unknown"
    return "renderer-sha256:" + digest.hexdigest()


def preflight_pdf(
    tex_path: Path,
    pdf_path: Path,
    *,
    max_allowed_overfull_pt: float = 8.0,
) -> ArtifactCheck:
    errors: list[str] = []
    warnings: list[str] = []
    log_path = tex_path.with_suffix(".log")

    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        errors.append("PDF is missing or empty")
    if not log_path.exists():
        errors.append("XeLaTeX log is missing; artifact cannot be preflighted")
        log_text = ""
    else:
        log_text = log_path.read_text(encoding="utf-8", errors="replace")

    missing_count = log_text.count("Missing character:")
    if missing_count:
        errors.append(f"XeLaTeX reported {missing_count} missing character(s)")

    overfull_values = [float(match.group("points")) for match in _OVERFULL_RE.finditer(log_text)]
    max_overfull = max(overfull_values, default=0.0)
    severe = [value for value in overfull_values if value > max_allowed_overfull_pt]
    if severe:
        errors.append(
            f"severe overfull hbox: max {max(severe):.2f}pt > {max_allowed_overfull_pt:.2f}pt"
        )
    elif overfull_values:
        warnings.append(f"minor overfull hbox present: max {max_overfull:.2f}pt")

    page_match = _PAGE_RE.search(log_text)
    page_count = int(page_match.group("pages")) if page_match else None
    if pdf_path.exists() and pdf_path.stat().st_size > 0 and page_count is None:
        warnings.append("page count could not be read from XeLaTeX log")

    return ArtifactCheck(
        name=tex_path.stem,
        tex_path=str(tex_path),
        pdf_path=str(pdf_path),
        pdf_sha256=sha256_file(pdf_path) if pdf_path.exists() and pdf_path.stat().st_size else None,
        page_count=page_count,
        max_overfull_pt=max_overfull,
        missing_character_count=missing_count,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def build_artifact_manifest(
    *,
    root: Path,
    exam_id: str,
    exam_fingerprint: str,
    out_dir: Path,
    names: tuple[str, ...] = ("student", "teacher", "answer_sheet"),
) -> ArtifactManifest:
    checks: list[ArtifactCheck] = []
    for name in names:
        tex = out_dir / f"{name}.tex"
        pdf = out_dir / f"{name}.pdf"
        checks.append(preflight_pdf(tex, pdf))

    extras: dict[str, str] = {}
    for filename in REQUIRED_EXTRA_FILES:
        path = out_dir / filename
        if path.exists() and path.stat().st_size:
            extras[filename] = sha256_file(path)

    return ArtifactManifest(
        exam_id=exam_id,
        exam_fingerprint=exam_fingerprint,
        renderer_revision=renderer_revision(root),
        checks=tuple(checks),
        extra_files=extras,
    )


def write_artifact_manifest(manifest: ArtifactManifest, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest.model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path

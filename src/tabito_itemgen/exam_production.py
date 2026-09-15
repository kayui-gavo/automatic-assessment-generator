from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pydantic import ValidationError

from .artifact_preflight import (
    REQUIRED_EXTRA_FILES,
    ArtifactManifest,
    renderer_revision,
    sha256_file,
)
from .exam_models import (
    ExamHumanQA,
    ExamManifest,
    Q1Section,
    Q2OrderingTask,
    Q2Section,
    Q3Section,
    Q5Section,
    SECTION_SPECS,
    SectionRef,
)
from .exam_review_models import (
    SECTION_SPECIFIC_QA,
    ReviewExecution,
    SectionHumanQA,
    SectionReview,
)
from .exam_validation import ValidationResult, validate_exam, validate_section_file
from .io import dump_json, load_json
from .model_policy import (
    POLICY_VERSION,
    PREFERRED_MODEL,
    context_is_memory_isolated,
    execution_is_review_grade,
    reasoning_is_review_grade,
)
from .models import Item
from .production import parse_chat_json
from .section_io import load_section, save_section_draft, section_fingerprint, section_id


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class Readiness:
    subject_id: str
    fingerprint: str
    gates: tuple[Gate, ...]

    @property
    def ready(self) -> bool:
        return all(gate.passed for gate in self.gates)


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _exam_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")[:-3]


def exam_draft_dir(root: Path, exam_id: str) -> Path:
    return root / "exam_bank" / "draft" / exam_id


def exam_approved_dir(root: Path, exam_id: str) -> Path:
    return root / "exam_bank" / "approved" / exam_id


def exam_workspace_dir(root: Path, exam_id: str) -> Path:
    return root / "workspace" / "exams" / exam_id


def manifest_path(root: Path, exam_id: str, *, approved: bool = False) -> Path:
    base = exam_approved_dir(root, exam_id) if approved else exam_draft_dir(root, exam_id)
    return base / "exam.json"


def create_exam_project(
    root: Path,
    *,
    exam_family: str,
    title_ja: str | None = None,
    notes: str = "",
    q4_topic_request: str = "",
    q5_topic_request: str = "",
) -> tuple[ExamManifest, Path]:
    if exam_family not in {"main_2026", "makeup_2026"}:
        raise ValueError("exam_family must be main_2026 or makeup_2026")
    exam_id = f"TABITO-CN-EXAM-{_exam_stamp()}"
    refs: list[SectionRef] = []
    for section in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        score, start, end = SECTION_SPECS[section]
        refs.append(
            SectionRef(
                section=section,
                section_id=f"{exam_id}-{section}",
                expected_score=score,
                answer_start=start,
                answer_end=end,
            )
        )
    manifest = ExamManifest(
        exam_id=exam_id,
        exam_family=exam_family,
        title_ja=title_ja or f"旅人教育 共通テスト中国語 模試 {exam_id[-7:]}",
        notes=notes,
        q4_topic_request=q4_topic_request,
        q5_topic_request=q5_topic_request,
        sections=refs,
    )
    path = manifest_path(root, exam_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(path, manifest.model_dump())
    (path.parent / "sections").mkdir(parents=True, exist_ok=True)
    return manifest, path


def load_manifest(path: Path) -> ExamManifest:
    return ExamManifest.model_validate(load_json(path))


def _ref_for(manifest: ExamManifest, section: str) -> SectionRef:
    return next(ref for ref in manifest.sections if ref.section == section)


def _save_manifest(path: Path, manifest: ExamManifest) -> None:
    dump_json(path, manifest.model_dump())


def import_section_response(
    root: Path,
    exam_id: str,
    section_name: str,
    text: str,
) -> tuple[Path, ValidationResult]:
    path = manifest_path(root, exam_id)
    manifest = load_manifest(path)
    ref = _ref_for(manifest, section_name)
    data = parse_chat_json(text)
    if data.get("section") != section_name:
        raise ValueError(f"response section {data.get('section')!r} does not match {section_name}")
    incoming_id = data.get("item_id") if section_name == "Q4" else data.get("section_id")
    if incoming_id != ref.section_id:
        raise ValueError(f"response section id {incoming_id!r} does not match request {ref.section_id!r}")

    response_dir = exam_workspace_dir(root, exam_id) / "responses"
    response_dir.mkdir(parents=True, exist_ok=True)
    dump_json(response_dir / f"{section_name.lower()}.response.json", data)

    from pydantic import TypeAdapter

    from .exam_models import SectionData

    section = TypeAdapter(SectionData).validate_python(data)
    if isinstance(section, (Item, Q5Section)) and section.surface_family != manifest.exam_family:
        raise ValueError(
            f"{section_name} surface family {section.surface_family!r} does not match exam family {manifest.exam_family!r}"
        )
    section_path = save_section_draft(path.parent, section)
    result = validate_section_file(section_path)
    ref.path = str(section_path.relative_to(path.parent))
    ref.state = "draft"
    ref.fingerprint = section_fingerprint(load_section(section_path))
    manifest.workflow.state = "draft"
    _save_manifest(path, manifest)
    return section_path, result


def section_review_path(root: Path, exam_id: str, section: str) -> Path:
    return exam_workspace_dir(root, exam_id) / "reviews" / f"{section.lower()}.review.json"


def section_review_execution_path(root: Path, exam_id: str, section: str) -> Path:
    return exam_workspace_dir(root, exam_id) / "reviews" / f"{section.lower()}.review_execution.json"


def section_qa_path(root: Path, exam_id: str, section: str) -> Path:
    return exam_workspace_dir(root, exam_id) / "human_qa" / f"{section.lower()}.human_qa.json"


def exam_qa_path(root: Path, exam_id: str) -> Path:
    return exam_workspace_dir(root, exam_id) / "exam_qa.json"


def exam_qa_meta_path(root: Path, exam_id: str) -> Path:
    return exam_workspace_dir(root, exam_id) / "exam_qa.meta.json"


def exam_release_record_path(root: Path, exam_id: str) -> Path:
    return exam_workspace_dir(root, exam_id) / "release.json"


def exam_artifact_manifest_path(root: Path, exam_id: str) -> Path:
    return root / "output" / exam_id / "artifact_manifest.json"


def _section_file(root: Path, manifest: ExamManifest, section: str) -> Path:
    ref = _ref_for(manifest, section)
    if not ref.path:
        raise ValueError(f"{section} has not been generated")
    return manifest_path(root, manifest.exam_id).parent / ref.path


def section_author_answers(section) -> dict[str, list[int]]:
    if isinstance(section, Item):
        return {
            task.task_id: [slot.correct_option for slot in task.answer_slots]
            for task in section.tasks
        }
    if isinstance(section, Q1Section):
        return {task.task_id: [task.answer_slot.correct_option] for task in section.tasks}
    if isinstance(section, Q2Section):
        return {
            task.task_id: (
                [slot.correct_option for slot in task.answer_slots]
                if isinstance(task, Q2OrderingTask)
                else [task.answer_slot.correct_option]
            )
            for task in section.tasks
        }
    if isinstance(section, Q3Section):
        return {task.task_id: [task.answer_slot.correct_option] for task in section.tasks}
    if isinstance(section, Q5Section):
        return {
            task.task_id: [slot.correct_option for slot in task.answer_slots]
            for task in section.tasks
        }
    raise TypeError(f"unsupported section type {type(section)!r}")


def _answers_match(section, task_id: str, author: list[int], reviewer: list[int]) -> bool:
    """Respect the response semantics of each task when comparing a blind solve.

    Only true multi-select questions are set-valued. Ordering tasks and multi-slot
    questions encode different answer positions, so reversing their answers must fail.
    """

    if isinstance(section, (Item, Q5Section)):
        task = next(task for task in section.tasks if task.task_id == task_id)
        if task.response_mode == "multi_select":
            return sorted(reviewer) == sorted(author)
    return reviewer == author


def _review_errors(section, review: SectionReview) -> list[str]:
    errors: list[str] = []
    if review.section != section.section or review.section_id != section_id(section):
        errors.append("review section identity does not match candidate")
    if review.candidate_fingerprint != section_fingerprint(section):
        errors.append("review fingerprint does not match current candidate")
    if review.verdict != "pass":
        errors.append(f"review verdict is {review.verdict}, not pass")
    expected = section_author_answers(section)
    if set(review.independent_answers) != set(expected):
        errors.append("review task ids do not match candidate tasks")
    else:
        for task_id, author in expected.items():
            reviewer = review.independent_answers[task_id]
            if not _answers_match(section, task_id, author, reviewer):
                errors.append(f"{task_id}: reviewer answer {reviewer} != author key {author}")
    if any(issue.severity == "high" for issue in review.issues):
        errors.append("review contains high-severity issue")
    return errors


def _review_execution_errors(section, execution: ReviewExecution) -> list[str]:
    errors: list[str] = []
    if execution.section != section.section or execution.section_id != section_id(section):
        errors.append("review execution identity does not match candidate")
    if execution.candidate_fingerprint != section_fingerprint(section):
        errors.append("review execution record is stale")
    if execution.policy_version != POLICY_VERSION:
        errors.append(
            f"review execution policy {execution.policy_version!r} is not current {POLICY_VERSION!r}"
        )
    if not execution.fresh_chat_confirmed:
        errors.append("blind review was not confirmed as an independent context")
    if not context_is_memory_isolated(execution.context_mode):
        errors.append(
            f"blind review context mode {execution.context_mode!r} is not confirmed memory-isolated"
        )
    if execution.authoring_context_seen:
        errors.append("blind reviewer had access to authoring/revision context")
    if not reasoning_is_review_grade(execution.reasoning_level):
        errors.append(
            f"blind review reasoning level {execution.reasoning_level!r} is below production grade"
        )
    elif not execution_is_review_grade(execution.model_label, execution.reasoning_level):
        errors.append(
            "blind review model/reasoning combination is not allowed by current production policy: "
            f"{execution.model_label!r} / {execution.reasoning_level!r}"
        )
    return errors


def import_section_review(
    root: Path,
    exam_id: str,
    section_name: str,
    text: str,
    *,
    model_label: str = PREFERRED_MODEL,
    reasoning_level: str = "unknown",
    fresh_chat_confirmed: bool = False,
    context_mode: str = "unknown",
    authoring_context_seen: bool = False,
) -> Path:
    manifest = load_manifest(manifest_path(root, exam_id))
    section = load_section(_section_file(root, manifest, section_name))
    review = SectionReview.model_validate(parse_chat_json(text))
    if review.candidate_fingerprint != section_fingerprint(section):
        raise ValueError("review was produced for a different candidate version")

    path = section_review_path(root, exam_id, section_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(path, review.model_dump())

    execution = ReviewExecution(
        section=section_name,
        section_id=section_id(section),
        candidate_fingerprint=section_fingerprint(section),
        policy_version=POLICY_VERSION,
        model_label=model_label,
        reasoning_level=reasoning_level,
        fresh_chat_confirmed=fresh_chat_confirmed,
        context_mode=context_mode,
        authoring_context_seen=authoring_context_seen,
    )
    dump_json(section_review_execution_path(root, exam_id, section_name), execution.model_dump())

    errors = _review_errors(section, review) + _review_execution_errors(section, execution)
    ref = _ref_for(manifest, section_name)
    ref.state = "reviewed" if not errors else "draft"
    _save_manifest(manifest_path(root, exam_id), manifest)
    return path


def save_section_human_qa(
    root: Path,
    exam_id: str,
    section_name: str,
    qa: SectionHumanQA,
) -> Path:
    manifest = load_manifest(manifest_path(root, exam_id))
    section = load_section(_section_file(root, manifest, section_name))
    current = section_fingerprint(section)
    if qa.section != section_name or qa.section_id != section_id(section):
        raise ValueError("section Human QA identity does not match candidate")
    if qa.candidate_fingerprint != current:
        raise ValueError("section Human QA was completed for a different candidate version")

    if qa.disposition == "approve":
        review_path = section_review_path(root, exam_id, section_name)
        execution_path = section_review_execution_path(root, exam_id, section_name)
        review_errors: list[str] = []
        if not review_path.exists():
            review_errors.append("review JSON not saved")
        else:
            try:
                review = SectionReview.model_validate(load_json(review_path))
                review_errors.extend(_review_errors(section, review))
            except (ValidationError, ValueError, OSError) as exc:
                review_errors.append(str(exc))
        if not execution_path.exists():
            review_errors.append("blind review execution record not saved")
        else:
            try:
                execution = ReviewExecution.model_validate(load_json(execution_path))
                review_errors.extend(_review_execution_errors(section, execution))
            except (ValidationError, ValueError, OSError) as exc:
                review_errors.append(str(exc))
        if review_errors:
            raise ValueError(
                "Human QA approve requires a current passing Blind Review: "
                + "; ".join(review_errors)
            )

    path = section_qa_path(root, exam_id, section_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(path, qa.model_dump())
    return path


def _qa_errors(section, qa: SectionHumanQA) -> list[str]:
    errors: list[str] = []
    current = section_fingerprint(section)
    if qa.candidate_fingerprint != current:
        errors.append("Human QA is stale")
    if qa.disposition != "approve":
        errors.append(f"Human QA disposition is {qa.disposition}")
    failed_common = [name for name, value in qa.checks.model_dump().items() if not value]
    if failed_common:
        errors.append("Human QA common checks failed: " + ", ".join(failed_common))
    required_specific = SECTION_SPECIFIC_QA[section.section]
    failed_specific = [name for name in required_specific if not qa.section_specific_checks.get(name, False)]
    if failed_specific:
        errors.append("Human QA section checks failed: " + ", ".join(failed_specific))
    return errors


def section_release_readiness(root: Path, exam_id: str, section_name: str) -> Readiness:
    manifest = load_manifest(manifest_path(root, exam_id))
    section_path = _section_file(root, manifest, section_name)
    section = load_section(section_path)
    fingerprint = section_fingerprint(section)
    validation = validate_section_file(section_path)
    gates: list[Gate] = [
        Gate(
            "deterministic validation",
            validation.passed,
            "pass" if validation.passed else "; ".join(validation.errors),
        )
    ]

    review_path = section_review_path(root, exam_id, section_name)
    execution_path = section_review_execution_path(root, exam_id, section_name)
    if not review_path.exists():
        gates.append(Gate("blind review", False, "review JSON not saved"))
    else:
        try:
            review = SectionReview.model_validate(load_json(review_path))
            errors = _review_errors(section, review)
            if not execution_path.exists():
                errors.append("blind review execution record not saved")
            else:
                execution = ReviewExecution.model_validate(load_json(execution_path))
                errors.extend(_review_execution_errors(section, execution))
            gates.append(Gate("blind review", not errors, "pass" if not errors else "; ".join(errors)))
        except (ValidationError, ValueError) as exc:
            gates.append(Gate("blind review", False, str(exc)))

    qa_path = section_qa_path(root, exam_id, section_name)
    if not qa_path.exists():
        gates.append(Gate("human QA", False, "section Human QA not saved"))
    else:
        try:
            qa = SectionHumanQA.model_validate(load_json(qa_path))
            errors = _qa_errors(section, qa)
            gates.append(Gate("human QA", not errors, "pass" if not errors else "; ".join(errors)))
        except (ValidationError, ValueError) as exc:
            gates.append(Gate("human QA", False, str(exc)))

    return Readiness(section_id(section), fingerprint, tuple(gates))


def exam_fingerprint(root: Path, exam_id: str) -> str:
    path = manifest_path(root, exam_id)
    manifest = load_manifest(path)
    payload = manifest.model_dump()
    payload["workflow"].pop("state", None)
    for ref in payload["sections"]:
        ref.pop("state", None)
        ref.pop("fingerprint", None)
    section_hashes: dict[str, str | None] = {}
    for ref in manifest.sections:
        if ref.path and (path.parent / ref.path).exists():
            section_hashes[ref.section] = section_fingerprint(load_section(path.parent / ref.path))
        else:
            section_hashes[ref.section] = None
    encoded = json.dumps(
        {"manifest": payload, "section_fingerprints": section_hashes},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _artifact_gate(root: Path, exam_id: str) -> Gate:
    path = exam_artifact_manifest_path(root, exam_id)
    if not path.exists():
        return Gate("artifact preflight", False, "artifact_manifest.json not found; render with PDF preflight first")
    try:
        artifact = ArtifactManifest.model_validate(load_json(path))
    except (ValidationError, ValueError, OSError) as exc:
        return Gate("artifact preflight", False, str(exc))

    if artifact.exam_id != exam_id:
        return Gate("artifact preflight", False, "artifact manifest exam_id mismatch")
    current_fingerprint = exam_fingerprint(root, exam_id)
    if artifact.exam_fingerprint != current_fingerprint:
        return Gate("artifact preflight", False, "PDF artifacts are stale for the current exam content")

    current_renderer = renderer_revision(root)
    if current_renderer == "unknown":
        return Gate("artifact preflight", False, "current renderer revision could not be determined")
    if artifact.renderer_revision == "unknown":
        return Gate("artifact preflight", False, "artifact renderer revision is unknown")
    if artifact.renderer_revision != current_renderer:
        return Gate(
            "artifact preflight",
            False,
            "PDF artifacts are stale for the current renderer; regenerate and preflight again",
        )

    required = {"student", "teacher", "answer_sheet"}
    names = {check.name for check in artifact.checks}
    if names != required:
        return Gate("artifact preflight", False, f"artifact set must be exactly {sorted(required)}, got {sorted(names)}")

    missing_extra_records = [
        filename for filename in REQUIRED_EXTRA_FILES if filename not in artifact.extra_files
    ]
    if missing_extra_records:
        return Gate(
            "artifact preflight",
            False,
            "required artifact hashes missing from manifest: " + ", ".join(missing_extra_records),
        )

    if not artifact.passed:
        failed = [
            f"{check.name}: {'; '.join(check.errors)}"
            for check in artifact.checks
            if not check.passed
        ]
        return Gate("artifact preflight", False, " | ".join(failed))

    out_dir = root / "output" / exam_id
    for check in artifact.checks:
        pdf = out_dir / f"{check.name}.pdf"
        if not pdf.exists() or not check.pdf_sha256:
            return Gate("artifact preflight", False, f"{check.name}.pdf missing from output")
        if sha256_file(pdf) != check.pdf_sha256:
            return Gate("artifact preflight", False, f"{check.name}.pdf changed after preflight")

    for filename, expected_sha in artifact.extra_files.items():
        file_name = Path(filename)
        if file_name.is_absolute() or file_name.name != filename:
            return Gate("artifact preflight", False, f"invalid artifact filename {filename!r}")
        artifact_file = out_dir / filename
        if not artifact_file.exists() or not artifact_file.is_file():
            return Gate("artifact preflight", False, f"{filename} missing after preflight")
        if sha256_file(artifact_file) != expected_sha:
            return Gate("artifact preflight", False, f"{filename} changed after preflight")

    return Gate("artifact preflight", True, f"pass · renderer {artifact.renderer_revision[:12]}")


def save_exam_human_qa(root: Path, exam_id: str, qa: ExamHumanQA) -> Path:
    if qa.exam_id != exam_id:
        raise ValueError("exam Human QA exam_id does not match")

    artifact_gate = _artifact_gate(root, exam_id)
    if not artifact_gate.passed:
        raise ValueError("final Exam QA requires current preflighted PDFs: " + artifact_gate.detail)

    if qa.disposition == "approve":
        manifest = load_manifest(manifest_path(root, exam_id))
        validation = validate_exam(manifest_path(root, exam_id))
        prerequisite_errors: list[str] = []
        if not validation.passed:
            prerequisite_errors.append("exam validation failed: " + "; ".join(validation.errors))
        for ref in manifest.sections:
            if not ref.path:
                prerequisite_errors.append(f"{ref.section} has not been generated")
                continue
            readiness = section_release_readiness(root, exam_id, ref.section)
            if not readiness.ready:
                detail = " | ".join(
                    f"{gate.name}: {gate.detail}"
                    for gate in readiness.gates
                    if not gate.passed
                )
                prerequisite_errors.append(f"{ref.section} is not Ready: {detail}")
        if prerequisite_errors:
            raise ValueError(
                "Final Exam QA approve requires every section to be Ready: "
                + " | ".join(prerequisite_errors)
            )

    artifact_path = exam_artifact_manifest_path(root, exam_id)
    artifact = ArtifactManifest.model_validate(load_json(artifact_path))
    path = exam_qa_path(root, exam_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(path, qa.model_dump())
    dump_json(
        exam_qa_meta_path(root, exam_id),
        {
            "exam_id": exam_id,
            "exam_fingerprint": exam_fingerprint(root, exam_id),
            "artifact_manifest_sha256": sha256_file(artifact_path),
            "renderer_revision": artifact.renderer_revision,
            "saved_at": _now(),
        },
    )
    return path


def _exam_qa_gate(root: Path, exam_id: str) -> Gate:
    path = exam_qa_path(root, exam_id)
    meta = exam_qa_meta_path(root, exam_id)
    if not path.exists() or not meta.exists():
        return Gate("exam human QA", False, "exam Human QA not saved")
    try:
        qa = ExamHumanQA.model_validate(load_json(path))
        saved_meta = load_json(meta)
    except (ValidationError, ValueError, OSError) as exc:
        return Gate("exam human QA", False, str(exc))
    if saved_meta.get("exam_fingerprint") != exam_fingerprint(root, exam_id):
        return Gate("exam human QA", False, "exam changed after final Human QA")

    artifact_gate = _artifact_gate(root, exam_id)
    if not artifact_gate.passed:
        return Gate("exam human QA", False, "artifact changed after final Human QA: " + artifact_gate.detail)
    artifact_path = exam_artifact_manifest_path(root, exam_id)
    if saved_meta.get("artifact_manifest_sha256") != sha256_file(artifact_path):
        return Gate("exam human QA", False, "PDF artifact manifest changed after final Human QA")

    failed = [name for name, value in qa.checks.model_dump().items() if not value]
    if qa.disposition != "approve" or failed:
        detail = f"disposition={qa.disposition}"
        if failed:
            detail += " | failed checks: " + ", ".join(failed)
        return Gate("exam human QA", False, detail)
    return Gate("exam human QA", True, "pass")


def exam_release_readiness(root: Path, exam_id: str) -> Readiness:
    path = manifest_path(root, exam_id)
    validation = validate_exam(path)
    gates: list[Gate] = [
        Gate(
            "exam validation",
            validation.passed,
            "pass" if validation.passed else "; ".join(validation.errors),
        )
    ]
    manifest = load_manifest(path)
    for ref in manifest.sections:
        if not ref.path:
            gates.append(Gate(f"{ref.section} release", False, "section not generated"))
            continue
        readiness = section_release_readiness(root, exam_id, ref.section)
        detail = "pass" if readiness.ready else " | ".join(
            f"{gate.name}: {gate.detail}" for gate in readiness.gates if not gate.passed
        )
        gates.append(Gate(f"{ref.section} release", readiness.ready, detail))
    gates.append(_artifact_gate(root, exam_id))
    gates.append(_exam_qa_gate(root, exam_id))
    return Readiness(exam_id, exam_fingerprint(root, exam_id), tuple(gates))


def _review_execution_snapshot(root: Path, exam_id: str, manifest: ExamManifest) -> dict[str, dict]:
    snapshot: dict[str, dict] = {}
    for ref in manifest.sections:
        path = section_review_execution_path(root, exam_id, ref.section)
        if not path.exists():
            raise ValueError(f"missing review execution record for {ref.section}")
        execution = ReviewExecution.model_validate(load_json(path))
        snapshot[ref.section] = execution.model_dump()
    return snapshot


def approve_exam(root: Path, exam_id: str) -> tuple[Path, Readiness]:
    readiness = exam_release_readiness(root, exam_id)
    if not readiness.ready:
        failed = [f"{gate.name}: {gate.detail}" for gate in readiness.gates if not gate.passed]
        raise ValueError("exam release gates failed: " + " | ".join(failed))

    source = exam_draft_dir(root, exam_id)
    target = exam_approved_dir(root, exam_id)
    if target.exists():
        approved_manifest = target / "exam.json"
        if approved_manifest.exists():
            record = exam_release_record_path(root, exam_id)
            if record.exists() and load_json(record).get("exam_fingerprint") == readiness.fingerprint:
                return target, readiness
        raise ValueError("approved exam_id already exists with different or unverifiable content")

    artifact_path = exam_artifact_manifest_path(root, exam_id)
    artifact_snapshot = load_json(artifact_path)
    artifact_source_dir = root / "output" / exam_id
    draft_manifest = load_manifest(source / "exam.json")
    review_execution_snapshot = _review_execution_snapshot(root, exam_id, draft_manifest)

    shutil.copytree(source, target)
    shutil.copytree(artifact_source_dir, target / "artifacts")
    approved_manifest = load_manifest(target / "exam.json")
    approved_manifest.workflow.state = "approved"
    for ref in approved_manifest.sections:
        ref.state = "approved"
        if ref.path:
            section_path = target / ref.path
            section = load_section(section_path)
            section.workflow.state = "approved"
            dump_json(section_path, section.model_dump())
    dump_json(target / "exam.json", approved_manifest.model_dump())

    record = {
        "exam_id": exam_id,
        "exam_fingerprint": readiness.fingerprint,
        "approved_at": _now(),
        "approved_path": str(target.relative_to(root)),
        "model_policy_version": POLICY_VERSION,
        "section_review_execution": review_execution_snapshot,
        "artifact_manifest_sha256": sha256_file(artifact_path),
        "artifact_manifest": artifact_snapshot,
        "gates": [
            {"name": gate.name, "passed": gate.passed, "detail": gate.detail}
            for gate in readiness.gates
        ],
    }
    record_path = exam_release_record_path(root, exam_id)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(record_path, record)
    shutil.rmtree(source)
    return target, readiness

import shutil

import pytest

from tabito_itemgen.artifact_preflight import ArtifactManifest
from tabito_itemgen.exam_models import ExamHumanQA, ExamQAChecks
from tabito_itemgen.exam_production import (
    approve_exam,
    import_section_response,
    load_manifest,
    save_exam_human_qa,
)
from tabito_itemgen.io import load_json

from tests.artifact_factory import write_clean_artifacts
from tests.full_exam_factory import build_exam
from tests.test_exam_release import _complete_section_qa


def _approve_test_exam(root):
    manifest, _ = build_exam(root, "main_2026")
    for section in ("Q1", "Q2", "Q3", "Q4", "Q5"):
        _complete_section_qa(root, manifest.exam_id, section)
    write_clean_artifacts(root, manifest.exam_id)
    qa = ExamHumanQA(
        exam_id=manifest.exam_id,
        reviewer="Final QA",
        disposition="approve",
        checks=ExamQAChecks(**{name: True for name in ExamQAChecks.model_fields}),
    )
    save_exam_human_qa(root, manifest.exam_id, qa)
    target, _ = approve_exam(root, manifest.exam_id)
    return manifest, target


def test_approved_exam_cannot_be_reimported_through_draft_pipeline(tmp_path):
    manifest, target = _approve_test_exam(tmp_path)
    approved = load_manifest(target / "exam.json")
    q1 = next(ref for ref in approved.sections if ref.section == "Q1")
    section_path = target / q1.path
    original = section_path.read_bytes()

    with pytest.raises(FileNotFoundError):
        import_section_response(tmp_path, manifest.exam_id, "Q1", "{}")

    assert section_path.read_bytes() == original
    assert approved.workflow.state == "approved"


def test_approved_artifacts_are_detached_from_mutable_output(tmp_path):
    manifest, target = _approve_test_exam(tmp_path)
    approved_artifacts = target / "artifacts"
    approved_answer = approved_artifacts / "answer_key.json"
    approved_student = approved_artifacts / "student.pdf"
    answer_snapshot = approved_answer.read_bytes()
    student_snapshot = approved_student.read_bytes()

    output = tmp_path / "output" / manifest.exam_id
    (output / "answer_key.json").write_text('{"tampered": true}\n', encoding="utf-8")
    (output / "student.pdf").write_bytes(b"%PDF-1.4\nchanged temporary output\n")

    assert approved_answer.read_bytes() == answer_snapshot
    assert approved_student.read_bytes() == student_snapshot

    shutil.rmtree(output)
    historical = ArtifactManifest.model_validate(
        load_json(approved_artifacts / "artifact_manifest.json")
    )
    assert historical.passed
    assert historical.renderer_revision.startswith("renderer-sha256:")
    assert approved_answer.read_bytes() == answer_snapshot
    assert approved_student.read_bytes() == student_snapshot

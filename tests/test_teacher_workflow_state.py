from tabito_itemgen.exam_generate import create_section_revision_request
from tabito_itemgen.exam_production import (
    import_section_review,
    load_manifest,
    manifest_path,
    save_section_human_qa,
    section_author_answers,
)
from tabito_itemgen.exam_review_models import (
    SECTION_SPECIFIC_QA,
    SectionHumanQA,
    SectionQAChecks,
    SectionReview,
)
from tabito_itemgen.section_io import load_section, section_fingerprint
from tabito_itemgen.teacher_workflow_state import (
    revision_block_message,
    section_is_rejected,
    section_status,
)

from tests.full_exam_factory import ROOT, build_exam

ISOLATED = "non_personalized_temporary_chat"


def _section_context(root, exam_id, section_name):
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    path = manifest_path(root, exam_id).parent / ref.path
    section = load_section(path)
    return manifest, ref, path, section


def _review(root, exam_id, section_name, verdict="pass") -> SectionReview:
    manifest, ref, _, section = _section_context(root, exam_id, section_name)
    del manifest
    return SectionReview(
        section=section_name,
        section_id=ref.section_id,
        candidate_fingerprint=section_fingerprint(section),
        verdict=verdict,
        independent_answers=section_author_answers(section),
        issues=[],
        overall_comment_ja="test review",
    )


def _copy_revision_assets(root, section_name):
    (root / "prompts").mkdir(parents=True, exist_ok=True)
    (root / "blueprints").mkdir(parents=True, exist_ok=True)
    (root / "prompts" / "revise_section.md").write_text(
        (ROOT / "prompts" / "revise_section.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / "blueprints" / f"{section_name.lower()}_2026.yaml").write_text(
        (ROOT / "blueprints" / f"{section_name.lower()}_2026.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )


def test_bad_review_execution_routes_back_to_review_not_item_revision(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review(tmp_path, manifest.exam_id, "Q1", verdict="pass")
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q1",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=False,
        context_mode=ISOLATED,
    )

    current, ref, _, section = _section_context(tmp_path, manifest.exam_id, "Q1")
    assert section_status(tmp_path, current, manifest_path(tmp_path, manifest.exam_id), ref) == "blind_review"
    message = revision_block_message(tmp_path, current, ref, section)
    assert message is not None
    assert "重新独立审题" in message


def test_review_content_failure_routes_to_revision(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review(tmp_path, manifest.exam_id, "Q1", verdict="revise")
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q1",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED,
    )

    current, ref, _, section = _section_context(tmp_path, manifest.exam_id, "Q1")
    assert section_status(tmp_path, current, manifest_path(tmp_path, manifest.exam_id), ref) == "review_failed"
    assert not section_is_rejected(tmp_path, current, ref, section)
    assert revision_block_message(tmp_path, current, ref, section) is None


def test_review_reject_routes_to_regeneration_not_revision(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review(tmp_path, manifest.exam_id, "Q1", verdict="reject")
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q1",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED,
    )

    current, ref, _, section = _section_context(tmp_path, manifest.exam_id, "Q1")
    assert section_status(tmp_path, current, manifest_path(tmp_path, manifest.exam_id), ref) == "rejected"
    assert section_is_rejected(tmp_path, current, ref, section)
    assert "重新出题" in revision_block_message(tmp_path, current, ref, section)


def test_teacher_revision_note_is_included_in_revision_prompt(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review(tmp_path, manifest.exam_id, "Q1", verdict="pass")
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q1",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED,
    )

    current, ref, _, section = _section_context(tmp_path, manifest.exam_id, "Q1")
    fingerprint = section_fingerprint(section)
    qa = SectionHumanQA(
        section="Q1",
        section_id=ref.section_id,
        candidate_fingerprint=fingerprint,
        reviewer="QA",
        disposition="revise",
        checks=SectionQAChecks(**{name: True for name in SectionQAChecks.model_fields}),
        section_specific_checks={name: True for name in SECTION_SPECIFIC_QA["Q1"]},
        note="把第三个候选的措辞改得更自然，但不要降低辨音难度。",
    )
    save_section_human_qa(tmp_path, manifest.exam_id, "Q1", qa)

    assert section_status(tmp_path, current, manifest_path(tmp_path, manifest.exam_id), ref) == "review_failed"
    assert revision_block_message(tmp_path, current, ref, section) is None

    _copy_revision_assets(tmp_path, "Q1")
    request = create_section_revision_request(tmp_path, manifest.exam_id, "Q1")
    text = request.read_text(encoding="utf-8")
    assert "## Teacher QA" in text
    assert "把第三个候选的措辞改得更自然" in text


def test_teacher_reject_routes_to_regeneration(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    review = _review(tmp_path, manifest.exam_id, "Q1", verdict="pass")
    import_section_review(
        tmp_path,
        manifest.exam_id,
        "Q1",
        review.model_dump_json(),
        reasoning_level="high",
        fresh_chat_confirmed=True,
        context_mode=ISOLATED,
    )

    current, ref, _, section = _section_context(tmp_path, manifest.exam_id, "Q1")
    qa = SectionHumanQA(
        section="Q1",
        section_id=ref.section_id,
        candidate_fingerprint=section_fingerprint(section),
        reviewer="QA",
        disposition="reject",
        checks=SectionQAChecks(),
        section_specific_checks={},
        note="这一版不用。",
    )
    save_section_human_qa(tmp_path, manifest.exam_id, "Q1", qa)

    assert section_status(tmp_path, current, manifest_path(tmp_path, manifest.exam_id), ref) == "rejected"
    assert section_is_rejected(tmp_path, current, ref, section)
    assert "重新出题" in revision_block_message(tmp_path, current, ref, section)

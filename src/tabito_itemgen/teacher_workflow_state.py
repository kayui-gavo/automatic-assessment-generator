from __future__ import annotations

from pathlib import Path

from .exam_production import (
    section_qa_path,
    section_release_readiness,
    section_review_path,
)
from .exam_review_models import SectionHumanQA, SectionReview
from .exam_validation import validate_section_file
from .io import load_json
from .section_io import load_section, section_fingerprint

SECTION_NAV_LABELS = {
    "Q1": "发音・拼音",
    "Q2": "词语",
    "Q3": "表达",
    "Q4": "综合资料",
    "Q5": "长文阅读",
}


def _current_review(
    root: Path,
    exam_id: str,
    section_name: str,
    fingerprint: str,
) -> SectionReview | None:
    path = section_review_path(root, exam_id, section_name)
    if not path.exists():
        return None
    try:
        review = SectionReview.model_validate(load_json(path))
    except Exception:
        return None
    return review if review.candidate_fingerprint == fingerprint else None


def _current_qa(
    root: Path,
    exam_id: str,
    section_name: str,
    fingerprint: str,
) -> SectionHumanQA | None:
    path = section_qa_path(root, exam_id, section_name)
    if not path.exists():
        return None
    try:
        qa = SectionHumanQA.model_validate(load_json(path))
    except Exception:
        return None
    return qa if qa.candidate_fingerprint == fingerprint else None


def review_needs_revision(review: SectionReview, blind_detail: str) -> bool:
    """Tell content failure from review-execution failure."""

    if review.verdict == "revise":
        return True
    return (
        "review contains high-severity issue" in blind_detail
        or ": reviewer answer " in blind_detail
    )


def section_is_rejected(root: Path, manifest, ref, section) -> bool:
    fingerprint = section_fingerprint(section)
    qa = _current_qa(root, manifest.exam_id, ref.section, fingerprint)
    if qa and qa.disposition == "reject":
        return True
    review = _current_review(root, manifest.exam_id, ref.section, fingerprint)
    return bool(review and review.verdict == "reject")


def section_status(root: Path, manifest, exam_path: Path, ref) -> str:
    path = exam_path.parent / ref.path if ref.path else None
    if path is None or not path.exists():
        return "not_generated"
    if not validate_section_file(path).passed:
        return "needs_fix"
    if "approved" in exam_path.parts:
        return "approved"

    try:
        section = load_section(path)
        fingerprint = section_fingerprint(section)
        readiness = section_release_readiness(root, manifest.exam_id, ref.section)
    except Exception:
        return "draft"

    if readiness.ready:
        return "ready"

    blind = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
    if blind and blind.passed:
        qa = _current_qa(root, manifest.exam_id, ref.section, fingerprint)
        if qa and qa.disposition == "reject":
            return "rejected"
        if qa and qa.disposition == "revise":
            return "review_failed"
        return "teacher_qa"

    review = _current_review(root, manifest.exam_id, ref.section, fingerprint)
    if review is None:
        return "blind_review"
    if review.verdict == "reject":
        return "rejected"
    if blind and review_needs_revision(review, blind.detail):
        return "review_failed"

    # The candidate itself has no revision evidence. The failed gate came from
    # review execution / provenance, so route the teacher back to independent
    # review instead of telling them to rewrite a good item.
    return "blind_review"


def next_action_text(ref, status: str) -> str:
    section = f"{ref.section} {SECTION_NAV_LABELS[ref.section]}"
    if status == "not_generated":
        return f"打开 {section}，先生成题目。"
    if status == "needs_fix":
        return f"打开 {section} 的「返修」，先修正结构校验问题。"
    if status in {"draft", "blind_review"}:
        return f"打开 {section} 的「质量检查」，完成或重新进行独立审题。"
    if status == "review_failed":
        return f"打开 {section} 的「返修」，按当前审题或教师意见修改后重新独立审题。"
    if status == "rejected":
        return f"打开 {section} 的「返修」，保留本版记录并重新出题。"
    if status == "teacher_qa":
        return f"打开 {section} 的「质量检查」，完成教师确认。"
    return f"{section} 已就绪。"


def revision_block_message(root: Path, manifest, ref, section) -> str | None:
    """Return a teacher-facing reason when revision should not be generated."""

    fingerprint = section_fingerprint(section)
    qa = _current_qa(root, manifest.exam_id, ref.section, fingerprint)
    if qa and qa.disposition == "revise":
        return None
    if qa and qa.disposition == "reject":
        return "当前版本已标记为「不采用」。请重新出题，而不是继续返修这一版。"

    review = _current_review(root, manifest.exam_id, ref.section, fingerprint)
    if review is None:
        return None  # Let the existing UI explain missing/stale review files.
    if review.verdict == "reject":
        return "独立审题结论为「不采用」。请重新出题，而不是继续返修这一版。"

    try:
        readiness = section_release_readiness(root, manifest.exam_id, ref.section)
    except Exception:
        return None
    blind = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
    if blind is None:
        return None
    if review_needs_revision(review, blind.detail):
        return None
    if blind.passed:
        return "独立审题已经通过，教师也没有要求返修。当前版本不需要生成返修指令。"
    return (
        "当前失败来自独立审题的执行方式或记录，不是题目内容问题。"
        "请回到「质量检查」重新独立审题，不要改题。"
    )

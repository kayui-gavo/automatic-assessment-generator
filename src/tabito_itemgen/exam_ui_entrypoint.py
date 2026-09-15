from __future__ import annotations

import tabito_itemgen.exam_ui as exam_ui
from tabito_itemgen.exam_ui_style import APP_CSS
from tabito_itemgen.response_audit import import_section_response as audited_import_section_response
from tabito_itemgen.teacher_workflow_state import (
    next_action_text,
    revision_block_message,
    section_is_rejected,
    section_status,
)

# The entrypoint owns runtime presentation / teacher-routing policy while the
# large workbench module remains focused on rendering forms and actions.
exam_ui.APP_CSS = APP_CSS
exam_ui._section_status = section_status
exam_ui._next_action_text = next_action_text
# All teacher-facing section imports first pass identity/renderability checks and
# then preserve an immutable raw-response audit copy.
exam_ui.import_section_response = audited_import_section_response
# Teacher-facing states describe the next action, not internal pipeline jargon.
exam_ui.STATUS_COPY["review_failed"] = ("需要返修", "bad")
exam_ui.STATUS_COPY["rejected"] = ("不采用", "bad")

_original_save_exam_human_qa = exam_ui.save_exam_human_qa
_original_revision_import = exam_ui._render_revision_import
_original_section_workspace = exam_ui._render_section_workspace


def _guarded_save_exam_human_qa(root, exam_id, qa):
    """Do not let the UI say final QA is approved with unchecked requirements."""

    if qa.disposition == "approve":
        failed = [name for name, value in qa.checks.model_dump().items() if not value]
        if failed:
            labels = [exam_ui.EXAM_QA_LABELS.get(name, name) for name in failed]
            raise ValueError("整卷不能标记为「通过」。以下检查尚未确认：" + "；".join(labels))
    return _original_save_exam_human_qa(root, exam_id, qa)


exam_ui.save_exam_human_qa = _guarded_save_exam_human_qa


def _render_history_restore(root, manifest, ref) -> None:
    history_dir = (
        root
        / "exam_bank"
        / "draft"
        / manifest.exam_id
        / "history"
        / ref.section.lower()
    )
    if not history_dir.exists():
        return

    history_files = sorted(
        history_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not history_files:
        return

    with exam_ui.st.expander("历史版本 / 回退", expanded=False):
        exam_ui.st.caption(
            "每次导入新版本前，系统都会自动保留上一版。恢复历史版本也不会删除当前版本。"
        )
        for history_path in history_files[:8]:
            try:
                historical = exam_ui.load_section(history_path)
                fingerprint = exam_ui.section_fingerprint(historical)
            except Exception:
                continue

            label_col, action_col = exam_ui.st.columns([3, 1])
            label_col.caption(f"版本 {fingerprint[:10]}")
            if action_col.button(
                "恢复",
                key=f"restore-{manifest.exam_id}-{ref.section}-{fingerprint[:12]}",
                use_container_width=True,
            ):
                restored_path, result = exam_ui.import_section_response(
                    root,
                    manifest.exam_id,
                    ref.section,
                    history_path.read_text(encoding="utf-8"),
                )
                restored = exam_ui.load_section(restored_path)
                restored_fingerprint = exam_ui.section_fingerprint(restored)
                exam_ui.st.session_state[
                    exam_ui._section_view_key(
                        manifest.exam_id,
                        ref.section,
                        restored_fingerprint,
                    )
                ] = "质量检查" if result.passed else "返修"
                exam_ui._set_flash(
                    manifest.exam_id,
                    ref.section,
                    "success" if result.passed else "warning",
                    (
                        "已恢复历史版本。当前被替换的版本也已自动归档。"
                        if result.passed
                        else "已恢复历史版本，但该版本仍有结构问题，请先修正。"
                    ),
                )
                exam_ui.st.rerun()


def _guarded_revision_import(root, manifest, ref, section, path) -> None:
    _render_history_restore(root, manifest, ref)
    if section_is_rejected(root, manifest, ref, section):
        exam_ui.st.markdown("### 不采用")
        exam_ui.st.caption(
            "当前版本保留在历史记录中，但不再继续返修。请重新生成这一大题。"
        )
        exam_ui._render_generation_panel(root, manifest, ref)
        return

    message = revision_block_message(root, manifest, ref, section)
    if message:
        exam_ui.st.markdown("### 返修")
        exam_ui.st.info(message)
        return
    _original_revision_import(root, manifest, ref, section, path)


exam_ui._render_revision_import = _guarded_revision_import


def _routed_section_workspace(
    root,
    manifest,
    exam_path,
    ref,
    status,
    *,
    is_approved,
):
    # Rejected candidates should immediately land on the re-generation surface
    # even if the same fingerprint's radio state was previously "质量检查".
    if status == "rejected" and ref.path:
        path = exam_path.parent / ref.path
        if path.exists():
            try:
                section = exam_ui.load_section(path)
                fingerprint = exam_ui.section_fingerprint(section)
                view_key = exam_ui._section_view_key(
                    manifest.exam_id,
                    ref.section,
                    fingerprint,
                )
                exam_ui.st.session_state[view_key] = "返修"
            except Exception:
                pass
    return _original_section_workspace(
        root,
        manifest,
        exam_path,
        ref,
        status,
        is_approved=is_approved,
    )


exam_ui._render_section_workspace = _routed_section_workspace


def main() -> None:
    exam_ui.main()


if __name__ == "__main__":
    main()

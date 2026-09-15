from __future__ import annotations

import tabito_itemgen.exam_ui as exam_ui
from tabito_itemgen.exam_ui_style import APP_CSS
from tabito_itemgen.teacher_workflow_state import (
    next_action_text,
    revision_block_message,
    section_status,
)

# The entrypoint owns runtime presentation / teacher-routing policy while the
# large workbench module remains focused on rendering forms and actions.
exam_ui.APP_CSS = APP_CSS
exam_ui._section_status = section_status
exam_ui._next_action_text = next_action_text
# This state can come from either independent review or teacher QA, so avoid
# telling the teacher that the failure necessarily came from blind review.
exam_ui.STATUS_COPY["review_failed"] = ("需要返修", "bad")

_original_revision_import = exam_ui._render_revision_import


def _guarded_revision_import(root, manifest, ref, section, path) -> None:
    message = revision_block_message(root, manifest, ref, section)
    if message:
        exam_ui.st.markdown("### 返修")
        exam_ui.st.info(message)
        return
    _original_revision_import(root, manifest, ref, section, path)


exam_ui._render_revision_import = _guarded_revision_import


def main() -> None:
    exam_ui.main()


if __name__ == "__main__":
    main()

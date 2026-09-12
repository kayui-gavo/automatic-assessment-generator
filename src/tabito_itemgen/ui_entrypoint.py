from __future__ import annotations

import streamlit as st

import tabito_itemgen.ui_workbench_v2 as workbench
from tabito_itemgen.production import human_qa_binding_status
from tabito_itemgen.review_io import import_bound_review_response

# Keep the large presentation/workflow page stable while enforcing the production
# boundary here. This adapter can disappear once UI components are split into
# smaller public modules.
workbench.import_review_response = import_bound_review_response

_original_human_qa_form = workbench._human_qa_form
_original_load_human_qa = workbench.load_human_qa_if_present


def _version_safe_human_qa_form(root, item):
    existing = _original_load_human_qa(root, item.item_id)
    if existing is None:
        return _original_human_qa_form(root, item)

    bound, detail = human_qa_binding_status(root, item)
    if bound:
        return _original_human_qa_form(root, item)

    # A stale QA record is useful audit history, but its approval/check marks must
    # never be pre-filled for a modified candidate. Temporarily present an empty QA
    # form so the human reviewer must actively re-check the current version.
    st.warning(detail + "。旧 QA 记录保留，但本版 required checks 已重置。")
    previous_loader = workbench.load_human_qa_if_present
    workbench.load_human_qa_if_present = lambda *_args, **_kwargs: None
    try:
        return _original_human_qa_form(root, item)
    finally:
        workbench.load_human_qa_if_present = previous_loader


workbench._human_qa_form = _version_safe_human_qa_form


def main() -> None:
    workbench.main()


if __name__ == "__main__":
    main()

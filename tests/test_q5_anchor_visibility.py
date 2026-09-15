from __future__ import annotations

from tabito_itemgen.exam_validation import _validate_q5
from tests.full_exam_factory import q5


def test_q5_visible_anchor_markers_are_required():
    section = q5("Q5-VISIBLE", "main_2026")
    assert _validate_q5(section).errors == ()

    section.paragraphs[0].text_zh = section.paragraphs[0].text_zh.replace("〔下線部1〕", "")
    result = _validate_q5(section)
    assert any("marker_label" in error and "A1" in error for error in result.errors)

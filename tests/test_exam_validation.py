from tabito_itemgen.exam_validation import validate_exam

from tests.full_exam_factory import build_exam


def test_complete_main_exam_validates_1_to_50(tmp_path):
    _, manifest_path = build_exam(tmp_path, "main_2026")
    result = validate_exam(manifest_path)
    assert result.errors == ()


def test_complete_makeup_exam_validates_1_to_50(tmp_path):
    _, manifest_path = build_exam(tmp_path, "makeup_2026")
    result = validate_exam(manifest_path)
    assert result.errors == ()

from tabito_itemgen.answer_sheet import render_answer_sheet_tex

from tests.full_exam_factory import build_exam


def test_answer_sheet_covers_all_50_answers_and_scoring(tmp_path) -> None:
    manifest, _ = build_exam(tmp_path, "main_2026")
    outputs = render_answer_sheet_tex(tmp_path, manifest.exam_id, compile_pdf=False)

    tex = outputs["answer_sheet_tex"]
    scheme = outputs["scoring_scheme"]
    assert tex and tex.exists()
    assert scheme and scheme.exists()

    text = tex.read_text(encoding="utf-8")
    assert "解答用紙" in text
    assert "第1問" in text
    assert "第5問" in text
    assert "01" in text
    assert "50" in text

    scoring = scheme.read_text(encoding="utf-8")
    assert '"total_points": 200' in scoring
    assert '"group_id": "Q2-9-10"' in scoring
    assert '"award_mode": "all_or_nothing"' in scoring

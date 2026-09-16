from __future__ import annotations

from tabito_itemgen.exam_render import render_exam

from tests.full_exam_factory import build_exam


def test_full_exam_fixture_renders_complete_tex_and_answer_key(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    outputs = render_exam(tmp_path, manifest.exam_id, compile_pdf=False)

    student = outputs["student_tex"]
    teacher = outputs["teacher_tex"]
    answer_key = outputs["answer_key"]
    assert student and student.exists()
    assert teacher and teacher.exists()
    assert answer_key and answer_key.exists()

    student_text = student.read_text(encoding="utf-8")
    teacher_text = teacher.read_text(encoding="utf-8")
    for label in ("第1問", "第2問", "第3問", "第4問", "第5問"):
        assert label in student_text
    assert "【教師用】" not in student_text
    assert "【教師用】" in teacher_text
    assert "解答番号 1～50" in student_text

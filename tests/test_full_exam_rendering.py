import json

from tabito_itemgen.exam_render import render_exam

from tests.full_exam_factory import build_exam


def test_full_exam_renderer_writes_one_student_and_teacher_booklet(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    outputs = render_exam(tmp_path, manifest.exam_id, compile_pdf=False)
    student = outputs["student_tex"]
    teacher = outputs["teacher_tex"]
    assert student and student.exists()
    assert teacher and teacher.exists()

    text = student.read_text(encoding="utf-8")
    for number in range(1, 6):
        assert f"第{number}問" in text
    assert "試験時間 80分" in text
    assert "200点満点" in text
    assert "task_id" not in text
    assert "fingerprint" not in text
    assert "dependency_mode" not in text

    key = json.loads(outputs["answer_key"].read_text(encoding="utf-8"))
    assert list(map(int, key)) == list(range(1, 51))

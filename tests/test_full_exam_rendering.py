import json
from types import SimpleNamespace

from tabito_itemgen.exam_render import _ordering_frame, render_exam

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


def test_q2_ordering_frame_places_answer_numbers_in_requested_blank_positions():
    task = SimpleNamespace(
        task_id="Q2-C",
        sentence_frame_zh="这家店 ＿＿ ＿＿ ＿＿ ＿＿ 。",
        correct_sequence=[2, 1, 3, 4],
        answer_positions=[2, 4],
        answer_slots=[SimpleNamespace(answer_number=9), SimpleNamespace(answer_number=10)],
    )

    frame = _ordering_frame(task)
    box9 = r"\fbox{\rule{0pt}{1.45em}\hspace{0.42em}9\hspace{0.42em}}"
    box10 = r"\fbox{\rule{0pt}{1.45em}\hspace{0.42em}10\hspace{0.42em}}"

    assert frame.count(r"\underline{\hspace{4.0em}}") == 2
    assert frame.count(box9) == 1
    assert frame.count(box10) == 1
    assert frame.index(box9) < frame.index(box10)


def test_q2_ordering_frame_rejects_mismatched_blank_count():
    task = SimpleNamespace(
        task_id="Q2-C",
        sentence_frame_zh="＿＿ ＿＿ ＿＿ 。",
        correct_sequence=[1, 2, 3, 4],
        answer_positions=[2, 4],
        answer_slots=[SimpleNamespace(answer_number=9), SimpleNamespace(answer_number=10)],
    )

    try:
        _ordering_frame(task)
    except ValueError as exc:
        assert "sentence frame has 3 blanks" in str(exc)
    else:
        raise AssertionError("mismatched ordering frame must be rejected")

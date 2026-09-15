from __future__ import annotations

import shutil
from pathlib import Path

from tabito_itemgen.exam_render import render_exam

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "exam_001"
EXAM_ID = "TABITO-CN-PILOT-EXAM-001"


def _stage_pilot(root: Path) -> None:
    target = root / "exam_bank" / "draft" / EXAM_ID
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(PILOT, target)


def test_real_pilot_exam_001_renders_continuous_tex(tmp_path):
    _stage_pilot(tmp_path)
    outputs = render_exam(tmp_path, EXAM_ID, compile_pdf=False)

    student = outputs["student_tex"]
    teacher = outputs["teacher_tex"]
    answer_key = outputs["answer_key"]
    assert student and student.exists()
    assert teacher and teacher.exists()
    assert answer_key and answer_key.exists()

    student_text = student.read_text(encoding="utf-8")
    assert "地域の防災体験イベント" in student_text
    assert "古い商店街の共同配送と店主の変化" not in student_text  # topic metadata must not leak as a heading
    assert "共同配送" in student_text
    for label in ("第1問", "第2問", "第3問", "第4問", "第5問"):
        assert label in student_text

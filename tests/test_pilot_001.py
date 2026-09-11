from pathlib import Path

from tabito_itemgen.render import render_item_tex
from tabito_itemgen.validate import validate_item_file

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "pilots" / "q4_pilot_001_reuse_station_v2.json"


def test_pilot_001_passes_structural_validation():
    item, errors, warnings = validate_item_file(PILOT)
    assert item is not None
    assert errors == []
    assert sum(len(task.answer_slots) for task in item.tasks) == 16
    assert {task.subsection for task in item.tasks} == {"A", "B"}


def test_pilot_001_has_integrative_work_in_both_subsections():
    item, errors, _ = validate_item_file(PILOT)
    assert item is not None and errors == []
    integrative = {"within_compound", "cross_source", "scenario_plus_source"}
    for subsection in ("A", "B"):
        assert any(
            task.subsection == subsection and task.dependency_mode in integrative
            for task in item.tasks
        )


def test_pilot_001_avoids_decorative_visual_for_station_lookup():
    item, errors, _ = validate_item_file(PILOT)
    assert item is not None and errors == []
    station_material = next(m for m in item.materials if m.material_id == "B-M3")
    assert station_material.type == "table"


def test_pilot_001_renders_student_and_teacher_tex(tmp_path):
    item, errors, _ = validate_item_file(PILOT)
    assert item is not None and errors == []
    student = render_item_tex(item, tmp_path, teacher=False)
    teacher = render_item_tex(item, tmp_path, teacher=True)
    student_text = student.read_text(encoding="utf-8")
    teacher_text = teacher.read_text(encoding="utf-8")
    assert "第4問" in student_text
    assert "正答" not in student_text
    assert "正答" in teacher_text
    assert "情報依存" in teacher_text

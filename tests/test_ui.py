from pathlib import Path

from tabito_itemgen.ui_launcher import app_path


def test_ui_launcher_points_to_full_exam_workbench():
    path = app_path()
    assert path.name == "exam_ui.py"
    assert path.exists()


def test_full_exam_ui_source_compiles_and_keeps_legacy_q4_ui():
    exam_ui = app_path()
    source = exam_ui.read_text(encoding="utf-8")
    compile(source, str(exam_ui), "exec")
    assert "共通テスト中国語 模試制作 Workbench" in source
    assert "新建完整模試" in source
    assert "Q1–Q5 production status" in source
    assert "Final Exam QA" in source
    assert "Approve → 正式模試库" in source

    legacy = Path(__file__).resolve().parents[1] / "src" / "tabito_itemgen" / "ui_entrypoint.py"
    assert legacy.exists()
    compile(legacy.read_text(encoding="utf-8"), str(legacy), "exec")

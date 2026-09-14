from pathlib import Path

from tabito_itemgen.ui_launcher import app_path


def test_ui_launcher_points_to_full_exam_workbench():
    path = app_path()
    assert path.name == "exam_ui_entrypoint.py"
    assert path.exists()


def test_full_exam_ui_source_compiles_and_keeps_legacy_q4_ui():
    entrypoint = app_path()
    compile(entrypoint.read_text(encoding="utf-8"), str(entrypoint), "exec")
    assert "render_simple_section_preview" in entrypoint.read_text(encoding="utf-8")

    root = Path(__file__).resolve().parents[1]
    exam_ui = root / "src" / "tabito_itemgen" / "exam_ui.py"
    source = exam_ui.read_text(encoding="utf-8")
    compile(source, str(exam_ui), "exec")
    assert 'page_title="TABITO 中国語模試"' in source
    assert "新建完整模試" in source
    assert "Final Exam QA" in source
    assert "Approve → 正式模試库" in source
    assert "Blind Review" in source
    assert "Temporary Chat" in source
    assert "non_personalized_temporary_chat" in source
    assert "PREFERRED_MODEL" in source
    assert "MIN_REASONING_LEVEL" in source
    assert "TABITO EDUCATION · EXAM PRODUCTION" not in source
    assert "共通テスト中国語 模試制作 Workbench" not in source

    legacy = root / "src" / "tabito_itemgen" / "ui_entrypoint.py"
    assert legacy.exists()
    compile(legacy.read_text(encoding="utf-8"), str(legacy), "exec")

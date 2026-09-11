from pathlib import Path

from tabito_itemgen.ui_launcher import app_path


def test_ui_launcher_points_to_existing_app():
    path = app_path()
    assert path.name == "ui_app.py"
    assert path.exists()


def test_ui_app_source_compiles():
    path = app_path()
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    assert "题目预览" in source
    assert "Blind Review" in source
    assert "生成学生版 / 教师版" in source

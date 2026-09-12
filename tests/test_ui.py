from tabito_itemgen.ui_launcher import app_path


def test_ui_launcher_points_to_existing_app():
    path = app_path()
    assert path.name == "ui_workbench_v2.py"
    assert path.exists()


def test_ui_app_source_compiles():
    path = app_path()
    source = path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    assert "📄 试卷" in source
    assert "✨ 命题" in source
    assert "✅ 审题" in source
    assert "🚀 Release" in source
    assert "Blind Review" in source
    assert "Human QA" in source
    assert "content fingerprint" in source
    assert "Approve → 进入正式题库" in source

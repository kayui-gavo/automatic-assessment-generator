from pathlib import Path

from tabito_itemgen.ui_launcher import app_path


def test_ui_launcher_points_to_secure_entrypoint():
    path = app_path()
    assert path.name == "ui_entrypoint.py"
    assert path.exists()


def test_ui_entrypoint_and_workbench_source_compile():
    entrypoint = app_path()
    entry_source = entrypoint.read_text(encoding="utf-8")
    compile(entry_source, str(entrypoint), "exec")
    assert "import_bound_review_response" in entry_source
    assert "required checks 已重置" in entry_source

    workbench = Path(__file__).resolve().parents[1] / "src" / "tabito_itemgen" / "ui_workbench_v2.py"
    source = workbench.read_text(encoding="utf-8")
    compile(source, str(workbench), "exec")
    assert "📄 试卷" in source
    assert "✨ 命题" in source
    assert "✅ 审题" in source
    assert "🚀 Release" in source
    assert "Blind Review" in source
    assert "Human QA" in source
    assert "content fingerprint" in source
    assert "Approve → 进入正式题库" in source

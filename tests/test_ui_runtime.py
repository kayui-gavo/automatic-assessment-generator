from streamlit.testing.v1 import AppTest

from tabito_itemgen.ui_launcher import app_path


def test_default_workbench_session_renders_without_exception():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()

    assert not at.exception
    labels = [tab.label for tab in at.tabs]
    assert labels == ["📄 试卷预览", "✨ 新建命题", "✅ 质检 / 审题", "🛠 编辑 / 导出"]


def test_default_workbench_opens_active_pilot_not_rejected_history():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()

    assert not at.exception
    selectboxes = list(at.sidebar.selectbox)
    assert selectboxes
    assert "q4_pilot_002_library_study_main2026.json" in str(selectboxes[0].value)

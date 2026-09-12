from streamlit.testing.v1 import AppTest

from tabito_itemgen.ui_launcher import app_path


def test_default_workbench_session_renders_without_exception():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()

    assert not at.exception
    labels = [tab.label for tab in at.tabs]
    assert labels == ["📄 试卷", "✨ 命题", "✅ 审题", "🚀 Release", "🛠 编辑 / 导出"]


def test_default_workbench_opens_active_pilot_not_rejected_history():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()

    assert not at.exception
    selectboxes = list(at.sidebar.selectbox)
    assert selectboxes
    assert "q4_pilot_002_library_study_main2026.json" in str(selectboxes[0].value)


def test_workbench_exposes_version_safe_qa_and_release_workflow():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()

    assert not at.exception
    markdown_values = [element.value for element in at.markdown]
    subheaders = [element.value for element in at.subheader]
    combined = markdown_values + subheaders
    assert any("Human QA" in value for value in combined)
    assert any("Blind Review" in value for value in combined)
    assert any("content fingerprint" in value for value in combined)
    assert any("Release readiness" in value for value in combined)

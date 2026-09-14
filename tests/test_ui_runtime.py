from streamlit.testing.v1 import AppTest

from tabito_itemgen.ui_launcher import app_path


def test_default_full_exam_workbench_renders_without_exception():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()
    assert not at.exception


def test_default_home_is_simple_exam_creation_surface():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()
    assert not at.exception

    buttons = [button.label for button in at.button]
    assert "创建模试" in buttons

    markdown_values = [element.value for element in at.markdown]
    assert any("新建模试" in value for value in markdown_values)
    assert not any("模試制作 Workbench" in value for value in markdown_values)


def test_full_exam_workbench_exposes_main_and_makeup_blueprints():
    at = AppTest.from_file(str(app_path()), default_timeout=15)
    at.run()
    assert not at.exception

    radio_values = [option for radio in at.radio for option in radio.options]
    assert "2026 本試験型" in radio_values
    assert "2026 追試験型" in radio_values

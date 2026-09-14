from tabito_itemgen.exam_ui_style import APP_CSS


def test_teacher_workbench_avoids_saas_card_and_pill_chrome():
    lowered = APP_CSS.lower()

    assert ".pill" not in lowered
    assert "border-radius:999px" not in lowered
    assert "border-radius: 999px" not in lowered
    assert "tabito-kicker" not in lowered
    assert "box-shadow: 0 " not in lowered


def test_teacher_workbench_uses_flat_workflow_and_exam_surfaces():
    assert ".workflow-row" in APP_CSS
    assert ".next-action" in APP_CSS
    assert ".exam-header" in APP_CSS
    assert ".source-text" in APP_CSS
    assert "border-bottom: 1px solid var(--line)" in APP_CSS

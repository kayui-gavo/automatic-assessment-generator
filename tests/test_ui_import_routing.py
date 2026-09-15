import tabito_itemgen.exam_production as exam_production
import tabito_itemgen.exam_ui as exam_ui
import tabito_itemgen.exam_ui_entrypoint as exam_ui_entrypoint
import tabito_itemgen.response_audit as response_audit
from tabito_itemgen.ui_launcher import app_path


def test_teacher_runtime_routes_model_responses_through_audited_import():
    assert exam_ui.import_section_response is response_audit.import_section_response


def test_history_restore_keeps_provenance_neutral_core_import():
    assert exam_ui_entrypoint.core_import_section_response is exam_production.import_section_response


def test_launcher_uses_policy_entrypoint_not_raw_exam_ui():
    assert app_path().name == "exam_ui_entrypoint.py"

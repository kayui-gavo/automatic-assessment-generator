from pathlib import Path

from tabito_itemgen.validate import validate_item_file

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "pilots" / "q4_pilot_002_library_study_main2026.json"
MAKEUP_V1 = ROOT / "pilots" / "q4_pilot_003_stargazing_makeup2026.json"
MAKEUP_V2 = ROOT / "pilots" / "q4_pilot_003_stargazing_makeup2026_v2.json"


def test_main_pilot_passes_option_language_surface():
    item, errors, _ = validate_item_file(MAIN)
    assert item is not None
    assert not [error for error in errors if "options to match" in error]


def test_old_makeup_pilot_is_rejected_for_flattened_option_language():
    item, errors, _ = validate_item_file(MAKEUP_V1)
    assert item is not None
    language_errors = [error for error in errors if "options to match" in error]
    assert language_errors


def test_makeup_v2_passes_option_language_surface():
    item, errors, _ = validate_item_file(MAKEUP_V2)
    assert item is not None
    assert errors == []

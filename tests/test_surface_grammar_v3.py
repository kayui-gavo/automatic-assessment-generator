import json
from pathlib import Path

from tabito_itemgen.validate import validate_item_file

ROOT = Path(__file__).resolve().parents[1]
FAILED_PILOT = ROOT / "pilots" / "q4_pilot_001_reuse_station_v2.json"


def test_legacy_pilot_fails_when_judged_as_v3_main_family(tmp_path):
    data = json.loads(FAILED_PILOT.read_text(encoding="utf-8"))
    data["workflow"]["blueprint_version"] = "R8-2026-main-tsui-v3"
    data["surface_family"] = "main_2026"
    path = tmp_path / "pilot_as_v3.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    item, errors, _ = validate_item_file(path)
    assert item is not None
    assert any("task-slot grouping mismatch" in error for error in errors)


def test_v3_full_item_without_surface_family_is_rejected(tmp_path):
    data = json.loads(FAILED_PILOT.read_text(encoding="utf-8"))
    data["workflow"]["blueprint_version"] = "R8-2026-main-tsui-v3"
    data.pop("surface_family", None)
    path = tmp_path / "missing_family.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    item, errors, _ = validate_item_file(path)
    assert item is not None
    assert any("requires surface_family" in error for error in errors)


def test_generation_prompt_explicitly_preserves_surface_grammar():
    prompt = (ROOT / "prompts" / "generate_q4.md").read_text(encoding="utf-8")
    profile = (ROOT / "blueprints" / "q4_2026_generation_profile.yaml").read_text(encoding="utf-8")
    assert "main_2026" in prompt and "makeup_2026" in prompt
    assert "21・22" in prompt and "27・28" in prompt
    assert "shared_A_surface_grammar" in profile

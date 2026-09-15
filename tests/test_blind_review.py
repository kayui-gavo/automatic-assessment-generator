import json
from pathlib import Path

from tabito_itemgen.blind_surface import blind_section_dict
from tabito_itemgen.exam_production import load_manifest, manifest_path
from tabito_itemgen.generate_request import _blind_item_dict
from tabito_itemgen.models import Item
from tabito_itemgen.section_io import load_section

from tests.full_exam_factory import build_exam

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "q4_example_response.json"
PILOT = ROOT / "pilots" / "q4_pilot_002_library_study_main2026.json"


def test_blind_packet_removes_answer_key_rationales_and_authoring_metadata():
    item = Item.model_validate(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    blind = _blind_item_dict(item)

    for key in (
        "quality_notes",
        "workflow",
        "scenario_summary_ja",
        "difficulty",
        "topic",
        "surface_family",
        "schema_version",
        "item_id",
        "title_ja",
        "scope",
        "domain",
    ):
        assert key not in blind

    for material in blind["materials"]:
        assert "bundle_id" not in material

    for task in blind["tasks"]:
        assert "dependency_mode" not in task
        assert "evidence" not in task
        assert "operations" not in task
        assert "rationale_ja" not in task
        assert "distractor_rationales_ja" not in task
        assert "slot_distractor_rationales_ja" not in task
        assert all("correct_option" not in slot for slot in task["answer_slots"])
        assert all("slot_id" not in slot for slot in task["answer_slots"])


def test_blind_packet_hides_first_class_surface_family_but_keeps_visible_intro():
    data = json.loads(PILOT.read_text(encoding="utf-8"))
    data["subsection_intros_ja"] = {
        "A": "高校生が図書館の学習スペースについて調べている。",
        "B": "その後、実際に利用する場面について考える。",
    }
    item = Item.model_validate(data)
    assert item.surface_family == "main_2026"

    blind = _blind_item_dict(item)
    assert "surface_family" not in blind
    assert blind["subsection_intros_ja"]["A"].startswith("高校生が")
    assert blind["subsection_intros_ja"]["B"].startswith("その後")


def _section(root: Path, exam_id: str, section_name: str):
    manifest = load_manifest(manifest_path(root, exam_id))
    ref = next(ref for ref in manifest.sections if ref.section == section_name)
    return load_section(manifest_path(root, exam_id).parent / ref.path)


def test_q1_blind_surface_hides_internal_pinyin_and_schema_but_keeps_dialogue_pinyin(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    q1 = _section(tmp_path, manifest.exam_id, "Q1")
    blind = blind_section_dict(q1)

    assert "schema_version" not in blind
    assert "section_id" not in blind
    assert "title_ja" not in blind

    phonetic_tasks = [task for task in blind["tasks"] if "headword" in task]
    dialogue_tasks = [task for task in blind["tasks"] if "lines" in task]
    assert phonetic_tasks
    assert dialogue_tasks

    for task in phonetic_tasks:
        assert "task_type" not in task
        assert "order" not in task
        assert "target" not in task
        assert "pinyin" not in task["headword"]
        assert "label" not in task["headword"]
        assert set(task["headword"]) == {"hanzi", "target_index"}
        assert all("pinyin" not in candidate for candidate in task["candidates"])
        assert "slot_id" not in task["answer_slot"]

    for task in dialogue_tasks:
        assert "task_type" not in task
        assert "order" not in task
        assert all(line.get("pinyin") for line in task["lines"])
        assert "slot_id" not in task["answer_slot"]


def test_q4_blind_surface_hides_evidence_and_operation_taxonomy(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    q4 = _section(tmp_path, manifest.exam_id, "Q4")
    blind = blind_section_dict(q4)

    for key in ("difficulty", "schema_version", "item_id", "title_ja", "scope", "domain"):
        assert key not in blind
    for task in blind["tasks"]:
        assert "evidence" not in task
        assert "dependency_mode" not in task
        assert "operations" not in task
        assert "rationale_ja" not in task
        assert all("slot_id" not in slot for slot in task["answer_slots"])


def test_q5_blind_surface_removes_prelinks_but_preserves_visible_underline(tmp_path):
    manifest, _ = build_exam(tmp_path, "main_2026")
    q5 = _section(tmp_path, manifest.exam_id, "Q5")

    # source_excerpt is not an answer-side evidence pointer here: the renderer uses
    # it to identify the span visibly underlined after 〔下線部1〕 in the booklet.
    q5.anchors[0].source_excerpt = "她觉得这种做法很有意思。"
    blind = blind_section_dict(q5)

    assert "schema_version" not in blind
    assert "section_id" not in blind
    assert "title_ja" not in blind
    for task in blind["tasks"]:
        assert "anchor_refs" not in task
        assert "operation" not in task
        assert "rationale_ja" not in task
        assert all("slot_id" not in slot for slot in task["answer_slots"])
    assert blind["anchors"][0]["source_excerpt"] == "她觉得这种做法很有意思。"

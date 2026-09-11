import json
from pathlib import Path

from tabito_itemgen.generate_request import _blind_item_dict
from tabito_itemgen.models import Item

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "q4_example_response.json"


def test_blind_packet_removes_answer_key_and_rationales():
    item = Item.model_validate(json.loads(EXAMPLE.read_text(encoding="utf-8")))
    blind = _blind_item_dict(item)
    assert "quality_notes" not in blind
    for task in blind["tasks"]:
        assert "evidence" not in task
        assert "rationale_ja" not in task
        assert "distractor_rationales_ja" not in task
        assert "slot_distractor_rationales_ja" not in task
        assert all("correct_option" not in slot for slot in task["answer_slots"])

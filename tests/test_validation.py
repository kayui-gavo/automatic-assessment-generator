import json
from pathlib import Path

from tabito_itemgen.validate import validate_item_file
from test_models import sample_item


def test_q4_has_cross_material(tmp_path: Path):
    path = tmp_path / "item.json"
    path.write_text(json.dumps(sample_item(), ensure_ascii=False), encoding="utf-8")
    item, errors, warnings = validate_item_file(path)
    assert item is not None
    assert not errors

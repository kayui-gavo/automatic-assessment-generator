from pathlib import Path

from pydantic import TypeAdapter

from tabito_itemgen.models import Material
from tabito_itemgen.render import _material_block


def _material(data):
    return TypeAdapter(Material).validate_python(data)


def test_social_feed_renders_posts_without_internal_bundle_label():
    material = _material(
        {
            "type": "social_feed",
            "material_id": "B-M1",
            "subsection": "B",
            "order": 1,
            "bundle_id": "INTERNAL-BUNDLE",
            "title": "運行情報",
            "posts": [
                {"date_label": "9月12日", "author": "運営", "body": "午後は混雑します。"},
                {"date_label": "9月13日", "author": "運営", "body": "雨天時は時刻が変わります。"},
            ],
        }
    )
    tex = _material_block(material)
    assert "運行情報" in tex
    assert "9月12日" in tex
    assert "INTERNAL-BUNDLE" not in tex
    assert "bundle:" not in tex


def test_schematic_map_renders_nodes_edges_and_labels():
    material = _material(
        {
            "type": "schematic_map",
            "material_id": "B-M2",
            "subsection": "B",
            "order": 2,
            "title": "会場略図",
            "nodes": [
                {"node_id": "A", "label": "駅", "x": 0, "y": 0},
                {"node_id": "B", "label": "会場", "x": 5, "y": 0},
            ],
            "edges": [{"source": "A", "target": "B", "label": "徒歩10分"}],
        }
    )
    tex = _material_block(material)
    assert "会場略図" in tex
    assert "徒歩10分" in tex
    assert "schematicnode" in tex


def test_annotated_diagram_uses_directed_edge():
    material = _material(
        {
            "type": "annotated_diagram",
            "material_id": "A-M3",
            "subsection": "A",
            "order": 3,
            "nodes": [
                {"node_id": "L1", "label": "入力"},
                {"node_id": "L2", "label": "処理"},
            ],
            "edges": [{"source": "L1", "target": "L2", "label": "自動"}],
            "annotations": ["図は模式図である。"],
        }
    )
    tex = _material_block(material)
    assert "->,>=stealth" in tex
    assert "図は模式図である" in tex

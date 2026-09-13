from __future__ import annotations

from tabito_itemgen.models import ChartMaterial, ChartSeries
from tabito_itemgen.render import _chart_material


def _chart(kind: str) -> ChartMaterial:
    return ChartMaterial(
        type="chart",
        material_id="TEST-CHART",
        subsection="A",
        order=1,
        title="测试图表",
        chart_kind=kind,
        categories=["项目 A", "项目,B"],
        series=[ChartSeries(name="人数", values=[12, 18])],
        y_label="人",
        footnotes=[],
    )


def test_vertical_chart_uses_numeric_coordinates_and_braced_tick_labels():
    tex = _chart_material(_chart("bar"))

    assert "symbolic x coords" not in tex
    assert "coordinates {(0,12.0) (1,18.0)}" in tex
    assert "xtick={0,1}" in tex
    assert "xticklabels={{项目 A},{项目,B}}" in tex
    assert r"font=\small" in tex
    assert r"font=\\small" not in tex


def test_horizontal_chart_uses_numeric_coordinates_and_braced_tick_labels():
    tex = _chart_material(_chart("horizontal_bar"))

    assert "symbolic y coords" not in tex
    assert "coordinates {(12.0,0) (18.0,1)}" in tex
    assert "ytick={0,1}" in tex
    assert "yticklabels={{项目 A},{项目,B}}" in tex
    assert r"font=\small" in tex
    assert r"font=\\small" not in tex

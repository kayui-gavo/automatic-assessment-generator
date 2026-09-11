from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from tabito_itemgen.generate_request import (
    create_q4_request,
    create_review_request,
    create_revision_request,
)
from tabito_itemgen.models import (
    ChartMaterial,
    FlowchartMaterial,
    Item,
    Review,
    SchematicMaterial,
    SocialFeedMaterial,
    TableMaterial,
    TextMaterial,
)
from tabito_itemgen.paths import find_project_root
from tabito_itemgen.presentation import (
    FAMILY_LABELS,
    FAMILY_SUMMARIES,
    answer_numbers,
    owner_task_for_order,
    question_number,
    slot_group_summary,
    subsection_intro,
    subquestion_index,
    task_groups,
    tasks_for_subsection,
    timeline,
)
from tabito_itemgen.render import compile_xelatex, render_item_tex
from tabito_itemgen.validate import (
    check_bank_similarity,
    compare_review,
    validate_item_file,
)

OPTION_MARKS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]


APP_CSS = """
<style>
:root {
  --ink: #172433;
  --muted: #66717f;
  --navy: #18324e;
  --paper: #fffefa;
  --canvas: #f5f3ed;
  --line: #d9d6cc;
  --soft: #ece9df;
  --gold: #8a7345;
  --ok: #2f684f;
  --warn: #8a5c1c;
  --bad: #9a3f3f;
}
.stApp { background: var(--canvas); color: var(--ink); }
.block-container { max-width: 1380px; padding-top: 1.6rem; padding-bottom: 3rem; }
[data-testid="stSidebar"] { background: #eeece5; border-right: 1px solid #ddd9ce; }
[data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }
#MainMenu, footer { visibility: hidden; }
h1, h2, h3 { color: var(--navy); letter-spacing: -.015em; }
.tabito-kicker { letter-spacing: .12em; color: var(--gold); font-size: .76rem; font-weight: 800; }
.tabito-title { font-size: 2rem; line-height: 1.15; font-weight: 760; color: var(--navy); margin-top: .22rem; }
.tabito-sub { color: var(--muted); margin-top: .35rem; font-size: .94rem; }
.status-row { display:flex; flex-wrap:wrap; gap:.45rem; margin:.85rem 0 .2rem 0; }
.pill { display:inline-block; border:1px solid #d5d2c9; background:#fffdf7; color:#46515e; border-radius:999px; padding:.24rem .62rem; font-size:.78rem; }
.pill.ok { border-color:#b8d1c4; color:var(--ok); background:#f2f8f4; }
.pill.warn { border-color:#ddc9a8; color:var(--warn); background:#fff9ee; }
.pill.bad { border-color:#debcbc; color:var(--bad); background:#fff5f5; }
.paper-note { color:#7a746a; font-size:.82rem; margin:.1rem 0 .75rem 0; }
.exam-header { font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; color:#111; }
.exam-subject { font-size:.93rem; font-weight:700; margin-bottom:.6rem; }
.exam-title { font-size:1.24rem; line-height:1.7; }
.exam-rule { border-top:1.2px solid #202020; margin:.55rem 0 1rem 0; }
.exam-section { font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; font-size:1.14rem; font-weight:700; color:#111; margin:1.2rem 0 .25rem 0; }
.exam-intro { font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; color:#222; line-height:1.9; margin:.15rem 0 .7rem 0; }
.exam-question { font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; font-size:1.02rem; font-weight:700; color:#111; margin:1.05rem 0 .45rem 0; }
.exam-subq-label { font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; font-weight:700; color:#111; margin:.65rem 0 .15rem 0; }
.exam-prompt { font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; color:#151515; line-height:1.9; margin:.6rem 0 .42rem 0; }
.answer-badge { display:inline-block; border:1px solid #161616; min-width:2.15rem; padding:.02rem .32rem; margin-left:.22rem; text-align:center; font-family:Georgia,serif; font-weight:700; background:#fff; }
.source { margin:.65rem 0 .85rem 0; color:#111; }
.source-title { font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; font-weight:700; margin-bottom:.28rem; }
.source-text { font-family: 'Songti SC','STSong','Noto Serif CJK SC','Yu Mincho',serif; font-size:.98rem; line-height:1.92; white-space:normal; }
.source-note { color:#646464; font-size:.79rem; line-height:1.6; margin-top:.28rem; }
.glossary { margin-top:.38rem; padding-top:.3rem; border-top:1px dotted #aaa; color:#555; font-size:.78rem; }
.exam-table { width:100%; border-collapse:collapse; margin:.55rem 0 .35rem 0; font-size:.9rem; background:#fff; }
.exam-table th, .exam-table td { border:1px solid #777; padding:.42rem .5rem; text-align:center; vertical-align:middle; }
.exam-table th { background:#f2f1ed; font-weight:700; }
.social-post { border:1px solid #9b9b9b; padding:.6rem .72rem; margin:.42rem 0; background:#fff; }
.social-meta { font-size:.75rem; color:#666; margin-bottom:.24rem; }
.option-list { margin:.25rem 0 .8rem 0; }
.option-row { display:grid; grid-template-columns:2rem minmax(0,1fr); gap:.22rem; padding:.18rem 0; color:#151515; line-height:1.72; font-family: Georgia, 'Yu Mincho', 'Hiragino Mincho ProN', serif; }
.option-mark { font-weight:700; }
.teacher-key { width:100%; border-collapse:collapse; font-size:.9rem; }
.teacher-key th, .teacher-key td { border-bottom:1px solid #ddd8cc; padding:.42rem .5rem; text-align:left; }
.teacher-key th { color:#5f6872; font-size:.78rem; text-transform:uppercase; letter-spacing:.04em; }
.gate-box { border:1px solid #d9d5ca; border-radius:8px; padding:.7rem .85rem; background:#fffdf8; margin:.35rem 0; }
.small-muted { color:var(--muted); font-size:.82rem; }
div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--paper); border-color:#d8d4c8; border-radius:4px; }
button[kind="primary"] { border-radius:6px; }
[data-baseweb="tab-list"] { gap:.25rem; }
</style>
"""


def _root() -> Path:
    try:
        return find_project_root()
    except RuntimeError:
        return Path.cwd()


def _item_status(path: Path) -> str:
    name = path.name
    if name.startswith("q4_pilot_001_"):
        return "rejected"
    if name == "q4_pilot_003_stargazing_makeup2026.json":
        return "superseded"
    if name in {
        "q4_pilot_002_library_study_main2026.json",
        "q4_pilot_003_stargazing_makeup2026_v2.json",
    }:
        return "active"
    if "approved" in path.parts:
        return "approved"
    if "draft" in path.parts:
        return "draft"
    if "examples" in path.parts:
        return "fixture"
    return "pilot"


def _discover_items(root: Path, show_history: bool) -> dict[str, Path]:
    candidates: list[tuple[int, str, Path]] = []
    directories = [
        root / "pilots",
        root / "item_bank" / "approved",
        root / "item_bank" / "draft",
        root / "examples",
    ]
    rank = {"active": 0, "approved": 1, "draft": 2, "pilot": 3, "fixture": 4, "superseded": 5, "rejected": 6}
    label = {
        "active": "Active pilot",
        "approved": "Approved",
        "draft": "Draft",
        "pilot": "Pilot",
        "fixture": "Fixture",
        "superseded": "Superseded",
        "rejected": "Rejected",
    }
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            status = _item_status(path)
            if not show_history and status in {"rejected", "superseded", "fixture"}:
                continue
            candidates.append((rank[status], f"{label[status]} · {path.name}", path))
    return {display: path for _, display, path in sorted(candidates, key=lambda row: (row[0], row[1]))}


def _parse_item(text: str) -> tuple[Item | None, str | None]:
    try:
        return Item.model_validate(json.loads(text)), None
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        return None, str(exc)


def _write_ui_temp(root: Path, text: str, name: str = "current.json") -> Path:
    path = root / "workspace" / "ui_temp" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _validation_result(root: Path, text: str):
    temp = _write_ui_temp(root, text)
    return validate_item_file(temp)


def _escape_lines(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")


def _notes_html(notes: list[str]) -> str:
    if not notes:
        return ""
    return "".join(f'<div class="source-note">{html.escape(note)}</div>' for note in notes)


def _glosses_html(glosses: dict[str, str]) -> str:
    if not glosses:
        return ""
    body = "　".join(
        f"*{html.escape(word)}：{html.escape(gloss)}" for word, gloss in glosses.items()
    )
    return f'<div class="glossary">{body}</div>'


def _render_table(material: TableMaterial) -> None:
    header = "".join(f"<th>{html.escape(column)}</th>" for column in material.columns)
    rows = "".join(
        "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
        for row in material.rows
    )
    st.markdown(
        f'<div class="source"><div class="source-title">{html.escape(material.title or "")}</div>'
        f'<table class="exam-table"><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>'
        f'{_notes_html(material.footnotes)}</div>',
        unsafe_allow_html=True,
    )


def _chart_spec(material: ChartMaterial) -> dict:
    values = []
    for series in material.series:
        for category, value in zip(material.categories, series.values):
            values.append({"category": category, "value": value, "series": series.name})

    grayscale = ["#27313b", "#7b858e", "#b7bcc1", "#d7dadd"]
    base = {
        "data": {"values": values},
        "config": {
            "view": {"stroke": None},
            "axis": {
                "labelColor": "#30353a",
                "titleColor": "#30353a",
                "gridColor": "#e8e6e0",
                "domainColor": "#777",
                "tickColor": "#999",
                "labelFontSize": 12,
                "titleFontSize": 12,
            },
            "legend": {"labelColor": "#30353a", "title": None},
        },
    }
    color = {
        "field": "series",
        "type": "nominal",
        "scale": {"range": grayscale[: max(1, len(material.series))]},
        "legend": None if len(material.series) == 1 else {"orient": "bottom"},
    }
    if material.chart_kind == "horizontal_bar":
        base.update(
            {
                "mark": {"type": "bar"},
                "encoding": {
                    "y": {"field": "category", "type": "nominal", "sort": material.categories, "title": None},
                    "x": {"field": "value", "type": "quantitative", "title": material.y_label or None},
                    "color": color,
                    "yOffset": {"field": "series"},
                },
            }
        )
    elif material.chart_kind == "line":
        base.update(
            {
                "mark": {"type": "line", "point": True, "strokeWidth": 2},
                "encoding": {
                    "x": {"field": "category", "type": "ordinal", "sort": material.categories, "title": None},
                    "y": {"field": "value", "type": "quantitative", "title": material.y_label or None},
                    "color": color,
                },
            }
        )
    else:
        encoding = {
            "x": {"field": "category", "type": "nominal", "sort": material.categories, "title": None},
            "y": {
                "field": "value",
                "type": "quantitative",
                "title": material.y_label or None,
                "stack": "zero" if material.chart_kind == "stacked_bar" else None,
            },
            "color": color,
        }
        if material.chart_kind == "bar" and len(material.series) > 1:
            encoding["xOffset"] = {"field": "series"}
        base.update({"mark": {"type": "bar"}, "encoding": encoding})
    return base


def _render_graph(material: FlowchartMaterial | SchematicMaterial) -> None:
    lines = [
        "digraph G {",
        'graph [bgcolor="transparent", pad="0.2", nodesep="0.45", ranksep="0.55"];',
        'rankdir="LR";',
        'node [shape=box, style="rounded", fontname="Helvetica", fontsize=11, color="#535b63"];',
        'edge [color="#69717a", fontname="Helvetica", fontsize=9];',
    ]
    for node in material.nodes:
        label = node.label.replace('"', "'")
        note = getattr(node, "note", None)
        if note:
            label = f"{label}\\n{str(note).replace(chr(34), chr(39))}"
        lines.append(f'"{node.node_id}" [label="{label}"];')
    for edge in material.edges:
        attrs = []
        if edge.label:
            attrs.append(f'label="{edge.label.replace(chr(34), chr(39))}"')
        if getattr(edge, "dashed", False):
            attrs.append('style="dashed"')
        attr = f" [{', '.join(attrs)}]" if attrs else ""
        lines.append(f'"{edge.source}" -> "{edge.target}"{attr};')
        if getattr(edge, "bidirectional", False):
            lines.append(f'"{edge.target}" -> "{edge.source}"{attr};')
    lines.append("}")
    st.graphviz_chart("\n".join(lines), use_container_width=True)


def _render_material(material, debug: bool = False) -> None:
    if isinstance(material, TextMaterial):
        title = f'<div class="source-title">{html.escape(material.title)}</div>' if material.title else ""
        st.markdown(
            f'<div class="source">{title}<div class="source-text">{_escape_lines(material.body)}</div>'
            f'{_glosses_html(material.glosses)}</div>',
            unsafe_allow_html=True,
        )
        return

    if isinstance(material, TableMaterial):
        _render_table(material)
        return

    if isinstance(material, ChartMaterial):
        if material.title:
            st.markdown(f'<div class="source-title">{html.escape(material.title)}</div>', unsafe_allow_html=True)
        st.vega_lite_chart(_chart_spec(material), use_container_width=True)
        if material.footnotes:
            st.markdown(_notes_html(material.footnotes), unsafe_allow_html=True)
        return

    if isinstance(material, SocialFeedMaterial):
        title = f'<div class="source-title">{html.escape(material.title)}</div>' if material.title else ""
        blocks = []
        for post in material.posts:
            meta = " · ".join(part for part in [post.date_label, post.author] if part)
            blocks.append(
                f'<div class="social-post"><div class="social-meta">{html.escape(meta)}</div>'
                f'<div class="source-text">{_escape_lines(post.body)}</div></div>'
            )
        st.markdown(
            f'<div class="source">{title}{"".join(blocks)}{_glosses_html(material.glosses)}'
            f'{_notes_html(material.footnotes)}</div>',
            unsafe_allow_html=True,
        )
        return

    if isinstance(material, (FlowchartMaterial, SchematicMaterial)):
        if material.title:
            st.markdown(f'<div class="source-title">{html.escape(material.title)}</div>', unsafe_allow_html=True)
        _render_graph(material)
        notes = list(getattr(material, "annotations", [])) + list(material.footnotes)
        if notes:
            st.markdown(_notes_html(notes), unsafe_allow_html=True)
        return

    if debug:
        st.json(material.model_dump())


def _answer_badges(task) -> str:
    return "".join(
        f'<span class="answer-badge">{slot.answer_number}</span>' for slot in task.answer_slots
    )


def _render_options(task) -> None:
    rows = []
    for index, option in enumerate(task.options, start=1):
        mark = OPTION_MARKS[index - 1] if index <= len(OPTION_MARKS) else f"({index})"
        rows.append(
            f'<div class="option-row"><div class="option-mark">{mark}</div>'
            f'<div>{html.escape(option)}</div></div>'
        )
    st.markdown(f'<div class="option-list">{"".join(rows)}</div>', unsafe_allow_html=True)


def _render_booklet_preview(item: Item) -> None:
    st.markdown('<div class="exam-header exam-subject">中国語</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="exam-header exam-title"><b>第4問</b>　次の問い（A・B）に答えよ。（配点 60）</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="exam-rule"></div>', unsafe_allow_html=True)

    for subsection in ("A", "B"):
        tasks = tasks_for_subsection(item, subsection)
        if not tasks:
            continue
        groups = task_groups(item, subsection)
        introduced: set[str] = set()
        current_qno: int | None = None

        st.markdown(f'<div class="exam-section">{subsection}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="exam-intro">{html.escape(subsection_intro(item, subsection))}</div>',
            unsafe_allow_html=True,
        )

        for order, kind, block in timeline(item, subsection):
            owner = block if kind == "task" else owner_task_for_order(tasks, order)
            qno = question_number(item.surface_family, subsection, owner)
            if qno != current_qno:
                st.markdown(f'<div class="exam-question">問 {qno}</div>', unsafe_allow_html=True)
                current_qno = qno

            if owner.task_id not in introduced:
                sub_index = subquestion_index(item, owner)
                if sub_index is not None:
                    st.markdown(
                        f'<div class="exam-subq-label">（{sub_index}）</div>',
                        unsafe_allow_html=True,
                    )
                introduced.add(owner.task_id)

            if kind == "material":
                _render_material(block)
            else:
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(block.prompt_ja)}　{_answer_badges(block)}</div>',
                    unsafe_allow_html=True,
                )
                _render_options(block)


def _answer_key_html(item: Item) -> str:
    rows = []
    for task in sorted(item.tasks, key=lambda task: min(answer_numbers(task))):
        answer = " / ".join(
            f"[{slot.answer_number}] {OPTION_MARKS[slot.correct_option - 1]}" for slot in task.answer_slots
        )
        rows.append(
            f"<tr><td>{html.escape(task.task_id)}</td><td>{answer}</td>"
            f"<td>{html.escape('・'.join(task.operations))}</td></tr>"
        )
    return (
        '<table class="teacher-key"><thead><tr><th>Task</th><th>正答</th><th>操作</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


def _render_teacher_view(item: Item) -> None:
    st.markdown("### 正答一覧")
    st.markdown(_answer_key_html(item), unsafe_allow_html=True)
    st.markdown("### 逐題レビュー")
    for task in sorted(item.tasks, key=lambda task: min(answer_numbers(task))):
        slots = "・".join(str(number) for number in answer_numbers(task))
        with st.expander(f"[{slots}] {task.prompt_ja}", expanded=False):
            answers = " / ".join(
                f"[{slot.answer_number}] {OPTION_MARKS[slot.correct_option - 1]}" for slot in task.answer_slots
            )
            st.success(f"正答　{answers}")
            st.caption(
                f"情報依存: {task.dependency_mode or '未指定'}　｜　操作: {' / '.join(task.operations)}"
            )
            st.markdown(f"**解説**　{task.rationale_ja}")
            st.markdown("**根拠**")
            for evidence in task.evidence:
                st.markdown(
                    f"- `{evidence.material_id}` {evidence.locator} — {evidence.explanation_ja}"
                )
            reasons = task.slot_distractor_rationales_ja if task.response_mode == "multi_slot_choice" else None
            if reasons:
                st.markdown("**誤答肢分析**")
                for slot in task.answer_slots:
                    st.markdown(f"[{slot.answer_number}]")
                    for option, reason in reasons.get(slot.slot_id, {}).items():
                        st.markdown(f"- {OPTION_MARKS[int(option) - 1]} {reason}")
            elif task.distractor_rationales_ja:
                st.markdown("**誤答肢分析**")
                for option, reason in task.distractor_rationales_ja.items():
                    st.markdown(f"- {OPTION_MARKS[int(option) - 1]} {reason}")


def _render_structure_view(item: Item) -> None:
    st.markdown("### 2026 surface grammar")
    st.info(FAMILY_SUMMARIES.get(item.surface_family or "", "legacy / unspecified"))
    st.code(slot_group_summary(item), language=None)
    rows = []
    material_map = {material.material_id: material for material in item.materials}
    for task in sorted(item.tasks, key=lambda task: min(answer_numbers(task))):
        refs = ", ".join(dict.fromkeys(e.material_id for e in task.evidence))
        rows.append(
            {
                "slots": "-".join(map(str, answer_numbers(task))),
                "task": task.task_id,
                "question": f"{task.subsection} 問{question_number(item.surface_family, task.subsection, task)}",
                "response": task.response_mode,
                "dependency": task.dependency_mode or "inferred",
                "evidence": refs,
                "material types": ", ".join(
                    sorted({material_map[mid].type for mid in refs.split(", ") if mid in material_map})
                ),
            }
        )
    st.dataframe(rows, hide_index=True, use_container_width=True)


def _render_validation(errors: list[str], warnings: list[str]) -> None:
    if errors:
        st.error(f"未通过 · {len(errors)} 个错误")
        for error in errors:
            st.markdown(f"- {error}")
    else:
        st.success("结构校验通过")
    if warnings:
        with st.expander(f"注意事项 · {len(warnings)}", expanded=bool(errors)):
            for warning in warnings:
                st.markdown(f"- {warning}")


def _download_file(path: Path, label: str, mime: str) -> None:
    if path.exists():
        st.download_button(
            label,
            data=path.read_bytes(),
            file_name=path.name,
            mime=mime,
            use_container_width=True,
        )


def _status_pills(item: Item | None, errors: list[str], warnings: list[str]) -> str:
    if item is None:
        return '<span class="pill bad">JSON 无法解析</span>'
    gate = (
        '<span class="pill bad">校验失败</span>'
        if errors
        else ('<span class="pill warn">通过 · 有警告</span>' if warnings else '<span class="pill ok">校验通过</span>')
    )
    family = FAMILY_LABELS.get(item.surface_family or "", "legacy")
    return (
        f'{gate}<span class="pill">{html.escape(family)}</span>'
        f'<span class="pill">{html.escape(item.workflow.state.upper())}</span>'
        f'<span class="pill">16 slots</span>'
        f'<span class="pill">{html.escape(item.workflow.blueprint_version)}</span>'
    )


def main() -> None:
    st.set_page_config(
        page_title="TABITO 中国語命題 Workbench",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)
    root = _root()

    st.sidebar.markdown("### 命題ライブラリ")
    show_history = st.sidebar.toggle("历史 / 失败样本", value=False)
    items = _discover_items(root, show_history=show_history)
    if not items:
        st.error("题目 JSON 未找到。请从 repository root 启动 UI。")
        st.stop()

    labels = list(items)
    preferred = next(
        (i for i, label in enumerate(labels) if "q4_pilot_002_library_study_main2026.json" in label),
        0,
    )
    selected_label = st.sidebar.selectbox("当前题目", labels, index=preferred)
    selected_path = items[selected_label]

    with st.sidebar.expander("上传 JSON", expanded=False):
        uploaded = st.file_uploader("item JSON", type=["json"], label_visibility="collapsed")
    st.sidebar.caption("默认只显示 active / approved / draft。打开上方开关才显示失败校准样本。")

    if uploaded is not None:
        source_key = f"upload:{uploaded.name}:{uploaded.size}"
        source_text = uploaded.getvalue().decode("utf-8")
        source_name = uploaded.name
    else:
        source_key = str(selected_path)
        source_text = selected_path.read_text(encoding="utf-8")
        source_name = selected_path.name

    if st.session_state.get("editor_source") != source_key:
        st.session_state["editor_source"] = source_key
        st.session_state["editor_text"] = source_text

    current_text = st.session_state["editor_text"]
    item, parse_error = _parse_item(current_text)
    validated_item, errors, warnings = _validation_result(root, current_text)
    if item is None and validated_item is not None:
        item = validated_item

    st.markdown('<div class="tabito-kicker">TABITO EDUCATION · INTERNAL ITEM WORKBENCH</div>', unsafe_allow_html=True)
    st.markdown('<div class="tabito-title">共通テスト中国語 命題 Workbench</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tabito-sub">2026 本試験・追試験を一次蓝本にした Q4 命題・審査・組版</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="status-row">{_status_pills(item, errors, warnings)}</div>', unsafe_allow_html=True)

    if source_name.startswith("q4_pilot_001_"):
        st.error("Pilot 001 は REJECTED：一般的な多資料読解に寄りすぎた失敗校准样本です。")
    elif source_name == "q4_pilot_003_stargazing_makeup2026.json":
        st.warning("Pilot 003 v1 は SUPERSEDED：slot構造は合うが、2026追試の選択肢言語分布から外れます。")

    preview_tab, create_tab, qa_tab, edit_tab = st.tabs(
        ["📄 试卷预览", "✨ 新建命题", "✅ 质检 / 审题", "🛠 编辑 / 导出"]
    )

    with preview_tab:
        if item is None:
            st.error("当前 JSON 无法解析。")
            st.code(parse_error or "unknown parse error", language=None)
        else:
            view = st.radio(
                "视图",
                ["学生册", "教师标注", "结构检查"],
                horizontal=True,
                label_visibility="collapsed",
            )
            if view == "学生册":
                st.markdown('<div class="paper-note">用于判断「像不像共通」。最终分页以 PDF 为准。</div>', unsafe_allow_html=True)
                with st.container(border=True):
                    _render_booklet_preview(item)
            elif view == "教师标注":
                _render_teacher_view(item)
            else:
                _render_structure_view(item)

    with create_tab:
        st.subheader("生成新的 Q4 命题请求")
        st.caption("先决定 2026 family，再决定题材。内容必须原创，但题型语法不允许被『原创』稀释。")
        family_choice = st.radio(
            "题型 family",
            ["main_2026", "makeup_2026"],
            format_func=lambda value: FAMILY_LABELS[value],
            horizontal=True,
        )
        st.markdown(
            f'<div class="gate-box"><b>{FAMILY_LABELS[family_choice]}</b><br>'
            f'<span class="small-muted">{FAMILY_SUMMARIES[family_choice]}</span></div>',
            unsafe_allow_html=True,
        )
        with st.form("new_item_form"):
            topic = st.text_input("主题 / 情境", placeholder="例如：地域施設の利用改善")
            notes = st.text_area(
                "补充要求",
                placeholder="例如：后半不要只做直接摘抄；希望出现真正的条件判断……",
                height=120,
            )
            with st.expander("高级设置", expanded=False):
                c1, c2, c3 = st.columns(3)
                difficulty = c1.selectbox("难度", ["official_like", "easy", "medium", "hard"])
                scope = c2.selectbox("范围", ["full", "mini"])
                domain = c3.text_input("domain", value="auto")
            submitted = st.form_submit_button("生成命题 Prompt", type="primary", use_container_width=True)
        if submitted:
            if not topic.strip():
                st.error("请输入主题。")
            else:
                item_id, request_path, spec_path = create_q4_request(
                    root,
                    topic=topic.strip(),
                    difficulty=difficulty,
                    domain=domain.strip() or "auto",
                    scope=scope,
                    notes=notes.strip() or None,
                    surface_family=family_choice,
                )
                st.success(f"已生成 {item_id} · {FAMILY_LABELS[family_choice]}")
                request_text = request_path.read_text(encoding="utf-8")
                st.text_area("复制到新的 ChatGPT 对话", request_text, height=360)
                c1, c2 = st.columns(2)
                with c1:
                    _download_file(request_path, "下载 request.md", "text/markdown")
                with c2:
                    _download_file(spec_path, "下载 spec.json", "application/json")

    with qa_tab:
        st.subheader("1 · 结构与质量闸门")
        _render_validation(errors, warnings)
        if item:
            matches = check_bank_similarity(item, root / "item_bank" / "approved")
            if matches:
                best_id, best_score = matches[0]
                st.warning(f"题库相似度最高：{best_score:.3f} · {best_id}")
            else:
                st.caption("当前 approved bank 中无显著文本相似项。")

        st.divider()
        st.subheader("2 · Blind Review")
        st.caption("生成给另一个 ChatGPT 对话的盲审 prompt。对方看不到 author key / rationale。")
        if item and st.button("生成 Blind Review Prompt", use_container_width=True):
            temp = _write_ui_temp(root, st.session_state["editor_text"])
            review_path = create_review_request(root, temp)
            review_text = review_path.read_text(encoding="utf-8")
            st.text_area("Blind review prompt", review_text, height=320)
            _download_file(review_path, "下载 review_request.md", "text/markdown")

        review_upload = st.file_uploader("导入 reviewer 返回的 JSON", type=["json"], key="review_upload")
        if review_upload is not None and item is not None:
            try:
                review_text = review_upload.getvalue().decode("utf-8")
                review = Review.model_validate(json.loads(review_text))
                review_errors, review_warnings = compare_review(item, review)
                if review_errors:
                    st.error("Blind review gate 未通过")
                    for error in review_errors:
                        st.markdown(f"- {error}")
                else:
                    st.success("Blind review gate 通过")
                for warning in review_warnings:
                    st.warning(warning)
                if review.issues:
                    st.markdown("**Reviewer issues**")
                    for issue in review.issues:
                        st.markdown(
                            f"- `{issue.severity}` {issue.category}: {issue.description} → {issue.suggested_fix}"
                        )
                st.markdown(f"**総評**　{review.overall_comment_ja}")

                if st.button("生成修订 Prompt", use_container_width=True):
                    item_path = _write_ui_temp(root, st.session_state["editor_text"], "revision_item.json")
                    review_path = _write_ui_temp(root, review_text, "revision_review.json")
                    revision_path = create_revision_request(root, item_path, review_path)
                    revision_text = revision_path.read_text(encoding="utf-8")
                    st.text_area("Revision prompt", revision_text, height=320)
                    _download_file(revision_path, "下载 revision_request.md", "text/markdown")
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                st.error(str(exc))

    with edit_tab:
        st.subheader("编辑")
        st.caption("正常教研无需碰 JSON。只有要精确修某个字段时再展开。")
        with st.expander("高级：编辑 Item JSON", expanded=False):
            edited = st.text_area("Item JSON", key="editor_text", height=560, label_visibility="collapsed")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("重新校验", type="primary", use_container_width=True):
                    _, edit_errors, edit_warnings = _validation_result(root, edited)
                    _render_validation(edit_errors, edit_warnings)
            with c2:
                if st.button("保存到 Draft", use_container_width=True):
                    candidate, error = _parse_item(edited)
                    if candidate is None:
                        st.error(error)
                    else:
                        target = root / "item_bank" / "draft" / f"{candidate.item_id}.json"
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_text(edited, encoding="utf-8")
                        st.success(f"已保存：{target.relative_to(root)}")
            st.download_button(
                "下载当前 JSON",
                data=edited.encode("utf-8"),
                file_name=source_name,
                mime="application/json",
                use_container_width=True,
            )

        st.divider()
        st.subheader("PDF / TeX 导出")
        st.caption("网页预览不需要 LaTeX。PDF 编译需要本机 XeLaTeX。")
        if item and st.button("生成学生版 / 教师版", type="primary", use_container_width=True):
            try:
                out_dir = root / "output" / item.item_id
                student_tex = render_item_tex(item, out_dir, teacher=False)
                teacher_tex = render_item_tex(item, out_dir, teacher=True)
                student_pdf = compile_xelatex(student_tex)
                teacher_pdf = compile_xelatex(teacher_tex)
                st.success(f"输出：{out_dir.relative_to(root)}")
                c1, c2 = st.columns(2)
                with c1:
                    if student_pdf:
                        _download_file(student_pdf, "下载学生版 PDF", "application/pdf")
                    else:
                        _download_file(student_tex, "下载学生版 TeX", "text/plain")
                with c2:
                    if teacher_pdf:
                        _download_file(teacher_pdf, "下载教师版 PDF", "application/pdf")
                    else:
                        _download_file(teacher_tex, "下载教师版 TeX", "text/plain")
            except Exception as exc:
                st.error(f"导出失败：{exc}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from tabito_itemgen.generate_request import (
    create_q4_request,
    create_review_request,
)
from tabito_itemgen.models import (
    ChartMaterial,
    FlowchartMaterial,
    Item,
    SchematicMaterial,
    SocialFeedMaterial,
    TableMaterial,
    TextMaterial,
)
from tabito_itemgen.paths import find_project_root
from tabito_itemgen.render import compile_xelatex, render_item_tex
from tabito_itemgen.validate import validate_item_file

OPTION_MARKS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
FAMILY_LABELS = {
    "main_2026": "2026 本試験型",
    "makeup_2026": "2026 追試験型",
}


def _root() -> Path:
    try:
        return find_project_root()
    except RuntimeError:
        return Path.cwd()


def _discover_items(root: Path) -> dict[str, Path]:
    groups = [
        ("Pilot", root / "pilots"),
        ("Draft", root / "item_bank" / "draft"),
        ("Approved", root / "item_bank" / "approved"),
        ("Example", root / "examples"),
    ]
    result: dict[str, Path] = {}
    for group, directory in groups:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.json")):
            if path.name.startswith("q4_pilot_001_"):
                label_group = "Rejected calibration"
            else:
                label_group = group
            result[f"{label_group} · {path.name}"] = path
    return result


def _parse_item(text: str) -> tuple[Item | None, str | None]:
    try:
        data = json.loads(text)
        return Item.model_validate(data), None
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        return None, str(exc)


def _raw_item_data(text: str) -> dict:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _write_ui_temp(root: Path, text: str) -> Path:
    path = root / "workspace" / "ui_temp" / "current.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _material_title(material) -> str:
    return material.title or material.type.replace("_", " ").title()


def _render_glosses(glosses: dict[str, str]) -> None:
    if not glosses:
        return
    with st.expander("語注", expanded=False):
        for word, gloss in glosses.items():
            st.markdown(f"**{word}** — {gloss}")


def _render_material(material) -> None:
    st.markdown(f"#### {_material_title(material)}")

    if isinstance(material, TextMaterial):
        st.markdown(material.body.replace("\n", "  \n"))
        _render_glosses(material.glosses)
        return

    if isinstance(material, TableMaterial):
        df = pd.DataFrame(material.rows, columns=material.columns)
        st.dataframe(df, hide_index=True, use_container_width=True)
        for note in material.footnotes:
            st.caption(note)
        return

    if isinstance(material, ChartMaterial):
        data = {series.name: series.values for series in material.series}
        df = pd.DataFrame(data, index=material.categories)
        if material.chart_kind == "line":
            st.line_chart(df)
        else:
            st.bar_chart(df)
        if material.y_label:
            st.caption(material.y_label)
        for note in material.footnotes:
            st.caption(note)
        return

    if isinstance(material, SocialFeedMaterial):
        for post in material.posts:
            with st.container(border=True):
                meta = " · ".join(part for part in [post.date_label, post.author] if part)
                if meta:
                    st.caption(meta)
                st.markdown(post.body)
        _render_glosses(material.glosses)
        for note in material.footnotes:
            st.caption(note)
        return

    if isinstance(material, (FlowchartMaterial, SchematicMaterial)):
        lines = ["digraph G {", 'rankdir="LR";', 'node [shape=box, style="rounded"];']
        for node in material.nodes:
            label = node.label.replace('"', "'")
            note = getattr(node, "note", None)
            if note:
                label = f"{label}\\n{str(note).replace(chr(34), chr(39))}"
            lines.append(f'"{node.node_id}" [label="{label}"];')
        for edge in material.edges:
            attrs: list[str] = []
            if edge.label:
                attrs.append(f'label="{edge.label.replace(chr(34), chr(39))}"')
            if getattr(edge, "dashed", False):
                attrs.append('style="dashed"')
            attr_text = f" [{', '.join(attrs)}]" if attrs else ""
            lines.append(f'"{edge.source}" -> "{edge.target}"{attr_text};')
            if getattr(edge, "bidirectional", False):
                lines.append(f'"{edge.target}" -> "{edge.source}"{attr_text};')
        lines.append("}")
        st.graphviz_chart("\n".join(lines), use_container_width=True)
        for annotation in getattr(material, "annotations", []):
            st.caption(annotation)
        for note in material.footnotes:
            st.caption(note)
        return

    st.json(material.model_dump())


def _render_task(task, teacher: bool) -> None:
    numbers = " ".join(f"[{slot.answer_number}]" for slot in task.answer_slots)
    st.markdown(f"#### {numbers} {task.prompt_ja}")
    for index, option in enumerate(task.options, start=1):
        mark = OPTION_MARKS[index - 1] if index <= len(OPTION_MARKS) else f"({index})"
        st.markdown(f"{mark} {option}")

    if not teacher:
        return

    st.divider()
    answers = []
    for slot in task.answer_slots:
        mark = OPTION_MARKS[slot.correct_option - 1]
        answers.append(f"[{slot.answer_number}] {mark}")
    st.success("正答: " + " / ".join(answers))
    st.caption(f"情報依存: {task.dependency_mode or '未指定'} · 操作: {', '.join(task.operations)}")
    st.markdown(f"**解説**  {task.rationale_ja}")

    with st.expander("根拠", expanded=False):
        for evidence in task.evidence:
            st.markdown(
                f"- **{evidence.material_id} / {evidence.locator}** — {evidence.explanation_ja}"
            )

    if task.response_mode == "multi_slot_choice" and task.slot_distractor_rationales_ja:
        with st.expander("誤答肢分析", expanded=False):
            for slot in task.answer_slots:
                st.markdown(f"**[{slot.answer_number}]**")
                for option, reason in task.slot_distractor_rationales_ja.get(slot.slot_id, {}).items():
                    idx = int(option)
                    st.markdown(f"- {OPTION_MARKS[idx - 1]} {reason}")
    elif task.distractor_rationales_ja:
        with st.expander("誤答肢分析", expanded=False):
            for option, reason in task.distractor_rationales_ja.items():
                idx = int(option)
                st.markdown(f"- {OPTION_MARKS[idx - 1]} {reason}")


def _render_exam(item: Item, teacher: bool) -> None:
    mode = "教師版" if teacher else "学生版"
    st.markdown(f"### 第4問　{item.title_ja}")
    st.caption(f"{mode} · {item.item_id} · {item.difficulty}")

    for subsection in ("A", "B"):
        st.markdown(f"## {subsection}")
        blocks: list[tuple[int, str, object]] = []
        blocks.extend(
            (material.order, "material", material)
            for material in item.materials
            if material.subsection == subsection
        )
        blocks.extend(
            (task.order, "task", task)
            for task in item.tasks
            if task.subsection == subsection
        )
        for _, kind, block in sorted(blocks, key=lambda value: value[0]):
            with st.container(border=True):
                if kind == "material":
                    _render_material(block)
                else:
                    _render_task(block, teacher=teacher)


def _validation_panel(root: Path, text: str) -> None:
    temp = _write_ui_temp(root, text)
    item, errors, warnings = validate_item_file(temp)
    if errors:
        st.error(f"FAIL · {len(errors)} error(s)")
        for error in errors:
            st.code(error, language=None)
    else:
        slots = sum(len(task.answer_slots) for task in item.tasks) if item else 0
        st.success(f"PASS · {slots} answer slots")
    for warning in warnings:
        st.warning(warning)


def _download_file(path: Path, label: str, mime: str) -> None:
    if path.exists():
        st.download_button(
            label,
            data=path.read_bytes(),
            file_name=path.name,
            mime=mime,
            use_container_width=True,
        )


def main() -> None:
    st.set_page_config(
        page_title="TABITO 命題 Workbench",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .stApp { background: #faf8f2; }
        [data-testid="stSidebar"] { background: #f2efe6; }
        h1, h2, h3 { color: #152a43; }
        .tabito-kicker { letter-spacing: .08em; color: #7c6a45; font-size: .82rem; font-weight: 700; }
        .tabito-sub { color: #657080; margin-top: -.6rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    root = _root()
    st.markdown('<div class="tabito-kicker">TABITO EDUCATION · INTERNAL ITEM WORKBENCH</div>', unsafe_allow_html=True)
    st.title("共通テスト中国語 命題 Workbench")
    st.markdown(
        '<div class="tabito-sub">2026 本試験型 / 追試験型 surface grammar · Q4 production workflow</div>',
        unsafe_allow_html=True,
    )

    items = _discover_items(root)
    if not items:
        st.error("题目 JSON 未找到。请从 repository root 启动 UI。")
        st.stop()

    labels = list(items)
    preferred = next(
        (i for i, label in enumerate(labels) if "q4_pilot_002_library_study_main2026.json" in label),
        0,
    )

    st.sidebar.header("题目")
    selected_label = st.sidebar.selectbox("选择已有题目", labels, index=preferred)
    selected_path = items[selected_label]
    uploaded = st.sidebar.file_uploader("或上传 item JSON", type=["json"])

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

    text = st.session_state["editor_text"]
    raw_data = _raw_item_data(text)
    item, parse_error = _parse_item(text)
    surface_family = raw_data.get("surface_family")

    if source_name.startswith("q4_pilot_001_"):
        st.error(
            "Pilot 001 已判定为 REJECTED calibration sample：它只有泛化的多资料阅读结构，"
            "不够接近 2026 本试/追试的实际 Q4 题型。请以 Pilot 002 及之后的 v3 样本为准。"
        )

    if item:
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Answer slots", sum(len(task.answer_slots) for task in item.tasks))
        c2.metric("Materials", len(item.materials))
        c3.metric("Tasks", len(item.tasks))
        c4.metric("Surface family", FAMILY_LABELS.get(surface_family, surface_family or "legacy"))
        c5.metric("Blueprint", item.workflow.blueprint_version.replace("R8-2026-", ""))
    else:
        st.error("当前 JSON 无法解析，先到「JSON / 校验」修正。")

    preview_tab, json_tab, request_tab, workflow_tab = st.tabs(
        ["👀 题目预览", "🧪 JSON / 校验", "✨ 新建命题", "🔍 Review / PDF"]
    )

    with preview_tab:
        if item is None:
            st.code(parse_error or "Unknown parsing error", language=None)
        else:
            if surface_family in FAMILY_LABELS:
                st.info(f"当前结构：{FAMILY_LABELS[surface_family]}（{surface_family}）")
            student_tab, teacher_tab = st.tabs(["学生版", "教师版"])
            with student_tab:
                _render_exam(item, teacher=False)
            with teacher_tab:
                _render_exam(item, teacher=True)

    with json_tab:
        st.caption(f"当前来源: {source_name}")
        edited = st.text_area(
            "Item JSON",
            key="editor_text",
            height=560,
        )
        left, right = st.columns(2)
        with left:
            if st.button("运行完整校验", type="primary", use_container_width=True):
                _validation_panel(root, edited)
        with right:
            if st.button("保存到 Draft", use_container_width=True):
                candidate, error = _parse_item(edited)
                if candidate is None:
                    st.error(error)
                else:
                    target = root / "item_bank" / "draft" / f"{candidate.item_id}.json"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(edited, encoding="utf-8")
                    st.success(f"已保存: {target.relative_to(root)}")
        st.download_button(
            "下载当前 JSON",
            data=edited.encode("utf-8"),
            file_name=source_name,
            mime="application/json",
        )

    with request_tab:
        st.subheader("生成一个新的 Q4 命题请求")
        st.caption(
            "full Q4 必须先选 2026 本试型或追试型。内容要原创，但 21–36 的题型骨架按所选 family 复现。"
        )
        with st.form("new_item_form"):
            topic = st.text_input("主题 / 情境", placeholder="例如：地域図書館の利用改善")
            surface_family_choice = st.radio(
                "2026 题型 family",
                options=["main_2026", "makeup_2026"],
                format_func=lambda value: FAMILY_LABELS[value],
                horizontal=True,
            )
            c1, c2, c3 = st.columns(3)
            difficulty = c1.selectbox("难度", ["official_like", "easy", "medium", "hard"])
            scope = c2.selectbox("范围", ["full", "mini"])
            domain = c3.text_input("domain", value="auto")
            notes = st.text_area(
                "追加要求",
                placeholder="内容原创，但请严格保持所选2026 family的问1/问2/问3和解答格结构……",
            )
            submitted = st.form_submit_button("生成 request.md", type="primary", use_container_width=True)
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
                    surface_family=surface_family_choice,
                )
                st.success(f"已生成 {item_id} · {FAMILY_LABELS[surface_family_choice]}")
                request_text = request_path.read_text(encoding="utf-8")
                st.text_area("直接复制给 ChatGPT", request_text, height=420)
                c1, c2 = st.columns(2)
                with c1:
                    _download_file(request_path, "下载 request.md", "text/markdown")
                with c2:
                    _download_file(spec_path, "下载 spec.json", "application/json")

    with workflow_tab:
        if item is None:
            st.warning("先修正当前 JSON。")
        else:
            st.subheader("Blind review")
            if st.button("生成 Blind Review Prompt", use_container_width=True):
                temp = _write_ui_temp(root, st.session_state["editor_text"])
                review_path = create_review_request(root, temp)
                review_text = review_path.read_text(encoding="utf-8")
                st.text_area("交给另一个 ChatGPT 对话", review_text, height=360)
                _download_file(review_path, "下载 review_request.md", "text/markdown")

            st.divider()
            st.subheader("PDF / TeX 导出")
            st.caption("网页预览无需 LaTeX。PDF 编译需要本机可用的 XeLaTeX。")
            if st.button("生成学生版 / 教师版", type="primary", use_container_width=True):
                out_dir = root / "output" / item.item_id
                student_tex = render_item_tex(item, out_dir, teacher=False)
                teacher_tex = render_item_tex(item, out_dir, teacher=True)
                student_pdf = compile_xelatex(student_tex)
                teacher_pdf = compile_xelatex(teacher_tex)
                st.success(f"已输出到 {out_dir.relative_to(root)}")
                c1, c2 = st.columns(2)
                with c1:
                    if student_pdf:
                        _download_file(student_pdf, "下载学生版 PDF", "application/pdf")
                    else:
                        _download_file(student_tex, "XeLaTeX 不可用 · 下载学生版 TeX", "text/plain")
                with c2:
                    if teacher_pdf:
                        _download_file(teacher_pdf, "下载教师版 PDF", "application/pdf")
                    else:
                        _download_file(teacher_tex, "XeLaTeX 不可用 · 下载教师版 TeX", "text/plain")

            st.divider()
            st.subheader("工作流状态")
            st.json(
                {
                    "item_id": item.item_id,
                    "state": item.workflow.state,
                    "surface_family": surface_family,
                    "generation_mode": item.workflow.generation_mode,
                    "blueprint": item.workflow.blueprint_version,
                    "source": source_name,
                }
            )


if __name__ == "__main__":
    main()

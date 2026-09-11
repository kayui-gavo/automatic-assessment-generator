from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .models import (
    ChartMaterial,
    FlowchartMaterial,
    Item,
    SchematicMaterial,
    SocialFeedMaterial,
    TableMaterial,
    TextMaterial,
)


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _answer_boxes(task) -> str:
    return r" \;・\; ".join(
        rf"\fbox{{\rule{{0pt}}{{1.55em}}\hspace{{0.45em}}{slot.answer_number}\hspace{{0.45em}}}}"
        for slot in task.answer_slots
    )


def _material_prefix(material) -> str:
    bundle = ""
    if getattr(material, "bundle_id", None):
        bundle = rf"\hfill{{\scriptsize bundle: {latex_escape(material.bundle_id)}}}"
    title = rf"\textbf{{{latex_escape(material.title)}}}" if material.title else ""
    if not title and not bundle:
        return ""
    return title + bundle + r"\par\medskip "


def _text_material(material: TextMaterial) -> str:
    body = latex_escape(material.body).replace("\n", r"\\" + "\n")
    glosses = ""
    if material.glosses:
        glosses = (r"\\" + "\n") + r"\quad ".join(
            rf"\footnotesize *{latex_escape(word)}：{latex_escape(note)}"
            for word, note in material.glosses.items()
        )
    return (
        "\\Needspace{6\\baselineskip}\n"
        "\\begin{minipage}{0.94\\linewidth}\n"
        + _material_prefix(material)
        + "{\\zhfont "
        + body
        + "}"
        + glosses
        + "\n\\end{minipage}\n"
    )


def _table_material(material: TableMaterial) -> str:
    n = len(material.columns)
    colspec = "|" + "|".join([">{\\centering\\arraybackslash}X"] * n) + "|"
    header = " & ".join(rf"\textbf{{{latex_escape(c)}}}" for c in material.columns) + r" \\ \hline"
    rows = "\n".join(" & ".join(latex_escape(cell) for cell in row) + r" \\ \hline" for row in material.rows)
    notes = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{8\\baselineskip}\n"
        + _material_prefix(material)
        + "\\begin{center}\n\\small\n"
        + rf"\begin{{tabularx}}{{0.98\linewidth}}{{{colspec}}}\hline"
        + "\n"
        + header
        + "\n"
        + rows
        + "\n\\end{tabularx}\n"
        + (notes + "\n" if notes else "")
        + "\\end{center}\n"
    )


def _chart_material(material: ChartMaterial) -> str:
    plots: list[str] = []
    line_styles = ["solid,mark=*", "dashed,mark=square*", "dotted,mark=triangle*"]
    horizontal = material.chart_kind == "horizontal_bar"
    for index, series in enumerate(material.series):
        if horizontal:
            pairs = " ".join(
                f"({value},{latex_escape(category)})"
                for category, value in zip(material.categories, series.values)
            )
        else:
            pairs = " ".join(
                f"({latex_escape(category)},{value})"
                for category, value in zip(material.categories, series.values)
            )
        if material.chart_kind in {"bar", "horizontal_bar", "stacked_bar"}:
            plot_style = "draw=black,fill=black!15"
        else:
            plot_style = "draw=black," + line_styles[index % len(line_styles)]
        legend = rf"\addlegendentry{{{latex_escape(series.name)}}}" if len(material.series) > 1 else ""
        plots.append(rf"\addplot+[{plot_style}] coordinates {{{pairs}}};{legend}")

    ylabel = latex_escape(material.y_label or "")
    symbols = ",".join(latex_escape(c) for c in material.categories)
    if horizontal:
        axis_style = (
            rf"xbar,symbolic y coords={{{symbols}}},ytick=data,xlabel={{{ylabel}}},"
            "y tick label style={font=\\small}"
        )
    else:
        bar_style = "ybar stacked," if material.chart_kind == "stacked_bar" else ("ybar," if material.chart_kind == "bar" else "")
        axis_style = (
            rf"{bar_style}symbolic x coords={{{symbols}}},xtick=data,"
            rf"x tick label style={{rotate=30,anchor=east}},ylabel={{{ylabel}}}"
        )
    notes = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{12\\baselineskip}\n"
        + _material_prefix(material)
        + "\\begin{center}\n"
        + "\\begin{tikzpicture}\n"
        + rf"\begin{{axis}}[width=0.9\linewidth,height=6cm,{axis_style},legend style={{at={{(0.5,-0.28)}},anchor=north,legend columns=-1}}]"
        + "\n"
        + "\n".join(plots)
        + "\n\\end{axis}\n\\end{tikzpicture}\n"
        + (notes + "\n" if notes else "")
        + "\\end{center}\n"
    )


def _node_xy(index: int, x: float | None, y: float | None, columns: int = 3) -> tuple[float, float]:
    if x is not None and y is not None:
        return x, y
    row, col = divmod(index, columns)
    return col * 5.0, -row * 2.4


def _flowchart_material(material: FlowchartMaterial) -> str:
    nodes = []
    for index, node in enumerate(material.nodes):
        x, y = _node_xy(index, node.x, node.y)
        nodes.append(
            rf"\node[flowbox] ({latex_escape(node.node_id)}) at ({x},{y}) {{{latex_escape(node.label)}}};"
        )
    edges = []
    for edge in material.edges:
        label = rf" node[midway,fill=white,inner sep=1pt] {{{latex_escape(edge.label)}}}" if edge.label else ""
        edges.append(
            rf"\draw[->,>=stealth] ({latex_escape(edge.source)}) --{label} ({latex_escape(edge.target)});"
        )
    notes = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{12\\baselineskip}\n"
        + _material_prefix(material)
        + "\\begin{center}\n\\begin{tikzpicture}[flowbox/.style={draw,rounded corners=1pt,align=center,text width=3.7cm,minimum height=1.0cm}]\n"
        + "\n".join(nodes)
        + "\n"
        + "\n".join(edges)
        + "\n\\end{tikzpicture}\n"
        + (notes + "\n" if notes else "")
        + "\\end{center}\n"
    )


def _social_feed_material(material: SocialFeedMaterial) -> str:
    blocks: list[str] = []
    for post in material.posts:
        meta_parts = [part for part in [post.author, post.date_label] if part]
        meta = " / ".join(latex_escape(part) for part in meta_parts)
        body = latex_escape(post.body).replace("\n", r"\\" + "\n")
        blocks.append(
            "\\noindent\\fbox{\\begin{minipage}{0.91\\linewidth}\n"
            + (rf"\textbf{{{meta}}}\par " if meta else "")
            + "{\\zhfont " + body + "}\n"
            + "\\end{minipage}}\\par\\vspace{0.35em}\n"
        )
    glosses = ""
    if material.glosses:
        glosses = r"\quad ".join(
            rf"\footnotesize *{latex_escape(word)}：{latex_escape(note)}"
            for word, note in material.glosses.items()
        ) + "\n"
    notes = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{10\\baselineskip}\n"
        + _material_prefix(material)
        + "\n".join(blocks)
        + glosses
        + (notes + "\n" if notes else "")
    )


def _schematic_material(material: SchematicMaterial) -> str:
    nodes: list[str] = []
    for index, node in enumerate(material.nodes):
        x, y = _node_xy(index, node.x, node.y, columns=4)
        label = latex_escape(node.label)
        if node.note:
            label += r"\\{\scriptsize " + latex_escape(node.note) + "}"
        nodes.append(
            rf"\node[schematicnode] ({latex_escape(node.node_id)}) at ({x},{y}) {{{label}}};"
        )
    edges: list[str] = []
    for edge in material.edges:
        if edge.bidirectional:
            arrow = "<->,>=stealth"
        elif material.type == "annotated_diagram":
            arrow = "->,>=stealth"
        else:
            arrow = "-"
        dash = ",dashed" if edge.dashed else ""
        label = rf" node[midway,fill=white,inner sep=1pt] {{{latex_escape(edge.label)}}}" if edge.label else ""
        edges.append(
            rf"\draw[{arrow}{dash}] ({latex_escape(edge.source)}) --{label} ({latex_escape(edge.target)});"
        )
    annotations = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.annotations)
    footnotes = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{12\\baselineskip}\n"
        + _material_prefix(material)
        + "\\begin{center}\n"
        + "\\begin{tikzpicture}[schematicnode/.style={draw,rounded corners=1pt,align=center,text width=3.0cm,minimum height=0.9cm}]\n"
        + "\n".join(nodes)
        + "\n"
        + "\n".join(edges)
        + "\n\\end{tikzpicture}\n"
        + (annotations + "\n" if annotations else "")
        + (footnotes + "\n" if footnotes else "")
        + "\\end{center}\n"
    )


def _material_block(material) -> str:
    if isinstance(material, TextMaterial):
        return _text_material(material)
    if isinstance(material, TableMaterial):
        return _table_material(material)
    if isinstance(material, ChartMaterial):
        return _chart_material(material)
    if isinstance(material, FlowchartMaterial):
        return _flowchart_material(material)
    if isinstance(material, SocialFeedMaterial):
        return _social_feed_material(material)
    if isinstance(material, SchematicMaterial):
        return _schematic_material(material)
    raise TypeError(f"unsupported material type: {type(material)!r}")


def _teacher_distractors(task) -> str:
    lines: list[str] = []
    if task.response_mode == "multi_slot_choice":
        for slot in task.answer_slots:
            reasons = task.slot_distractor_rationales_ja.get(slot.slot_id, {})
            if reasons:
                joined = " / ".join(f"{key}: {value}" for key, value in reasons.items())
                lines.append(f"{slot.slot_id} — {joined}")
    elif task.distractor_rationales_ja:
        lines.append(" / ".join(f"{key}: {value}" for key, value in task.distractor_rationales_ja.items()))
    return "\\\n".join(latex_escape(line) for line in lines)


def _task_block(task, teacher: bool) -> str:
    labels = [
        rf"\noindent\optnum{{{index + 1}}}\quad {latex_escape(option)}\par"
        for index, option in enumerate(task.options)
    ]
    boxes = _answer_boxes(task)
    answer_line = (r"\par\hfill " + boxes + r"\par") if len(task.answer_slots) >= 3 else (r" \hfill " + boxes + r"\par")
    block = (
        "\\Needspace{10\\baselineskip}\n\\vspace{0.9em}\n"
        + rf"\noindent\textbf{{{latex_escape(task.task_id)}}}\quad {latex_escape(task.prompt_ja)}"
        + answer_line + "\n"
        + "\\vspace{0.45em}\n"
        + "\n".join(labels)
        + "\n"
    )
    if teacher:
        answers = ", ".join(
            f"{slot.answer_number}→{slot.correct_option}" for slot in task.answer_slots
        )
        evidence = " / ".join(
            f"{e.material_id} [{e.locator}] {e.explanation_ja}" for e in task.evidence
        )
        dependency = task.dependency_mode or "(未指定・validatorで推定)"
        distractors = _teacher_distractors(task)
        block += (
            "\\begin{quote}\\small\n"
            + rf"\textbf{{正答}} {latex_escape(answers)}\par "
            + rf"\textbf{{情報依存}} {latex_escape(dependency)}\par "
            + rf"\textbf{{根拠}} {latex_escape(evidence)}\par "
            + rf"\textbf{{解説}} {latex_escape(task.rationale_ja)}\par "
            + (rf"\textbf{{誤答肢}} {distractors}" if distractors else "")
            + "\n\\end{quote}\n"
        )
    return block


def render_item_tex(item: Item, out_dir: Path, teacher: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=18mm]{geometry}
\usepackage{fontspec}
\usepackage{xeCJK}
\usepackage{array,tabularx}
\usepackage{needspace}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\setmainfont{Liberation Serif}
\setCJKmainfont{Noto Serif CJK JP}
\newCJKfontfamily\zhfont{Noto Serif CJK SC}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\newcommand{\optnum}[1]{\raisebox{0.1ex}{\textcircled{\scriptsize #1}}}
\pagestyle{plain}
\begin{document}
"""
    edition = "【教師用】" if teacher else ""
    tex += rf"\noindent\textbf{{中国語}}\hfill {edition}\par\vspace{{0.8em}}" + "\n"
    tex += rf"\noindent{{\Large\textbf{{第4問}}}}\quad 次の問い（A・B）に答えよ。（配点 60）\par" + "\n"
    tex += rf"\vspace{{0.5em}}\noindent\textbf{{旅人教育 オリジナル模試}}\quad {latex_escape(item.title_ja)}\par" + "\n"

    for subsection in ("A", "B"):
        tex += rf"\vspace{{1.2em}}\noindent{{\large\textbf{{{subsection}}}}}\par\vspace{{0.5em}}" + "\n"
        blocks: list[tuple[int, str]] = []
        for material in item.materials:
            if material.subsection == subsection:
                blocks.append((material.order, _material_block(material)))
        for task in item.tasks:
            if task.subsection == subsection:
                blocks.append((task.order, _task_block(task, teacher)))
        for _, block in sorted(blocks, key=lambda pair: pair[0]):
            tex += block + "\n"

    tex += "\\end{document}\n"
    suffix = "teacher" if teacher else "student"
    tex_path = out_dir / f"{item.item_id}.{suffix}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return tex_path


def compile_xelatex(tex_path: Path) -> Path | None:
    exe = shutil.which("xelatex")
    if not exe:
        return None
    subprocess.run(
        [exe, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=tex_path.parent,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    return tex_path.with_suffix(".pdf")

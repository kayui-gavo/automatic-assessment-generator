from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .models import ChartMaterial, FlowchartMaterial, Item, TableMaterial, TextMaterial


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
    nums = r" \;・\; ".join(
        rf"\fbox{{\rule{{0pt}}{{1.55em}}\hspace{{0.45em}}{slot.answer_number}\hspace{{0.45em}}}}"
        for slot in task.answer_slots
    )
    return rf"\hfill {nums}"


def _text_material(material: TextMaterial) -> str:
    title = rf"\textbf{{{latex_escape(material.title)}}}\par " if material.title else ""
    body = latex_escape(material.body).replace("\n", r"\\" + "\n")
    glosses = ""
    if material.glosses:
        glosses = (r"\\" + "\n") + r"\quad ".join(
            rf"\footnotesize *{latex_escape(word)}：{latex_escape(note)}"
            for word, note in material.glosses.items()
        )
    return (
        "\\begin{minipage}{0.94\\linewidth}\n"
        + title
        + "{\\zhfont "
        + body
        + "}"
        + glosses
        + "\n\\end{minipage}\n"
    )


def _table_material(material: TableMaterial) -> str:
    n = len(material.columns)
    colspec = "|" + "|".join([">{\\centering\\arraybackslash}X"] * n) + "|"
    title = rf"\textbf{{{latex_escape(material.title)}}}\par\medskip " if material.title else ""
    header = " & ".join(rf"\textbf{{{latex_escape(c)}}}" for c in material.columns) + r" \\ \hline"
    rows = "\n".join(" & ".join(latex_escape(cell) for cell in row) + r" \\ \hline" for row in material.rows)
    notes = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.footnotes)
    return (
        title
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
    title = rf"\textbf{{{latex_escape(material.title)}}}\par " if material.title else ""
    coords: list[str] = []
    line_styles = ["solid,mark=*", "dashed,mark=square*", "dotted,mark=triangle*"]
    for index, series in enumerate(material.series):
        pairs = " ".join(
            f"({latex_escape(category)},{value})"
            for category, value in zip(material.categories, series.values)
        )
        if material.chart_kind == "bar":
            plot_style = "draw=black,fill=black!15"
        else:
            plot_style = "draw=black," + line_styles[index % len(line_styles)]
        legend = rf"\addlegendentry{{{latex_escape(series.name)}}}" if len(material.series) > 1 else ""
        coords.append(rf"\addplot+[{plot_style}] coordinates {{{pairs}}};{legend}")
    style = "ybar," if material.chart_kind == "bar" else ""
    ylabel = latex_escape(material.y_label or "")
    symbols = ",".join(latex_escape(c) for c in material.categories)
    notes = "\\\n".join(rf"\footnotesize {latex_escape(note)}" for note in material.footnotes)
    return (
        title
        + "\\begin{center}\n"
        + "\\begin{tikzpicture}\n"
        + rf"\begin{{axis}}[width=0.9\linewidth,height=6cm,{style}symbolic x coords={{{symbols}}},xtick=data,x tick label style={{rotate=30,anchor=east}},ylabel={{{ylabel}}},legend style={{at={{(0.5,-0.28)}},anchor=north,legend columns=-1}}]"
        + "\n"
        + "\n".join(coords)
        + "\n\\end{axis}\n\\end{tikzpicture}\n"
        + (notes + "\n" if notes else "")
        + "\\end{center}\n"
    )


def _flowchart_material(material: FlowchartMaterial) -> str:
    title = rf"\textbf{{{latex_escape(material.title)}}}\par " if material.title else ""
    nodes = []
    for index, node in enumerate(material.nodes):
        row, col = divmod(index, 3)
        x, y = col * 5, -row * 2.4
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
        title
        + "\\begin{center}\n\\begin{tikzpicture}[flowbox/.style={draw,rounded corners=1pt,align=center,text width=3.7cm,minimum height=1.0cm}]\n"
        + "\n".join(nodes)
        + "\n"
        + "\n".join(edges)
        + "\n\\end{tikzpicture}\n"
        + (notes + "\n" if notes else "")
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
    raise TypeError(f"unsupported material type: {type(material)!r}")


def _task_block(task, teacher: bool) -> str:
    labels = []
    for index, option in enumerate(task.options):
        labels.append(rf"\noindent\optnum{{{index + 1}}}\quad {latex_escape(option)}\par")
    boxes = _answer_boxes(task)
    answer_line = (r"\par\hfill " + boxes + r"\par") if len(task.answer_slots) >= 3 else (" " + boxes + r"\par")
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
        block += (
            "\\begin{quote}\\small\n"
            + rf"\textbf{{正答}} {latex_escape(answers)}\par "
            + rf"\textbf{{根拠}} {latex_escape(evidence)}\par "
            + rf"\textbf{{解説}} {latex_escape(task.rationale_ja)}"
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

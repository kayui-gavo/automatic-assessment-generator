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
from .presentation import (
    owner_task_for_order,
    question_number,
    subsection_intro,
    subquestion_index,
    task_groups,
    tasks_for_subsection,
    timeline,
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
    return r" \quad ".join(
        rf"\fbox{{\rule{{0pt}}{{1.45em}}\hspace{{0.42em}}{slot.answer_number}\hspace{{0.42em}}}}"
        for slot in task.answer_slots
    )


def _material_title(material) -> str:
    if not material.title:
        return ""
    return rf"\textbf{{{latex_escape(material.title)}}}\par\smallskip "


def _text_material(material: TextMaterial) -> str:
    body = latex_escape(material.body).replace("\n", r"\\" + "\n")
    glosses = ""
    if material.glosses:
        glosses = (r"\\" + "\n") + r"\quad ".join(
            rf"\scriptsize *{latex_escape(word)}：{latex_escape(note)}"
            for word, note in material.glosses.items()
        )
    return (
        "\\Needspace{6\\baselineskip}\n"
        "\\begin{minipage}{0.96\\linewidth}\n"
        + _material_title(material)
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
    rows = "\n".join(
        " & ".join(latex_escape(cell) for cell in row) + r" \\ \hline"
        for row in material.rows
    )
    notes = "\\\n".join(rf"\scriptsize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{8\\baselineskip}\n"
        + _material_title(material)
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


def _pgf_tick_labels(categories: list[str]) -> str:
    """Brace each label so commas/spaces stay inside one pgfplots tick label."""
    return ",".join("{" + latex_escape(category) + "}" for category in categories)


def _chart_material(material: ChartMaterial) -> str:
    plots: list[str] = []
    line_styles = ["solid,mark=*", "dashed,mark=square*", "dotted,mark=triangle*"]
    fills = ["black!20", "black!42", "black!62", "black!78"]
    horizontal = material.chart_kind == "horizontal_bar"
    positions = list(range(len(material.categories)))

    for index, series in enumerate(material.series):
        if horizontal:
            pairs = " ".join(
                f"({value},{position})"
                for position, value in zip(positions, series.values)
            )
        else:
            pairs = " ".join(
                f"({position},{value})"
                for position, value in zip(positions, series.values)
            )

        if material.chart_kind in {"bar", "horizontal_bar", "stacked_bar"}:
            plot_style = f"draw=black,fill={fills[index % len(fills)]}"
        else:
            plot_style = "draw=black," + line_styles[index % len(line_styles)]
        legend = rf"\addlegendentry{{{latex_escape(series.name)}}}" if len(material.series) > 1 else ""
        plots.append(rf"\addplot+[{plot_style}] coordinates {{{pairs}}};{legend}")

    axis_label = latex_escape(material.y_label or "")
    ticks = ",".join(str(position) for position in positions)
    tick_labels = _pgf_tick_labels(material.categories)
    if horizontal:
        axis_style = (
            rf"xbar,ytick={{{ticks}}},yticklabels={{{tick_labels}}},xlabel={{{axis_label}}},"
            "y tick label style={font=\\small},grid=major"
        )
    else:
        bar_style = (
            "ybar stacked,"
            if material.chart_kind == "stacked_bar"
            else ("ybar," if material.chart_kind == "bar" else "")
        )
        axis_style = (
            rf"{bar_style}xtick={{{ticks}}},xticklabels={{{tick_labels}}},"
            r"x tick label style={rotate=25,anchor=east,font=\small},"
            rf"ylabel={{{axis_label}}},grid=major"
        )

    notes = "\\\n".join(rf"\scriptsize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{12\\baselineskip}\n"
        + _material_title(material)
        + "\\begin{center}\n"
        + "\\begin{tikzpicture}\n"
        + rf"\begin{{axis}}[width=0.9\linewidth,height=5.8cm,{axis_style},axis line style={{black!55}},grid style={{black!10}},legend style={{at={{(0.5,-0.25)}},anchor=north,legend columns=-1,draw=none}}]"
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
    nodes: list[str] = []
    for index, node in enumerate(material.nodes):
        x, y = _node_xy(index, node.x, node.y)
        nodes.append(
            rf"\node[flowbox] ({latex_escape(node.node_id)}) at ({x},{y}) {{{latex_escape(node.label)}}};"
        )

    edges: list[str] = []
    for edge in material.edges:
        label = (
            rf" node[midway,fill=white,inner sep=1pt] {{{latex_escape(edge.label)}}}"
            if edge.label
            else ""
        )
        edges.append(
            rf"\draw[->,>=stealth] ({latex_escape(edge.source)}) --{label} ({latex_escape(edge.target)});"
        )

    notes = "\\\n".join(rf"\scriptsize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{12\\baselineskip}\n"
        + _material_title(material)
        + "\\begin{center}\n"
        + "\\begin{tikzpicture}[flowbox/.style={draw,rounded corners=1pt,align=center,text width=3.7cm,minimum height=1.0cm}]\n"
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
            "\\noindent\\fbox{\\begin{minipage}{0.92\\linewidth}\n"
            + (rf"\textbf{{{meta}}}\par " if meta else "")
            + "{\\zhfont "
            + body
            + "}\n"
            + "\\end{minipage}}\\par\\vspace{0.3em}\n"
        )

    glosses = ""
    if material.glosses:
        glosses = r"\quad ".join(
            rf"\scriptsize *{latex_escape(word)}：{latex_escape(note)}"
            for word, note in material.glosses.items()
        ) + "\n"
    notes = "\\\n".join(rf"\scriptsize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{10\\baselineskip}\n"
        + _material_title(material)
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
            arrow = "draw"
        dash = ",dashed" if edge.dashed else ""
        label = (
            rf" node[midway,fill=white,inner sep=1pt] {{{latex_escape(edge.label)}}}"
            if edge.label
            else ""
        )
        edges.append(
            rf"\draw[{arrow}{dash}] ({latex_escape(edge.source)}) --{label} ({latex_escape(edge.target)});"
        )

    annotations = "\\\n".join(rf"\scriptsize {latex_escape(note)}" for note in material.annotations)
    footnotes = "\\\n".join(rf"\scriptsize {latex_escape(note)}" for note in material.footnotes)
    return (
        "\\Needspace{12\\baselineskip}\n"
        + _material_title(material)
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
    block = (
        "\\Needspace{8\\baselineskip}\n"
        + rf"\noindent {latex_escape(task.prompt_ja)}\hfill {_answer_boxes(task)}\par"
        + "\\vspace{0.35em}\n"
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
            + rf"\textbf{{{latex_escape(task.task_id)} / 正答}} {latex_escape(answers)}\par "
            + rf"\textbf{{情報依存}} {latex_escape(dependency)}\par "
            + rf"\textbf{{根拠}} {latex_escape(evidence)}\par "
            + rf"\textbf{{解説}} {latex_escape(task.rationale_ja)}\par "
            + (rf"\textbf{{誤答肢}} {distractors}" if distractors else "")
            + "\n\\end{quote}\n"
        )
    return block


def _font_setup() -> str:
    return r"""
\IfFontExistsTF{TeX Gyre Termes}
  {\setmainfont{TeX Gyre Termes}}
  {\IfFontExistsTF{Liberation Serif}
     {\setmainfont{Liberation Serif}}
     {\IfFontExistsTF{Times New Roman}
        {\setmainfont{Times New Roman}}
        {\setmainfont{Latin Modern Roman}}}}
\IfFontExistsTF{Noto Serif CJK JP}
  {\setCJKmainfont{Noto Serif CJK JP}}
  {\IfFontExistsTF{Hiragino Mincho ProN}
     {\setCJKmainfont{Hiragino Mincho ProN}}
     {\IfFontExistsTF{Songti SC}
        {\setCJKmainfont{Songti SC}}
        {\setCJKmainfont{FandolSong-Regular}}}}
\IfFontExistsTF{Noto Serif CJK SC}
  {\newCJKfontfamily\zhfont{Noto Serif CJK SC}}
  {\IfFontExistsTF{Songti SC}
     {\newCJKfontfamily\zhfont{Songti SC}}
     {\IfFontExistsTF{STSong}
        {\newCJKfontfamily\zhfont{STSong}}
        {\newcommand{\zhfont}{}}}}
"""


def render_item_tex(item: Item, out_dir: Path, teacher: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=18mm,top=16mm,bottom=18mm]{geometry}
\usepackage{fontspec}
\usepackage{xeCJK}
\usepackage{array,tabularx}
\usepackage{needspace}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{xcolor}
\pgfplotsset{compat=1.18}
"""
    tex += _font_setup()
    tex += r"""
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlength{\fboxsep}{3pt}
\newcommand{\optnum}[1]{\raisebox{0.1ex}{\textcircled{\scriptsize #1}}}
\pagestyle{plain}
\begin{document}
"""
    edition = "【教師用】" if teacher else ""
    tex += rf"\noindent\textbf{{中国語}}\hfill {edition}\par\vspace{{0.55em}}" + "\n"
    tex += rf"\noindent{{\Large\textbf{{第4問}}}}\quad 次の問い（A・B）に答えよ。（配点 60）\par" + "\n"
    tex += "\\vspace{0.35em}\\hrule\\vspace{0.85em}\n"

    for subsection in ("A", "B"):
        tasks = tasks_for_subsection(item, subsection)
        if not tasks:
            continue
        groups = task_groups(item, subsection)
        introduced: set[str] = set()
        current_qno: int | None = None

        tex += rf"\Needspace{{8\baselineskip}}\noindent{{\large\textbf{{{subsection}}}}}\quad {latex_escape(subsection_intro(item, subsection))}\par\vspace{{0.65em}}" + "\n"

        for order, kind, block in timeline(item, subsection):
            owner = block if kind == "task" else owner_task_for_order(tasks, order)
            qno = question_number(item.surface_family, subsection, owner)
            if qno != current_qno:
                tex += rf"\Needspace{{6\baselineskip}}\vspace{{0.55em}}\noindent\textbf{{問 {qno}}}\par\vspace{{0.25em}}" + "\n"
                current_qno = qno

            if owner.task_id not in introduced:
                sub_index = subquestion_index(item, owner)
                if sub_index is not None:
                    tex += rf"\noindent\textbf{{（{sub_index}）}}\par\vspace{{0.15em}}" + "\n"
                introduced.add(owner.task_id)

            if kind == "material":
                tex += _material_block(block) + "\n"
            else:
                tex += _task_block(block, teacher) + "\n"

    tex += "\\end{document}\n"
    suffix = "teacher" if teacher else "student"
    tex_path = out_dir / f"{item.item_id}.{suffix}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return tex_path


def compile_xelatex(tex_path: Path) -> Path | None:
    exe = shutil.which("xelatex")
    if not exe:
        return None
    result = subprocess.run(
        [exe, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=tex_path.parent,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        lines = result.stdout.splitlines()
        tail = "\n".join(lines[-80:])
        raise RuntimeError(f"XeLaTeX failed for {tex_path.name}:\n{tail}")
    return tex_path.with_suffix(".pdf")

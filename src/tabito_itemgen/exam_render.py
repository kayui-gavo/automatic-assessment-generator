from __future__ import annotations

import json
from pathlib import Path

from .exam_models import Q1DialogueTask, Q1PhoneticCountTask, Q1Section, Q2OrderingTask, Q2Section, Q3Section, Q5Section
from .exam_production import load_manifest, manifest_path
from .models import Item
from .presentation import owner_task_for_order, question_number, subsection_intro, subquestion_index, tasks_for_subsection, timeline
from .render import _font_setup, _material_block, _task_block, compile_xelatex, latex_escape
from .section_io import load_section


def _box(number: int) -> str:
    return rf"\fbox{{\rule{{0pt}}{{1.45em}}\hspace{{0.42em}}{number}\hspace{{0.42em}}}}"


def _options(options: list[str]) -> str:
    return "\n".join(
        rf"\noindent\optnum{{{index}}}\quad {latex_escape(option)}\par"
        for index, option in enumerate(options, start=1)
    )


def _teacher_note(title: str, body: str) -> str:
    return (
        "\\begin{quote}\\small\n"
        + rf"\textbf{{{latex_escape(title)}}} {latex_escape(body)}\par\n"
        + "\\end{quote}\n"
    )


def _section_header(number: int, label: str, score: int) -> str:
    return (
        "\\Needspace{8\\baselineskip}\n"
        + rf"\vspace{{0.8em}}\noindent{{\Large\textbf{{第{number}問}}}}"
        + rf"\quad {latex_escape(label)}\hfill （配点 {score}）\par\n"
        + "\\vspace{0.3em}\\hrule\\vspace{0.75em}\n"
    )


def _render_q1(section: Q1Section, teacher: bool) -> str:
    tex = _section_header(1, section.title_ja, 24)
    current_subsection = None
    for task in sorted(section.tasks, key=lambda value: value.answer_slot.answer_number):
        if task.subsection != current_subsection:
            tex += rf"\Needspace{{5\baselineskip}}\noindent{{\large\textbf{{{task.subsection}}}}}\par\vspace{{0.3em}}\n"
            current_subsection = task.subsection
        if isinstance(task, Q1PhoneticCountTask):
            tex += rf"\noindent {latex_escape(task.prompt_ja)}\hfill {_box(task.answer_slot.answer_number)}\par\n"
            tex += rf"\noindent\textbf{{見出し}}\quad {{\zhfont {latex_escape(task.headword.hanzi)}}} \quad {latex_escape(task.headword.pinyin)}\par\smallskip\n"
            for word in task.candidates:
                tex += rf"\noindent {latex_escape(word.label)}\quad {{\zhfont {latex_escape(word.hanzi)}}}\quad {latex_escape(word.pinyin)}\par\n"
            tex += "\\smallskip\n" + _options(task.options) + "\n"
        elif isinstance(task, Q1DialogueTask):
            tex += "\\begin{quote}\n"
            for line in task.lines:
                tex += rf"\noindent\textbf{{{latex_escape(line.speaker)}}}：{latex_escape(line.pinyin)}\par\n"
            tex += "\\end{quote}\n"
            tex += rf"\noindent {latex_escape(task.prompt_ja)}\hfill {_box(task.answer_slot.answer_number)}\par\n"
            tex += _options(task.options) + "\n"
        if teacher:
            tex += _teacher_note(
                f"正答 {task.answer_slot.answer_number}→{task.answer_slot.correct_option}",
                task.rationale_ja,
            )
    return tex


def _render_q2(section: Q2Section, teacher: bool) -> str:
    tex = _section_header(2, section.title_ja, 16)
    for task in sorted(section.tasks, key=lambda value: value.order):
        tex += rf"\Needspace{{7\baselineskip}}\noindent{{\large\textbf{{{task.subsection}}}}}\par\vspace{{0.25em}}\n"
        if isinstance(task, Q2OrderingTask):
            boxes = " \quad ".join(_box(slot.answer_number) for slot in task.answer_slots)
            tex += rf"\noindent {latex_escape(task.prompt_ja)}\hfill {boxes}\par\n"
            tex += rf"\noindent {latex_escape(task.source_ja)}\par\smallskip\n"
            tex += rf"\noindent{{\zhfont {latex_escape(task.sentence_frame_zh)}}}\par\smallskip\n"
            for token in task.token_pool:
                tex += rf"\optnum{{{token.token_id}}}\ {latex_escape(token.text_zh)}\quad "
            tex += "\\par\n"
            if teacher:
                answer = ", ".join(
                    f"{slot.answer_number}→{slot.correct_option}" for slot in task.answer_slots
                )
                tex += _teacher_note(f"正答 {answer}", task.rationale_ja)
        else:
            tex += rf"\noindent {latex_escape(task.prompt_ja)}\hfill {_box(task.answer_slot.answer_number)}\par\n"
            tex += rf"\noindent{{\zhfont {latex_escape(task.sentence_zh)}}}\par\smallskip\n"
            tex += _options(task.options) + "\n"
            if teacher:
                tex += _teacher_note(
                    f"正答 {task.answer_slot.answer_number}→{task.answer_slot.correct_option}",
                    task.rationale_ja,
                )
    return tex


def _render_q3(section: Q3Section, teacher: bool) -> str:
    tex = _section_header(3, section.title_ja, 40)
    current_subsection = None
    for task in sorted(section.tasks, key=lambda value: value.answer_slot.answer_number):
        if task.subsection != current_subsection:
            tex += rf"\Needspace{{5\baselineskip}}\noindent{{\large\textbf{{{task.subsection}}}}}\par\vspace{{0.3em}}\n"
            current_subsection = task.subsection
        tex += rf"\Needspace{{6\baselineskip}}\noindent {latex_escape(task.prompt_ja)}\hfill {_box(task.answer_slot.answer_number)}\par\n"
        tex += rf"\noindent {latex_escape(task.source_text)}\par\smallskip\n"
        tex += _options(task.options) + "\n"
        if teacher:
            tex += _teacher_note(
                f"正答 {task.answer_slot.answer_number}→{task.answer_slot.correct_option}",
                task.rationale_ja,
            )
    return tex


def _render_q4(section: Item, teacher: bool) -> str:
    tex = _section_header(4, "複合的な資料の読み取り", 60)
    for subsection in ("A", "B"):
        tasks = tasks_for_subsection(section, subsection)
        if not tasks:
            continue
        introduced: set[str] = set()
        current_qno: int | None = None
        tex += rf"\Needspace{{8\baselineskip}}\noindent{{\large\textbf{{{subsection}}}}}\quad {latex_escape(subsection_intro(section, subsection))}\par\vspace{{0.65em}}\n"
        for order, kind, block in timeline(section, subsection):
            owner = block if kind == "task" else owner_task_for_order(tasks, order)
            qno = question_number(section.surface_family, subsection, owner)
            if qno != current_qno:
                tex += rf"\Needspace{{6\baselineskip}}\vspace{{0.55em}}\noindent\textbf{{問 {qno}}}\par\vspace{{0.25em}}\n"
                current_qno = qno
            if owner.task_id not in introduced:
                sub_index = subquestion_index(section, owner)
                if sub_index is not None:
                    tex += rf"\noindent\textbf{{（{sub_index}）}}\par\vspace{{0.15em}}\n"
                introduced.add(owner.task_id)
            tex += (_material_block(block) if kind == "material" else _task_block(block, teacher)) + "\n"
    return tex


def _render_q5(section: Q5Section, teacher: bool) -> str:
    tex = _section_header(5, section.title_ja, 60)
    tex += "\\Needspace{10\\baselineskip}\n"
    for paragraph in section.paragraphs:
        tex += rf"\noindent{{\zhfont {latex_escape(paragraph.text_zh)}}}\par\vspace{{0.55em}}\n"
    tex += "\\vspace{0.4em}\n"
    for task in sorted(section.tasks, key=lambda value: value.question_no):
        boxes = " \quad ".join(_box(slot.answer_number) for slot in task.answer_slots)
        tex += rf"\Needspace{{7\baselineskip}}\noindent\textbf{{問 {task.question_no}}}\quad {latex_escape(task.prompt_ja)}\hfill {boxes}\par\n"
        tex += _options(task.options) + "\n"
        if teacher:
            answer = ", ".join(
                f"{slot.answer_number}→{slot.correct_option}" for slot in task.answer_slots
            )
            anchor_note = f" anchors={','.join(task.anchor_refs)}" if task.anchor_refs else ""
            tex += _teacher_note(f"正答 {answer}{anchor_note}", task.rationale_ja)
    return tex


def _document_preamble(title: str, teacher: bool) -> str:
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
    tex += rf"\noindent{{\Large\textbf{{{latex_escape(title)}}}}}\hfill {edition}\par\n"
    tex += "\\vspace{0.35em}\\hrule\\vspace{0.45em}\n"
    tex += "\\noindent 試験時間 80分 \quad 200点満点 \quad 解答番号 1～50\par\n"
    tex += "\\vspace{0.8em}\n"
    return tex


def _answer_key(sections: dict[str, object]) -> dict[str, int]:
    result: dict[str, int] = {}
    for section in sections.values():
        if isinstance(section, Item):
            slots = [slot for task in section.tasks for slot in task.answer_slots]
        elif isinstance(section, Q1Section):
            slots = [task.answer_slot for task in section.tasks]
        elif isinstance(section, Q2Section):
            slots = []
            for task in section.tasks:
                slots.extend(task.answer_slots if isinstance(task, Q2OrderingTask) else [task.answer_slot])
        elif isinstance(section, Q3Section):
            slots = [task.answer_slot for task in section.tasks]
        elif isinstance(section, Q5Section):
            slots = [slot for task in section.tasks for slot in task.answer_slots]
        else:
            continue
        for slot in slots:
            result[str(slot.answer_number)] = slot.correct_option
    return dict(sorted(result.items(), key=lambda item: int(item[0])))


def render_exam(root: Path, exam_id: str, *, compile_pdf: bool = False) -> dict[str, Path | None]:
    manifest_file = manifest_path(root, exam_id)
    if not manifest_file.exists():
        approved = root / "exam_bank" / "approved" / exam_id / "exam.json"
        if approved.exists():
            manifest_file = approved
        else:
            raise FileNotFoundError(f"exam {exam_id} not found")
    manifest = load_manifest(manifest_file)
    sections: dict[str, object] = {}
    for ref in manifest.sections:
        if not ref.path:
            raise ValueError(f"{ref.section} is missing")
        sections[ref.section] = load_section(manifest_file.parent / ref.path)

    out_dir = root / "output" / exam_id
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path | None] = {}
    for teacher, name in ((False, "student"), (True, "teacher")):
        tex = _document_preamble(manifest.title_ja, teacher)
        tex += _render_q1(sections["Q1"], teacher)
        tex += "\\clearpage\n" + _render_q2(sections["Q2"], teacher)
        tex += _render_q3(sections["Q3"], teacher)
        tex += "\\clearpage\n" + _render_q4(sections["Q4"], teacher)
        tex += "\\clearpage\n" + _render_q5(sections["Q5"], teacher)
        tex += "\\end{document}\n"
        tex_path = out_dir / f"{name}.tex"
        tex_path.write_text(tex, encoding="utf-8")
        outputs[f"{name}_tex"] = tex_path
        outputs[f"{name}_pdf"] = compile_xelatex(tex_path) if compile_pdf else None

    answer_key_path = out_dir / "answer_key.json"
    answer_key_path.write_text(
        json.dumps(_answer_key(sections), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    outputs["answer_key"] = answer_key_path
    return outputs

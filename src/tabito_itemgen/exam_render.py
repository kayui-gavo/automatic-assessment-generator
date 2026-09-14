from __future__ import annotations

import json
from pathlib import Path

from .answer_sheet import render_answer_sheet_tex
from .artifact_preflight import build_artifact_manifest, write_artifact_manifest
from .exam_models import (
    ArticleParagraph,
    Q1DialogueTask,
    Q1PhoneticCountTask,
    Q1Section,
    Q2OrderingTask,
    Q2Section,
    Q3Section,
    Q5Section,
)
from .exam_production import exam_fingerprint, load_manifest, manifest_path
from .exam_surface import ordering_surface_parts, q5_surface_segments, section_instruction
from .models import Item
from .presentation import (
    owner_task_for_order,
    question_number,
    subsection_intro,
    subquestion_index,
    tasks_for_subsection,
    timeline,
)
from .render import _font_setup, _material_block, _task_block, compile_xelatex, latex_escape
from .section_io import load_section


def _box(number: int) -> str:
    return rf"\fbox{{\rule{{0pt}}{{1.45em}}\hspace{{0.42em}}{number}\hspace{{0.42em}}}}"


def _tex_line(fragment: str = "") -> str:
    """Terminate one generated TeX line with a real newline character."""

    return fragment + "\n"


def _options(options: list[str], *, chinese: bool = False) -> str:
    lines: list[str] = []
    for index, option in enumerate(options, start=1):
        text = latex_escape(option)
        if chinese:
            text = r"{\zhfont " + text + "}"
        lines.append(rf"\noindent\optnum{{{index}}}\quad {text}\par")
    return "\n".join(lines)


def _ordering_frame(task: Q2OrderingTask) -> str:
    fragments: list[str] = []
    for part in ordering_surface_parts(task):
        if part.answer_number is not None:
            fragments.append(_box(part.answer_number))
        elif part.text:
            fragments.append(latex_escape(part.text))
        else:
            fragments.append(r"\underline{\hspace{4.0em}}")
    return "".join(fragments)


def _breakable_underline(source: str, *, chunk_size: int = 10) -> str:
    """Underline CJK prose while leaving legal line-break opportunities."""

    chunks = [source[index : index + chunk_size] for index in range(0, len(source), chunk_size)]
    return r"\allowbreak{}".join(rf"\uline{{{latex_escape(chunk)}}}" for chunk in chunks)


def _q1_word_surface(word, *, underline_target: bool) -> str:
    """Render only the Hanzi shown to candidates; pinyin remains authoring metadata.

    Official Q1 A/B underlines one target character inside a lexical item. The
    target_index field is 1-based. Legacy one-character fixtures without an
    explicit target remain renderable by underlining that sole character.
    """

    if not underline_target:
        return latex_escape(word.hanzi)
    target_index = word.target_index
    if target_index is None and len(word.hanzi) == 1:
        target_index = 1
    if target_index is None:
        return latex_escape(word.hanzi)
    index = target_index - 1
    return (
        latex_escape(word.hanzi[:index])
        + rf"\uline{{{latex_escape(word.hanzi[index])}}}"
        + latex_escape(word.hanzi[index + 1 :])
    )


def _q5_paragraph_text(section: Q5Section, paragraph: ArticleParagraph) -> str:
    fragments: list[str] = []
    for segment in q5_surface_segments(section, paragraph):
        if segment.kind == "marker":
            fragments.append(rf"{{\small\textbf{{{latex_escape(segment.text)}}}}}")
        elif segment.kind == "blank":
            fragments.append(r"\,\underline{\hspace{4.2em}}")
        elif segment.kind == "underline":
            fragments.append(_breakable_underline(segment.text))
        else:
            fragments.append(latex_escape(segment.text))
    return "".join(fragments)


def _teacher_note(title: str, body: str) -> str:
    return (
        _tex_line(r"\begin{quote}\small")
        + _tex_line(rf"\textbf{{{latex_escape(title)}}} {latex_escape(body)}\par")
        + _tex_line(r"\end{quote}")
    )


def _section_header(number: int, score: int) -> str:
    instruction = section_instruction(number)
    return (
        _tex_line(r"\Needspace{8\baselineskip}")
        + _tex_line(
            rf"\vspace{{0.8em}}\noindent{{\Large\textbf{{第{number}問}}}}"
            rf"\quad {latex_escape(instruction)}\hfill （配点 {score}）\par"
        )
        + _tex_line(r"\vspace{0.3em}\hrule\vspace{0.75em}")
    )


def _render_q1(section: Q1Section, teacher: bool) -> str:
    tex = _section_header(1, 24)
    current_subsection = None
    for task in sorted(section.tasks, key=lambda value: value.answer_slot.answer_number):
        if task.subsection != current_subsection:
            tex += _tex_line(
                rf"\Needspace{{5\baselineskip}}\noindent{{\large\textbf{{{task.subsection}}}}}"
                r"\par\vspace{0.3em}"
            )
            current_subsection = task.subsection
        tex += _tex_line(r"\Needspace{14\baselineskip}")
        if isinstance(task, Q1PhoneticCountTask):
            tex += _tex_line(
                rf"\noindent {latex_escape(task.prompt_ja)}\hfill "
                rf"{_box(task.answer_slot.answer_number)}\par"
            )
            underline_target = task.target in {"initial", "final"}
            tex += _tex_line(
                rf"\noindent\textbf{{見出し}}\quad {{\zhfont {_q1_word_surface(task.headword, underline_target=underline_target)}}}"
                r"\par\smallskip"
            )
            for word in task.candidates:
                tex += _tex_line(
                    rf"\noindent {latex_escape(word.label)}\quad "
                    rf"{{\zhfont {_q1_word_surface(word, underline_target=underline_target)}}}\par"
                )
            tex += _tex_line(r"\smallskip") + _options(task.options) + "\n"
        elif isinstance(task, Q1DialogueTask):
            tex += _tex_line(r"\begin{quote}")
            for line in task.lines:
                tex += _tex_line(
                    rf"\noindent\textbf{{{latex_escape(line.speaker)}}}：{latex_escape(line.pinyin)}\par"
                )
            tex += _tex_line(r"\end{quote}")
            tex += _tex_line(
                rf"\noindent {latex_escape(task.prompt_ja)}\hfill "
                rf"{_box(task.answer_slot.answer_number)}\par"
            )
            tex += _options(task.options) + "\n"
        if teacher:
            tex += _teacher_note(
                f"正答 {task.answer_slot.answer_number}→{task.answer_slot.correct_option}",
                task.rationale_ja,
            )
    return tex


def _render_q2(section: Q2Section, teacher: bool) -> str:
    tex = _section_header(2, 16)
    current_subsection = None
    for task in sorted(section.tasks, key=lambda value: value.order):
        if task.subsection != current_subsection:
            tex += _tex_line(
                rf"\Needspace{{7\baselineskip}}\noindent{{\large\textbf{{{task.subsection}}}}}"
                r"\par\vspace{0.25em}"
            )
            current_subsection = task.subsection
        tex += _tex_line(r"\Needspace{8\baselineskip}")
        if isinstance(task, Q2OrderingTask):
            tex += _tex_line(rf"\noindent {latex_escape(task.prompt_ja)}\par")
            tex += _tex_line(rf"\noindent {latex_escape(task.source_ja)}\par\smallskip")
            tex += _tex_line(rf"\noindent{{\zhfont {_ordering_frame(task)}}}\par\smallskip")
            for index, token in enumerate(task.token_pool, start=1):
                tex += rf"\optnum{{{token.token_id}}}\ {{\zhfont {latex_escape(token.text_zh)}}}\quad "
                if index == 4:
                    tex += _tex_line(r"\par\smallskip")
            tex += _tex_line(r"\par")
            if teacher:
                answer = ", ".join(
                    f"第{position}空欄 ({slot.answer_number})→{slot.correct_option}"
                    for position, slot in zip(task.answer_positions, task.answer_slots, strict=True)
                )
                tex += _teacher_note(f"正答 {answer}", task.rationale_ja)
        else:
            tex += _tex_line(
                rf"\noindent {latex_escape(task.prompt_ja)}\hfill "
                rf"{_box(task.answer_slot.answer_number)}\par"
            )
            tex += _tex_line(rf"\noindent{{\zhfont {latex_escape(task.sentence_zh)}}}\par\smallskip")
            tex += _options(task.options, chinese=True) + "\n"
            if teacher:
                tex += _teacher_note(
                    f"正答 {task.answer_slot.answer_number}→{task.answer_slot.correct_option}",
                    task.rationale_ja,
                )
    return tex


def _render_q3(section: Q3Section, teacher: bool) -> str:
    tex = _section_header(3, 40)
    current_subsection = None
    for task in sorted(section.tasks, key=lambda value: value.answer_slot.answer_number):
        if task.subsection != current_subsection:
            tex += _tex_line(
                rf"\Needspace{{5\baselineskip}}\noindent{{\large\textbf{{{task.subsection}}}}}"
                r"\par\vspace{0.3em}"
            )
            current_subsection = task.subsection
        tex += _tex_line(
            rf"\Needspace{{6\baselineskip}}\noindent {latex_escape(task.prompt_ja)}\hfill "
            rf"{_box(task.answer_slot.answer_number)}\par"
        )
        tex += _tex_line(rf"\noindent {latex_escape(task.source_text)}\par\smallskip")
        tex += _options(task.options) + "\n"
        if teacher:
            tex += _teacher_note(
                f"正答 {task.answer_slot.answer_number}→{task.answer_slot.correct_option}",
                task.rationale_ja,
            )
    return tex


def _print_safe_q4(section: Item) -> Item:
    """Normalize symbols that are unreliable in the Latin fallback font."""

    return Item.model_validate_json(section.model_dump_json().replace("℃", "°C"))


def _render_q4(section: Item, teacher: bool) -> str:
    section = _print_safe_q4(section)
    tex = _section_header(4, 60)
    for subsection in ("A", "B"):
        tasks = tasks_for_subsection(section, subsection)
        if not tasks:
            continue
        introduced: set[str] = set()
        current_qno: int | None = None
        tex += _tex_line(
            rf"\Needspace{{8\baselineskip}}\noindent{{\large\textbf{{{subsection}}}}}"
            rf"\quad {latex_escape(subsection_intro(section, subsection))}\par\vspace{{0.65em}}"
        )
        for order, kind, block in timeline(section, subsection):
            owner = block if kind == "task" else owner_task_for_order(tasks, order)
            qno = question_number(section.surface_family, subsection, owner)
            if qno != current_qno:
                tex += _tex_line(
                    rf"\Needspace{{18\baselineskip}}\vspace{{0.55em}}\noindent"
                    rf"\textbf{{問 {qno}}}\par\vspace{{0.25em}}"
                )
                current_qno = qno
            if owner.task_id not in introduced:
                sub_index = subquestion_index(section, owner)
                if sub_index is not None:
                    tex += _tex_line(r"\Needspace{14\baselineskip}")
                    tex += _tex_line(
                        rf"\noindent\textbf{{（{sub_index}）}}\par\vspace{{0.15em}}"
                    )
                introduced.add(owner.task_id)
            tex += (_material_block(block) if kind == "material" else _task_block(block, teacher)) + "\n"
    return tex


def _render_q5(section: Q5Section, teacher: bool) -> str:
    tex = _section_header(5, 60)
    tex += _tex_line(r"\Needspace{10\baselineskip}")
    for paragraph in section.paragraphs:
        tex += _tex_line(
            rf"\noindent{{\zhfont {_q5_paragraph_text(section, paragraph)}}}\par\vspace{{0.55em}}"
        )

    tex += _tex_line(r"\clearpage")
    for task in sorted(section.tasks, key=lambda value: value.question_no):
        if task.question_no == 7:
            tex += _tex_line(r"\clearpage")
        boxes = r" \quad ".join(_box(slot.answer_number) for slot in task.answer_slots)
        tex += _tex_line(
            rf"\Needspace{{7\baselineskip}}\noindent\textbf{{問 {task.question_no}}}\quad "
            rf"{latex_escape(task.prompt_ja)}\hfill {boxes}\par"
        )
        chinese_options = task.operation in {"lexical_choice", "discourse_connector", "sentence_choice"}
        tex += _options(task.options, chinese=chinese_options) + "\n"
        if teacher:
            answer = ", ".join(
                f"{slot.answer_number}→{slot.correct_option}" for slot in task.answer_slots
            )
            anchor_note = f" 参照={','.join(task.anchor_refs)}" if task.anchor_refs else ""
            tex += _teacher_note(f"正答 {answer}{anchor_note}", task.rationale_ja)
    return tex


def _document_preamble(title: str, teacher: bool) -> str:
    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=18mm,top=16mm,bottom=18mm]{geometry}
\usepackage{fontspec}
\usepackage{xeCJK}
\usepackage{array,tabularx}
\usepackage{needspace}
\usepackage[normalem]{ulem}
\usepackage{tikz}
\usepackage{pgfplots}
\usepackage{xcolor}
\pgfplotsset{compat=1.18}
\pgfplotsset{xbar/.append style={y tick label style={text width=2.6cm,align=right}}}
"""
    tex += _font_setup()
    if teacher:
        tex += r"""
\IfFontExistsTF{Noto Serif CJK JP}
  {\setmainfont{Noto Serif CJK JP}}
  {}
"""
    tex += r"""
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlength{\fboxsep}{3pt}
\newcommand{\optnum}[1]{\raisebox{0.1ex}{\textcircled{\scriptsize #1}}}
\pagestyle{plain}
\begin{document}
"""
    edition = "【教師用】" if teacher else ""
    tex += _tex_line(rf"\noindent{{\Large\textbf{{{latex_escape(title)}}}}}\hfill {edition}\par")
    tex += _tex_line(r"\vspace{0.35em}\hrule\vspace{0.45em}")
    tex += _tex_line(r"\noindent 試験時間 80分 \quad 200点満点 \quad 解答番号 1～50\par")
    tex += _tex_line(r"\vspace{0.8em}")
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
    draft_manifest = manifest_file.exists()
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
        tex += _tex_line(r"\clearpage") + _render_q2(sections["Q2"], teacher)
        tex += _tex_line(r"\clearpage") + _render_q3(sections["Q3"], teacher)
        tex += _tex_line(r"\clearpage") + _render_q4(sections["Q4"], teacher)
        tex += _tex_line(r"\clearpage") + _render_q5(sections["Q5"], teacher)
        tex += _tex_line(r"\end{document}")
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

    answer_sheet = render_answer_sheet_tex(root, exam_id, compile_pdf=compile_pdf)
    outputs.update(answer_sheet)

    if compile_pdf and draft_manifest:
        artifact = build_artifact_manifest(
            root=root,
            exam_id=exam_id,
            exam_fingerprint=exam_fingerprint(root, exam_id),
            out_dir=out_dir,
        )
        artifact_path = write_artifact_manifest(artifact, out_dir / "artifact_manifest.json")
        outputs["artifact_manifest"] = artifact_path
        if not artifact.passed:
            details = [
                f"{check.name}: {'; '.join(check.errors)}"
                for check in artifact.checks
                if not check.passed
            ]
            raise RuntimeError("PDF artifact preflight failed: " + " | ".join(details))
    else:
        outputs["artifact_manifest"] = None

    return outputs

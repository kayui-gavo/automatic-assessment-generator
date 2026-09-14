from __future__ import annotations

import json
from pathlib import Path

from .exam_models import Q1Section, Q2OrderingTask, Q2Section, Q3Section, Q5Section
from .exam_production import load_manifest, manifest_path
from .models import Item
from .render import _font_setup, compile_xelatex, latex_escape
from .scoring import scoring_scheme
from .section_io import load_section


def _resolve_manifest(root: Path, exam_id: str) -> Path:
    draft = manifest_path(root, exam_id)
    if draft.exists():
        return draft
    approved = root / "exam_bank" / "approved" / exam_id / "exam.json"
    if approved.exists():
        return approved
    raise FileNotFoundError(f"exam {exam_id} not found")


def answer_option_counts(sections: dict[str, object]) -> dict[int, int]:
    """Return the number of markable choices for every answer number."""

    result: dict[int, int] = {}
    for section in sections.values():
        if isinstance(section, Q1Section):
            for task in section.tasks:
                result[task.answer_slot.answer_number] = len(task.options)
        elif isinstance(section, Q2Section):
            for task in section.tasks:
                if isinstance(task, Q2OrderingTask):
                    for slot in task.answer_slots:
                        result[slot.answer_number] = len(task.token_pool)
                else:
                    result[task.answer_slot.answer_number] = len(task.options)
        elif isinstance(section, Q3Section):
            for task in section.tasks:
                result[task.answer_slot.answer_number] = len(task.options)
        elif isinstance(section, Item):
            for task in section.tasks:
                for slot in task.answer_slots:
                    result[slot.answer_number] = len(task.options)
        elif isinstance(section, Q5Section):
            for task in section.tasks:
                for slot in task.answer_slots:
                    result[slot.answer_number] = len(task.options)
    if sorted(result) != list(range(1, 51)):
        raise ValueError("answer sheet requires option counts for answer numbers 1 through 50")
    return result


def _mark(number: int) -> str:
    return rf"\textcircled{{\scriptsize {number}}}"


def _row(number: int, option_count: int) -> str:
    marks = r"\hspace{0.38em}".join(_mark(option) for option in range(1, option_count + 1))
    return (
        rf"\noindent\textbf{{{number:02d}}}\hspace{{0.8em}}"
        rf"{{\small {marks}}}\par\vspace{{0.20em}}"
    )


def render_answer_sheet_tex(
    root: Path,
    exam_id: str,
    *,
    compile_pdf: bool = False,
) -> dict[str, Path | None]:
    manifest_file = _resolve_manifest(root, exam_id)
    manifest = load_manifest(manifest_file)
    sections: dict[str, object] = {}
    for ref in manifest.sections:
        if not ref.path:
            raise ValueError(f"{ref.section} is missing")
        sections[ref.section] = load_section(manifest_file.parent / ref.path)

    counts = answer_option_counts(sections)
    out_dir = root / "output" / exam_id
    out_dir.mkdir(parents=True, exist_ok=True)

    tex = r"""\documentclass[10pt,a4paper]{article}
\usepackage[margin=16mm,top=14mm,bottom=14mm]{geometry}
\usepackage{fontspec}
\usepackage{xeCJK}
\usepackage{multicol}
\usepackage{array}
\usepackage{needspace}
"""
    tex += _font_setup()
    tex += r"""
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlength{\columnsep}{1.8em}
\pagestyle{empty}
\begin{document}
"""
    tex += rf"\noindent{{\Large\textbf{{{latex_escape(manifest.title_ja)}　解答用紙}}}}\par\vspace{{0.35em}}" + "\n"
    tex += r"\noindent 氏名：\underline{\hspace{12em}}\hfill 得点：\underline{\hspace{4em}} / 200\par" + "\n"
    tex += r"\vspace{0.45em}\hrule\vspace{0.6em}" + "\n"
    tex += r"\begin{multicols}{2}\raggedcolumns" + "\n"

    ranges = {
        "第1問": range(1, 7),
        "第2問": range(7, 13),
        "第3問": range(13, 21),
        "第4問": range(21, 37),
        "第5問": range(37, 51),
    }
    for label, numbers in ranges.items():
        tex += rf"\Needspace{{5\baselineskip}}\noindent\textbf{{{label}}}\par\smallskip" + "\n"
        for number in numbers:
            tex += _row(number, counts[number]) + "\n"
        tex += r"\vspace{0.35em}" + "\n"

    tex += r"\end{multicols}" + "\n"
    tex += r"\vfill\hrule\vspace{0.3em}" + "\n"
    tex += r"{\small ※ 解答番号ごとに一つだけマークすること。複数解答を求める設問は、指定された各解答番号に一つずつマークする。}" + "\n"
    tex += r"\end{document}" + "\n"

    tex_path = out_dir / "answer_sheet.tex"
    tex_path.write_text(tex, encoding="utf-8")
    pdf_path = compile_xelatex(tex_path) if compile_pdf else None

    scheme_path = out_dir / "scoring_scheme.json"
    scheme_path.write_text(
        json.dumps(scoring_scheme(manifest.exam_family).model_dump(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "answer_sheet_tex": tex_path,
        "answer_sheet_pdf": pdf_path,
        "scoring_scheme": scheme_path,
    }

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .models import Item


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
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _material_block(item: Item) -> str:
    out: list[str] = []
    for m in item.materials:
        title = f"\\textbf{{{latex_escape(m.title)}}}\\par\n" if m.title else ""
        content = latex_escape(m.content).replace("\n", "\\par\n")
        out.append(
            "\\begin{tcolorbox}[title={" + latex_escape(m.material_id) + "}]\n"
            + title
            + content
            + "\n\\end{tcolorbox}\n"
        )
    return "\n".join(out)


def render_item_tex(item: Item, out_dir: Path, teacher: bool = False) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    questions: list[str] = []
    for q in item.questions:
        opts = "\n".join(
            f"\\item {latex_escape(option)}" for option in q.options
        )
        block = (
            f"\\subsection*{{{latex_escape(q.question_id)}}}\n"
            f"{latex_escape(q.prompt_ja)}\n"
            "\\begin{enumerate}\n"
            f"{opts}\n"
            "\\end{enumerate}\n"
        )
        if teacher:
            block += (
                f"\\textbf{{正答：{q.correct_option}}}\\par\n"
                f"\\textbf{{解説：}}{latex_escape(q.rationale_ja)}\\par\n"
            )
        questions.append(block)

    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=18mm]{geometry}
\usepackage{fontspec}
\usepackage{xeCJK}
\usepackage[most]{tcolorbox}
\usepackage{enumitem}
\setmainfont{TeX Gyre Termes}
\setCJKmainfont{Noto Serif CJK JP}
\setlist[enumerate]{label=\arabic*.,leftmargin=2em}
\begin{document}
"""
    tex += f"\\section*{{共通テスト中国語 Q4 候補問題 — {latex_escape(item.title_ja)}}}\n"
    tex += _material_block(item)
    tex += "\n" + "\n".join(questions)
    tex += "\n\\end{document}\n"

    suffix = "teacher" if teacher else "student"
    tex_path = out_dir / f"{item.item_id}.{suffix}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    return tex_path


def compile_xelatex(tex_path: Path) -> Path | None:
    exe = shutil.which("xelatex")
    if not exe:
        return None
    subprocess.run(
        [exe, "-interaction=nonstopmode", tex_path.name],
        cwd=tex_path.parent,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    return tex_path.with_suffix(".pdf")

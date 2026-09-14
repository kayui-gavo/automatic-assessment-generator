from __future__ import annotations

import html

import streamlit as st

from .exam_models import Q1Section, Q2OrderingTask, Q2Section, Q3Section, Q5Section
from .exam_surface import ordering_surface_parts, q5_surface_segments, section_instruction

OPTION_MARKS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]


def _answer_badge(number: int) -> str:
    return f'<span class="answer-badge">{number}</span>'


def _q1_hanzi_html(word, *, underline_target: bool) -> str:
    escaped = html.escape(word.hanzi)
    if not underline_target:
        return escaped
    target_index = word.target_index
    if target_index is None and len(word.hanzi) == 1:
        target_index = 1
    if target_index is None:
        return escaped
    index = target_index - 1
    return (
        html.escape(word.hanzi[:index])
        + f'<span style="text-decoration:underline;text-underline-offset:3px">'
        + html.escape(word.hanzi[index])
        + "</span>"
        + html.escape(word.hanzi[index + 1 :])
    )


def _options(options: list[str]) -> None:
    rows = []
    for index, option in enumerate(options, start=1):
        mark = OPTION_MARKS[index - 1] if index <= len(OPTION_MARKS) else f"({index})"
        rows.append(
            '<div class="option-row">'
            f'<div class="option-mark">{mark}</div>'
            f'<div>{html.escape(option)}</div>'
            '</div>'
        )
    st.markdown(f'<div class="option-list">{"".join(rows)}</div>', unsafe_allow_html=True)


def _official_header(section) -> None:
    number = int(section.section[1])
    st.markdown(
        '<div class="exam-header exam-title">'
        f'<b>第{number}問</b>　{html.escape(section_instruction(number))}'
        f'<span style="float:right">（配点 {section.score}）</span>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="exam-rule"></div>', unsafe_allow_html=True)


def _ordering_html(task: Q2OrderingTask) -> str:
    # ordering_surface_parts represents an unasked blank with answer_number=None
    # and empty text.  Materialize those entries as visible underlines.
    result: list[str] = []
    for part in ordering_surface_parts(task):
        if part.answer_number is not None:
            result.append(_answer_badge(part.answer_number))
        elif part.text:
            result.append(html.escape(part.text))
        else:
            result.append(
                '<span style="display:inline-block;min-width:5em;'
                'border-bottom:1px solid #333">&nbsp;</span>'
            )
    return "".join(result)


def _q5_paragraph_html(section: Q5Section, paragraph) -> str:
    parts: list[str] = []
    for segment in q5_surface_segments(section, paragraph):
        escaped = html.escape(segment.text)
        if segment.kind == "marker":
            parts.append(f'<span class="anchor-marker"><b>{escaped}</b></span>')
        elif segment.kind == "blank":
            parts.append(
                '<span style="display:inline-block;min-width:5em;'
                'border-bottom:1.5px solid #222;margin:0 .15em">&nbsp;</span>'
            )
        elif segment.kind == "underline":
            parts.append(
                f'<span style="text-decoration:underline;text-underline-offset:3px">{escaped}</span>'
            )
        else:
            parts.append(escaped)
    return "".join(parts)


def render_simple_section_preview(section, teacher: bool = False) -> None:
    """Render Q1/Q2/Q3/Q5 using the same surface semantics as the PDF booklet."""

    _official_header(section)

    if isinstance(section, Q1Section):
        current = None
        for task in sorted(section.tasks, key=lambda value: value.answer_slot.answer_number):
            if task.subsection != current:
                st.markdown(
                    f'<div class="exam-section">{task.subsection}</div>',
                    unsafe_allow_html=True,
                )
                current = task.subsection
            if hasattr(task, "headword"):
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(task.prompt_ja)} '
                    f'{_answer_badge(task.answer_slot.answer_number)}</div>',
                    unsafe_allow_html=True,
                )
                underline_target = task.target in {"initial", "final"}
                headword = _q1_hanzi_html(task.headword, underline_target=underline_target)
                st.markdown(
                    f'<div class="q1-word"><b>見出し</b>　{headword}</div>',
                    unsafe_allow_html=True,
                )
                candidates = "".join(
                    '<span class="q1-choice">'
                    f'<b>{html.escape(word.label)}</b>　'
                    f'{_q1_hanzi_html(word, underline_target=underline_target)}'
                    '</span>'
                    for word in task.candidates
                )
                st.markdown(
                    f'<div class="q1-choice-row">{candidates}</div>',
                    unsafe_allow_html=True,
                )
            else:
                # Q1-D is intentionally pinyin-only on the student surface.
                for line in task.lines:
                    st.markdown(f"**{line.speaker}**：{line.pinyin}")
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(task.prompt_ja)} '
                    f'{_answer_badge(task.answer_slot.answer_number)}</div>',
                    unsafe_allow_html=True,
                )
            _options(task.options)
            if teacher:
                st.caption(
                    f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option} · "
                    f"{task.rationale_ja}"
                )
        return

    if isinstance(section, Q2Section):
        current = None
        for task in sorted(section.tasks, key=lambda value: value.order):
            if task.subsection != current:
                st.markdown(
                    f'<div class="exam-section">{task.subsection}</div>',
                    unsafe_allow_html=True,
                )
                current = task.subsection
            if isinstance(task, Q2OrderingTask):
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(task.prompt_ja)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(html.escape(task.source_ja))
                st.markdown(
                    f'<div class="source-text">{_ordering_html(task)}</div>',
                    unsafe_allow_html=True,
                )
                token_text = "　".join(
                    f"{OPTION_MARKS[token.token_id - 1]} {html.escape(token.text_zh)}"
                    for token in task.token_pool
                )
                st.markdown(token_text, unsafe_allow_html=True)
                if teacher:
                    answer = " / ".join(
                        f"[{slot.answer_number}] {slot.correct_option}" for slot in task.answer_slots
                    )
                    st.caption(f"正答 {answer} · {task.rationale_ja}")
            else:
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(task.prompt_ja)} '
                    f'{_answer_badge(task.answer_slot.answer_number)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(task.sentence_zh)
                _options(task.options)
                if teacher:
                    st.caption(
                        f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option} · "
                        f"{task.rationale_ja}"
                    )
        return

    if isinstance(section, Q3Section):
        current = None
        for task in sorted(section.tasks, key=lambda value: value.answer_slot.answer_number):
            if task.subsection != current:
                st.markdown(
                    f'<div class="exam-section">{task.subsection}</div>',
                    unsafe_allow_html=True,
                )
                current = task.subsection
            st.markdown(
                f'<div class="exam-prompt">{html.escape(task.prompt_ja)} '
                f'{_answer_badge(task.answer_slot.answer_number)}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(task.source_text)
            _options(task.options)
            if teacher:
                st.caption(
                    f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option} · "
                    f"{task.rationale_ja}"
                )
                for option, reasons in task.distractor_error_types.items():
                    detail = task.distractor_rationales_ja.get(option, "")
                    st.caption(f"誤答 {option} · {' / '.join(reasons)} · {detail}")
        return

    if isinstance(section, Q5Section):
        for paragraph in section.paragraphs:
            st.markdown(
                f'<div class="source-text">{_q5_paragraph_html(section, paragraph)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("---")
        for task in sorted(section.tasks, key=lambda value: value.question_no):
            badges = "".join(_answer_badge(slot.answer_number) for slot in task.answer_slots)
            st.markdown(
                f'<div class="exam-question">問 {task.question_no}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="exam-prompt">{html.escape(task.prompt_ja)} {badges}</div>',
                unsafe_allow_html=True,
            )
            _options(task.options)
            if teacher:
                answer = " / ".join(
                    f"[{slot.answer_number}] {slot.correct_option}" for slot in task.answer_slots
                )
                st.caption(f"正答 {answer} · {task.rationale_ja}")
                if task.anchor_refs:
                    st.caption("参照 anchor · " + " / ".join(task.anchor_refs))

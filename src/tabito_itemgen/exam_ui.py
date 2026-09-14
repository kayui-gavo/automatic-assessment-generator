from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from tabito_itemgen.exam_generate import (
    create_all_section_requests,
    create_exam_section_request,
    create_section_review_request,
    create_section_revision_request,
)
from tabito_itemgen.exam_models import (
    ExamHumanQA,
    ExamQAChecks,
    ExamQATiming,
    Q1Section,
    Q2OrderingTask,
    Q2Section,
    Q3Section,
    Q5Section,
)
from tabito_itemgen.exam_production import (
    approve_exam,
    create_exam_project,
    exam_qa_path,
    exam_release_readiness,
    import_section_response,
    import_section_review,
    load_manifest,
    save_exam_human_qa,
    save_section_human_qa,
    section_qa_path,
    section_release_readiness,
)
from tabito_itemgen.exam_render import render_exam
from tabito_itemgen.exam_review_models import (
    SECTION_SPECIFIC_QA,
    SectionHumanQA,
    SectionQAChecks,
    SectionQATiming,
)
from tabito_itemgen.exam_validation import validate_exam, validate_section_file
from tabito_itemgen.io import load_json
from tabito_itemgen.model_policy import MIN_REASONING_LEVEL, PREFERRED_MODEL
from tabito_itemgen.models import Item
from tabito_itemgen.paths import find_project_root
from tabito_itemgen.section_io import load_section, section_fingerprint
from tabito_itemgen.ui_app import (
    APP_CSS,
    OPTION_MARKS,
    _render_booklet_preview,
    _render_teacher_view,
)

SECTION_LABELS = {
    "Q1": "発音・ピンイン",
    "Q2": "語句",
    "Q3": "表現力",
    "Q4": "複合的な資料の読み取り",
    "Q5": "長文読解",
}


def _root() -> Path:
    try:
        return find_project_root()
    except RuntimeError:
        return Path.cwd()


def _discover_exams(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for state in ("draft", "approved"):
        directory = root / "exam_bank" / state
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*/exam.json"), reverse=True):
            try:
                manifest = load_manifest(path)
            except Exception:
                continue
            result[f"{state.upper()} · {manifest.title_ja} · {manifest.exam_id}"] = path
    return result


def _section_path(exam_path: Path, ref) -> Path | None:
    return exam_path.parent / ref.path if ref.path else None


def _section_status(root: Path, manifest, exam_path: Path, ref) -> str:
    path = _section_path(exam_path, ref)
    if path is None or not path.exists():
        return "未生成"
    if not validate_section_file(path).passed:
        return "结构修正"
    if "approved" in exam_path.parts:
        return "Approved"
    try:
        readiness = section_release_readiness(root, manifest.exam_id, ref.section)
    except Exception:
        return "Draft"
    if readiness.ready:
        return "Ready"
    blind = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
    return "Human QA" if blind and blind.passed else "Blind Review"


def _answer_badge(number: int) -> str:
    return f'<span class="answer-badge">{number}</span>'


def _html_options(options: list[str]) -> None:
    rows = []
    for index, option in enumerate(options, start=1):
        mark = OPTION_MARKS[index - 1] if index <= len(OPTION_MARKS) else f"({index})"
        rows.append(
            f'<div class="option-row"><div class="option-mark">{mark}</div>'
            f'<div>{html.escape(option)}</div></div>'
        )
    st.markdown(f'<div class="option-list">{"".join(rows)}</div>', unsafe_allow_html=True)


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
        + f"<u>{html.escape(word.hanzi[index])}</u>"
        + html.escape(word.hanzi[index + 1 :])
    )


def _preview_simple_section(section, teacher: bool = False) -> None:
    """Fallback preview used when the dedicated preview module is not injected."""

    st.markdown(f"### 第{section.section[1]}問　{section.title_ja}")
    if isinstance(section, Q1Section):
        current = None
        for task in sorted(section.tasks, key=lambda value: value.answer_slot.answer_number):
            if task.subsection != current:
                st.markdown(f"**{task.subsection}**")
                current = task.subsection
            if hasattr(task, "headword"):
                st.markdown(
                    f"{task.prompt_ja} {_answer_badge(task.answer_slot.answer_number)}",
                    unsafe_allow_html=True,
                )
                underline_target = task.target in {"initial", "final"}
                st.markdown(
                    "見出し　" + _q1_hanzi_html(task.headword, underline_target=underline_target),
                    unsafe_allow_html=True,
                )
                words = "　".join(
                    f"{word.label} {_q1_hanzi_html(word, underline_target=underline_target)}"
                    for word in task.candidates
                )
                st.markdown(words, unsafe_allow_html=True)
            else:
                for line in task.lines:
                    st.markdown(f"**{line.speaker}**：{line.pinyin}")
                st.markdown(
                    f"{task.prompt_ja} {_answer_badge(task.answer_slot.answer_number)}",
                    unsafe_allow_html=True,
                )
            _html_options(task.options)
            if teacher:
                st.caption(
                    f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option} · "
                    f"{task.rationale_ja}"
                )
        return

    if isinstance(section, Q2Section):
        for task in sorted(section.tasks, key=lambda value: value.order):
            st.markdown(f"**{task.subsection}**")
            if isinstance(task, Q2OrderingTask):
                badges = "".join(_answer_badge(slot.answer_number) for slot in task.answer_slots)
                st.markdown(f"{task.prompt_ja} {badges}", unsafe_allow_html=True)
                st.markdown(task.source_ja)
                st.markdown(task.sentence_frame_zh)
                st.markdown(
                    "　".join(
                        f"{OPTION_MARKS[token.token_id - 1]} {token.text_zh}"
                        for token in task.token_pool
                    )
                )
                if teacher:
                    answers = " / ".join(
                        f"[{slot.answer_number}] {slot.correct_option}" for slot in task.answer_slots
                    )
                    st.caption(f"正答 {answers} · {task.rationale_ja}")
            else:
                st.markdown(
                    f"{task.prompt_ja} {_answer_badge(task.answer_slot.answer_number)}",
                    unsafe_allow_html=True,
                )
                st.markdown(task.sentence_zh)
                _html_options(task.options)
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
                st.markdown(f"**{task.subsection}**")
                current = task.subsection
            st.markdown(
                f"{task.prompt_ja} {_answer_badge(task.answer_slot.answer_number)}",
                unsafe_allow_html=True,
            )
            st.markdown(task.source_text)
            _html_options(task.options)
            if teacher:
                st.caption(
                    f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option} · "
                    f"{task.rationale_ja}"
                )
        return

    if isinstance(section, Q5Section):
        for paragraph in section.paragraphs:
            st.markdown(paragraph.text_zh)
        st.divider()
        for task in sorted(section.tasks, key=lambda value: value.question_no):
            badges = "".join(_answer_badge(slot.answer_number) for slot in task.answer_slots)
            st.markdown(f"**問 {task.question_no}**　{task.prompt_ja} {badges}", unsafe_allow_html=True)
            _html_options(task.options)
            if teacher:
                answers = " / ".join(
                    f"[{slot.answer_number}] {slot.correct_option}" for slot in task.answer_slots
                )
                st.caption(f"正答 {answers} · {task.rationale_ja}")


def _render_section_preview(section, teacher: bool) -> None:
    if isinstance(section, Item):
        _render_teacher_view(section) if teacher else _render_booklet_preview(section)
    else:
        _preview_simple_section(section, teacher=teacher)


def _existing_section_qa(root: Path, exam_id: str, section_name: str, fingerprint: str):
    path = section_qa_path(root, exam_id, section_name)
    if not path.exists():
        return None
    try:
        qa = SectionHumanQA.model_validate(load_json(path))
    except Exception:
        return None
    return qa if qa.candidate_fingerprint == fingerprint else None


def _section_human_qa_form(root: Path, manifest, ref, section) -> None:
    fingerprint = section_fingerprint(section)
    existing = _existing_section_qa(root, manifest.exam_id, ref.section, fingerprint)

    st.markdown("#### Human QA")
    common_values = {}
    for field in SectionQAChecks.model_fields:
        common_values[field] = st.checkbox(
            field.replace("_", " "),
            value=bool(getattr(existing.checks, field)) if existing else False,
            key=f"qa-{ref.section}-{field}-{fingerprint[:8]}",
        )

    with st.expander("大题专项检查"):
        specific = {}
        for field in SECTION_SPECIFIC_QA[ref.section]:
            specific[field] = st.checkbox(
                field.replace("_", " "),
                value=bool(existing.section_specific_checks.get(field, False)) if existing else False,
                key=f"qas-{ref.section}-{field}-{fingerprint[:8]}",
            )

    reviewer = st.text_input(
        "审题人",
        value=existing.reviewer if existing else "TABITO 教研",
        key=f"reviewer-{ref.section}-{fingerprint[:8]}",
    )
    disposition = st.selectbox(
        "结论",
        ["revise", "approve", "reject"],
        index=["revise", "approve", "reject"].index(existing.disposition) if existing else 0,
        key=f"disp-{ref.section}-{fingerprint[:8]}",
    )
    note = st.text_area(
        "备注",
        value=existing.note if existing else "",
        height=80,
        key=f"qanote-{ref.section}-{fingerprint[:8]}",
    )

    timing = existing.timing if existing else SectionQATiming()
    with st.expander("返工记录"):
        cols = st.columns(4)
        first_read = cols[0].number_input(
            "初读", 0, 600, timing.first_read_minutes,
            key=f"time-read-{ref.section}-{fingerprint[:8]}",
        )
        language_edit = cols[1].number_input(
            "语言", 0, 600, timing.language_edit_minutes,
            key=f"time-lang-{ref.section}-{fingerprint[:8]}",
        )
        item_edit = cols[2].number_input(
            "命题", 0, 600, timing.item_edit_minutes,
            key=f"time-item-{ref.section}-{fingerprint[:8]}",
        )
        layout_edit = cols[3].number_input(
            "版面", 0, 600, timing.layout_edit_minutes,
            key=f"time-layout-{ref.section}-{fingerprint[:8]}",
        )
        biggest = st.text_input(
            "最大返工原因",
            value=existing.biggest_rework_cause if existing else "",
            key=f"biggest-{ref.section}-{fingerprint[:8]}",
        )

    if st.button("保存 Human QA", key=f"save-qa-{ref.section}-{fingerprint[:8]}"):
        qa = SectionHumanQA(
            section=ref.section,
            section_id=ref.section_id,
            candidate_fingerprint=fingerprint,
            reviewer=reviewer,
            disposition=disposition,
            checks=SectionQAChecks(**common_values),
            section_specific_checks=specific,
            timing=SectionQATiming(
                first_read_minutes=first_read,
                language_edit_minutes=language_edit,
                item_edit_minutes=item_edit,
                layout_edit_minutes=layout_edit,
            ),
            biggest_rework_cause=biggest,
            note=note,
        )
        try:
            save_section_human_qa(root, manifest.exam_id, ref.section, qa)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _create_exam_panel(root: Path) -> None:
    st.markdown("## 新建完整模試")
    family = st.radio(
        "2026 blueprint",
        ["main_2026", "makeup_2026"],
        format_func=lambda value: "2026 本試験型" if value == "main_2026" else "2026 追試験型",
        horizontal=True,
    )
    title = st.text_input("模試名（可选）", placeholder="旅人教育 共通テスト中国語 模試 第1回")
    q4_topic = st.text_input("Q4 希望主题（可选）")
    q5_topic = st.text_input("Q5 希望主题（可选）")
    notes = st.text_input("教研备注（可选）")
    if st.button("＋ 新建完整模試", type="primary"):
        manifest, _ = create_exam_project(
            root,
            exam_family=family,
            title_ja=title or None,
            notes=notes,
            q4_topic_request=q4_topic,
            q5_topic_request=q5_topic,
        )
        create_all_section_requests(root, manifest.exam_id)
        st.session_state["selected_exam_id"] = manifest.exam_id
        st.rerun()


def _render_exam_qa(root: Path, manifest) -> None:
    try:
        readiness = exam_release_readiness(root, manifest.exam_id)
    except Exception as exc:
        st.warning(str(exc))
        return

    section_gates = [gate for gate in readiness.gates if gate.name.endswith(" release")]
    if section_gates and not all(gate.passed for gate in section_gates):
        st.caption("Q1–Q5 全部 Ready 后进入 Final Exam QA。")
        return

    artifact_gate = next((gate for gate in readiness.gates if gate.name == "artifact preflight"), None)
    if artifact_gate is None or not artifact_gate.passed:
        st.caption("先生成并通过当前版本的 PDF preflight，再进行 Final Exam QA。")
        return

    existing = None
    path = exam_qa_path(root, manifest.exam_id)
    if path.exists():
        try:
            existing = ExamHumanQA.model_validate(load_json(path))
        except Exception:
            existing = None

    st.markdown("#### Final Exam QA")
    qa_values = {}
    for name in ExamQAChecks.model_fields:
        qa_values[name] = st.checkbox(
            name.replace("_", " "),
            value=bool(getattr(existing.checks, name)) if existing else False,
            key=f"examqa-{manifest.exam_id}-{name}",
        )

    reviewer = st.text_input("整卷审题人", value=existing.reviewer if existing else "TABITO 教研")
    disposition_options = ["revise", "approve", "reject"]
    disposition = st.selectbox(
        "整卷结论",
        disposition_options,
        index=(
            disposition_options.index(existing.disposition)
            if existing and existing.disposition in disposition_options
            else 0
        ),
    )
    note = st.text_area("整卷备注", value=existing.note if existing else "", height=80)
    timing = existing.timing if existing else ExamQATiming()
    with st.expander("整卷返工记录"):
        cols = st.columns(3)
        first_read = cols[0].number_input(
            "初读", 0, 600, timing.full_exam_first_read_minutes,
            key=f"exam-time-read-{manifest.exam_id}",
        )
        layout_fix = cols[1].number_input(
            "版面", 0, 600, timing.layout_fix_minutes,
            key=f"exam-time-layout-{manifest.exam_id}",
        )
        cross_fix = cols[2].number_input(
            "跨大题", 0, 600, timing.cross_section_fix_minutes,
            key=f"exam-time-cross-{manifest.exam_id}",
        )

    if st.button("保存 Final Exam QA"):
        qa = ExamHumanQA(
            exam_id=manifest.exam_id,
            reviewer=reviewer,
            disposition=disposition,
            checks=ExamQAChecks(**qa_values),
            timing=ExamQATiming(
                full_exam_first_read_minutes=first_read,
                layout_fix_minutes=layout_fix,
                cross_section_fix_minutes=cross_fix,
            ),
            note=note,
        )
        try:
            save_exam_human_qa(root, manifest.exam_id, qa)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_export(root: Path, manifest) -> None:
    if not all(ref.path for ref in manifest.sections):
        return
    if st.button("生成完整 TeX / PDF"):
        try:
            outputs = render_exam(root, manifest.exam_id, compile_pdf=True)
            for key, output in outputs.items():
                if output and output.exists():
                    mime = "application/pdf" if output.suffix == ".pdf" else "text/plain"
                    st.download_button(
                        f"下载 {key}", output.read_bytes(), file_name=output.name, mime=mime
                    )
        except Exception as exc:
            st.error(str(exc))


def _render_review_panel(root: Path, manifest, ref, section, path: Path) -> None:
    result = validate_section_file(path)
    if not result.passed:
        st.error("结构校验未通过")
        for error in result.errors:
            st.markdown(f"- {error}")
        return
    for warning in result.warnings:
        st.caption("warning · " + warning)

    st.markdown("#### Blind Review")
    st.caption(
        f"{PREFERRED_MODEL} · {MIN_REASONING_LEVEL.title()} · 非个性化 Temporary Chat"
    )
    st.caption(
        "只把 Blind Review Prompt 放进非个性化 Temporary Chat；不要让 memory、个性化、生成/修订历史或教师标注进入 reviewer 上下文。"
    )

    review_request = create_section_review_request(root, manifest.exam_id, ref.section)
    st.download_button(
        "下载 Blind Review Prompt",
        review_request.read_text(encoding="utf-8"),
        file_name=review_request.name,
    )

    isolated = st.checkbox(
        "已在非个性化 Temporary Chat 中完成，且 reviewer 未看过本题的生成、修订、答案或教师标注",
        key=f"isolated-review-{ref.section}-{section_fingerprint(section)[:8]}",
    )
    review_json = st.text_area(
        "Reviewer JSON",
        height=220,
        key=f"review-json-{ref.section}",
    )
    if st.button(
        "导入 Blind Review",
        key=f"review-import-{ref.section}",
        disabled=not isolated,
    ):
        try:
            import_section_review(
                root,
                manifest.exam_id,
                ref.section,
                review_json,
                model_label=PREFERRED_MODEL,
                reasoning_level=MIN_REASONING_LEVEL,
                fresh_chat_confirmed=True,
                context_mode="non_personalized_temporary_chat",
                authoring_context_seen=False,
            )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    blind_passed = False
    try:
        readiness = section_release_readiness(root, manifest.exam_id, ref.section)
        for gate in readiness.gates:
            mark = "✓" if gate.passed else "—"
            st.markdown(f"{mark} {gate.name}")
            if not gate.passed:
                st.caption(gate.detail)
        blind = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
        blind_passed = bool(blind and blind.passed)
    except Exception as exc:
        st.warning(str(exc))

    if blind_passed:
        st.divider()
        _section_human_qa_form(root, manifest, ref, section)
    else:
        st.caption("Blind Review 通过后进入 Human QA。")

    review_file = root / "workspace" / "exams" / manifest.exam_id / "reviews" / f"{ref.section.lower()}.review.json"
    if review_file.exists():
        revision_request = create_section_revision_request(root, manifest.exam_id, ref.section)
        st.caption(f"修订 · {PREFERRED_MODEL} · {MIN_REASONING_LEVEL.title()} · 建议新对话")
        st.download_button(
            "下载 Revision Prompt",
            revision_request.read_text(encoding="utf-8"),
            file_name=revision_request.name,
        )


def _render_revision_import(root: Path, manifest, ref) -> None:
    revised_json = st.text_area("修订版 JSON", height=340, key=f"revision-json-{ref.section}")
    if st.button("替换当前 Draft 并重新校验", type="primary", key=f"revision-import-{ref.section}"):
        try:
            _, result = import_section_response(root, manifest.exam_id, ref.section, revised_json)
            if result.errors:
                st.error("修订版已保存，但结构校验未通过：" + " | ".join(result.errors))
            else:
                st.rerun()
        except Exception as exc:
            st.error(str(exc))


def main() -> None:
    st.set_page_config(page_title="TABITO 中国語模試", page_icon="📘", layout="wide")
    st.markdown(APP_CSS, unsafe_allow_html=True)
    root = _root()

    exams = _discover_exams(root)
    choices = ["＋ 新建完整模試", *exams]
    default = 0
    selected_id = st.session_state.get("selected_exam_id")
    if selected_id:
        default = next((i for i, label in enumerate(choices) if selected_id in label), 0)

    st.sidebar.markdown("**中国語模試**")
    selection = st.sidebar.selectbox("模試", choices, index=default, label_visibility="collapsed")
    if selection == "＋ 新建完整模試":
        _create_exam_panel(root)
        return

    exam_path = exams[selection]
    manifest = load_manifest(exam_path)
    is_approved = "approved" in exam_path.parts
    st.session_state["selected_exam_id"] = manifest.exam_id
    family_label = "2026 本試験型" if manifest.exam_family == "main_2026" else "2026 追試験型"

    st.markdown(f"## {manifest.title_ja}")
    st.caption(f"{family_label} · 200点 · 80分 · 50解答欄 · {manifest.workflow.state}")

    overview, section_tab, release_tab = st.tabs(["整卷", "大题", "Release"])

    with overview:
        for ref in manifest.sections:
            cols = st.columns([0.6, 2.4, 1.2, 1.2])
            cols[0].markdown(f"**{ref.section}**")
            cols[1].markdown(SECTION_LABELS[ref.section])
            cols[2].markdown(f"{ref.expected_score}点 · {ref.answer_start}–{ref.answer_end}")
            cols[3].markdown(_section_status(root, manifest, exam_path, ref))

        validation = validate_exam(exam_path)
        if validation.errors:
            st.error("整卷结构尚未通过")
            for error in validation.errors:
                st.markdown(f"- {error}")
        if validation.warnings:
            with st.expander(f"Warnings · {len(validation.warnings)}"):
                for warning in validation.warnings:
                    st.markdown(f"- {warning}")

        if all(ref.path and (exam_path.parent / ref.path).exists() for ref in manifest.sections):
            st.divider()
            for ref in manifest.sections:
                _render_section_preview(load_section(exam_path.parent / ref.path), teacher=False)
                st.divider()

    with section_tab:
        section_name = st.selectbox(
            "大题",
            [ref.section for ref in manifest.sections],
            format_func=lambda value: f"{value} · {SECTION_LABELS[value]}",
        )
        ref = next(ref for ref in manifest.sections if ref.section == section_name)
        path = _section_path(exam_path, ref)

        if path is None or not path.exists():
            if is_approved:
                st.error(f"正式模試缺少 {section_name}")
            else:
                st.caption(f"生成 · {PREFERRED_MODEL} · {MIN_REASONING_LEVEL.title()}")
                request_path, _ = create_exam_section_request(root, manifest.exam_id, section_name)
                st.download_button(
                    "下载生成 Prompt",
                    request_path.read_text(encoding="utf-8"),
                    file_name=request_path.name,
                )
                response = st.text_area("生成结果 JSON", height=320, key=f"response-{section_name}")
                if st.button("导入并校验", type="primary", key=f"import-{section_name}"):
                    try:
                        _, result = import_section_response(root, manifest.exam_id, section_name, response)
                        if result.errors:
                            st.error(" | ".join(result.errors))
                        else:
                            st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        else:
            section = load_section(path)
            if is_approved:
                student, teacher = st.tabs(["学生预览", "教师标注"])
                with student:
                    _render_section_preview(section, teacher=False)
                with teacher:
                    _render_section_preview(section, teacher=True)
            else:
                student, teacher, review, revision = st.tabs(
                    ["学生预览", "教师标注", "Review", "修订"]
                )
                with student:
                    _render_section_preview(section, teacher=False)
                with teacher:
                    _render_section_preview(section, teacher=True)
                with review:
                    _render_review_panel(root, manifest, ref, section, path)
                with revision:
                    _render_revision_import(root, manifest, ref)

    with release_tab:
        if is_approved:
            st.caption("Approved · 只读。修改时创建新版本。")
            _render_export(root, manifest)
        else:
            try:
                readiness = exam_release_readiness(root, manifest.exam_id)
                for gate in readiness.gates:
                    mark = "✓" if gate.passed else "—"
                    st.markdown(f"{mark} {gate.name}")
                    if not gate.passed:
                        st.caption(gate.detail)
            except Exception as exc:
                readiness = None
                st.warning(str(exc))

            st.divider()
            _render_export(root, manifest)
            st.divider()
            _render_exam_qa(root, manifest)

            if readiness is not None and readiness.ready:
                if st.button("Approve → 正式模試库", type="primary"):
                    approve_exam(root, manifest.exam_id)
                    st.rerun()


if __name__ == "__main__":
    main()

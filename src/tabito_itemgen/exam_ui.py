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
            label = f"{state.upper()} · {manifest.title_ja} · {manifest.exam_id}"
            result[label] = path
    return result


def _status_badge(text: str, kind: str = "") -> str:
    return f'<span class="pill {kind}">{html.escape(text)}</span>'


def _section_path(exam_path: Path, ref) -> Path | None:
    return exam_path.parent / ref.path if ref.path else None


def _section_status(root: Path, manifest, exam_path: Path, ref) -> tuple[str, str]:
    path = _section_path(exam_path, ref)
    if path is None or not path.exists():
        return "未生成", ""
    validation = validate_section_file(path)
    if not validation.passed:
        return "结构修正", "bad"
    if "approved" in exam_path.parts:
        return "APPROVED", "ok"
    try:
        readiness = section_release_readiness(root, manifest.exam_id, ref.section)
    except Exception:
        return "Draft", ""
    if readiness.ready:
        return "Ready", "ok"
    review_gate = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
    if review_gate and review_gate.passed:
        return "Human QA", "warn"
    return "Blind Review", "warn"


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


def _preview_simple_section(section, teacher: bool = False) -> None:
    st.markdown(
        f'<div class="exam-header exam-title"><b>第{section.section[1]}問</b>　'
        f'{html.escape(section.title_ja)}（配点 {section.score}）</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="exam-rule"></div>', unsafe_allow_html=True)
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
                st.markdown(f"**{task.headword.hanzi}**　{task.headword.pinyin}")
                for word in task.candidates:
                    st.markdown(f"{word.label}　{word.hanzi}　{word.pinyin}")
            else:
                for line in task.lines:
                    st.markdown(f"**{line.speaker}**：{line.pinyin}")
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(task.prompt_ja)} '
                    f'{_answer_badge(task.answer_slot.answer_number)}</div>',
                    unsafe_allow_html=True,
                )
            _html_options(task.options)
            if teacher:
                st.caption(
                    f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option}"
                    f" · {task.rationale_ja}"
                )
        return
    if isinstance(section, Q2Section):
        for task in sorted(section.tasks, key=lambda value: value.order):
            st.markdown(
                f'<div class="exam-section">{task.subsection}</div>',
                unsafe_allow_html=True,
            )
            if isinstance(task, Q2OrderingTask):
                badges = "".join(_answer_badge(slot.answer_number) for slot in task.answer_slots)
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(task.prompt_ja)} {badges}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(task.source_ja)
                st.markdown(task.sentence_frame_zh)
                st.markdown(
                    "　".join(
                        f"{OPTION_MARKS[token.token_id - 1]} {token.text_zh}"
                        for token in task.token_pool
                    )
                )
                if teacher:
                    st.caption(
                        "正答 "
                        + " / ".join(
                            f"[{slot.answer_number}] {slot.correct_option}"
                            for slot in task.answer_slots
                        )
                        + f" · {task.rationale_ja}"
                    )
            else:
                st.markdown(
                    f'<div class="exam-prompt">{html.escape(task.prompt_ja)} '
                    f'{_answer_badge(task.answer_slot.answer_number)}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(task.sentence_zh)
                _html_options(task.options)
                if teacher:
                    st.caption(
                        f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option}"
                        f" · {task.rationale_ja}"
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
            _html_options(task.options)
            if teacher:
                st.caption(
                    f"正答 [{task.answer_slot.answer_number}] {task.answer_slot.correct_option}"
                    f" · {task.rationale_ja}"
                )
                for option, reasons in task.distractor_error_types.items():
                    detail = task.distractor_rationales_ja.get(option, "")
                    st.caption(f"誤答 {option} · {' / '.join(reasons)} · {detail}")
        return
    if isinstance(section, Q5Section):
        for paragraph in section.paragraphs:
            st.markdown(
                f'<div class="source-text">{html.escape(paragraph.text_zh)}</div>',
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
            _html_options(task.options)
            if teacher:
                st.caption(
                    "正答 "
                    + " / ".join(
                        f"[{slot.answer_number}] {slot.correct_option}"
                        for slot in task.answer_slots
                    )
                    + f" · {task.rationale_ja}"
                )
                if task.anchor_refs:
                    st.caption("参照 anchor · " + " / ".join(task.anchor_refs))


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
    if qa.candidate_fingerprint != fingerprint:
        st.warning("题目内容已修改。旧 Human QA 记录保留，但本版不会继承旧勾选。")
        return None
    return qa


def _section_human_qa_form(root: Path, manifest, ref, section) -> None:
    fingerprint = section_fingerprint(section)
    existing = _existing_section_qa(root, manifest.exam_id, ref.section, fingerprint)
    st.caption(f"candidate fingerprint · `{fingerprint[:16]}…`")

    common_values = {}
    for field in SectionQAChecks.model_fields:
        default = bool(getattr(existing.checks, field)) if existing else False
        common_values[field] = st.checkbox(
            field.replace("_", " "),
            value=default,
            key=f"qa-{ref.section}-{field}-{fingerprint[:8]}",
        )

    st.markdown("**Section-specific**")
    specific = {}
    for field in SECTION_SPECIFIC_QA[ref.section]:
        default = bool(existing.section_specific_checks.get(field, False)) if existing else False
        specific[field] = st.checkbox(
            field.replace("_", " "),
            value=default,
            key=f"qas-{ref.section}-{field}-{fingerprint[:8]}",
        )

    st.markdown("**人工返工时间（分钟）**")
    timing_defaults = existing.timing if existing else SectionQATiming()
    timing_cols = st.columns(4)
    first_read = timing_cols[0].number_input(
        "初读", min_value=0, max_value=600, value=timing_defaults.first_read_minutes,
        key=f"time-read-{ref.section}-{fingerprint[:8]}"
    )
    language_edit = timing_cols[1].number_input(
        "语言修改", min_value=0, max_value=600, value=timing_defaults.language_edit_minutes,
        key=f"time-lang-{ref.section}-{fingerprint[:8]}"
    )
    item_edit = timing_cols[2].number_input(
        "命题修改", min_value=0, max_value=600, value=timing_defaults.item_edit_minutes,
        key=f"time-item-{ref.section}-{fingerprint[:8]}"
    )
    layout_edit = timing_cols[3].number_input(
        "版面修改", min_value=0, max_value=600, value=timing_defaults.layout_edit_minutes,
        key=f"time-layout-{ref.section}-{fingerprint[:8]}"
    )

    reviewer = st.text_input(
        "Reviewer",
        value=existing.reviewer if existing else "TABITO 教研",
        key=f"reviewer-{ref.section}-{fingerprint[:8]}",
    )
    dispositions = ["revise", "approve", "reject"]
    disposition = st.selectbox(
        "Disposition",
        dispositions,
        index=dispositions.index(existing.disposition) if existing else 0,
        key=f"disp-{ref.section}-{fingerprint[:8]}",
    )
    defects = st.text_input(
        "Defects（逗号分隔）",
        value=", ".join(existing.defects) if existing else "",
        key=f"defects-{ref.section}-{fingerprint[:8]}",
    )
    biggest = st.text_input(
        "最大返工原因",
        value=existing.biggest_rework_cause if existing else "",
        key=f"biggest-{ref.section}-{fingerprint[:8]}",
    )
    note = st.text_area(
        "QA note",
        value=existing.note if existing else "",
        height=90,
        key=f"qanote-{ref.section}-{fingerprint[:8]}",
    )
    if st.button("保存 Human QA", key=f"save-qa-{ref.section}-{fingerprint[:8]}", width="stretch"):
        qa = SectionHumanQA(
            section=ref.section,
            section_id=ref.section_id,
            candidate_fingerprint=fingerprint,
            reviewer=reviewer,
            disposition=disposition,
            checks=SectionQAChecks(**common_values),
            section_specific_checks=specific,
            defects=[value.strip() for value in defects.split(",") if value.strip()],
            timing=SectionQATiming(
                first_read_minutes=first_read,
                language_edit_minutes=language_edit,
                item_edit_minutes=item_edit,
                layout_edit_minutes=layout_edit,
            ),
            biggest_rework_cause=biggest,
            note=note,
        )
        save_section_human_qa(root, manifest.exam_id, ref.section, qa)
        st.success("Human QA 已保存")
        st.rerun()


def _create_exam_panel(root: Path) -> None:
    st.markdown("## 新建完整模試")
    left, right = st.columns([1, 1])
    with left:
        family = st.radio(
            "2026 blueprint",
            ["main_2026", "makeup_2026"],
            format_func=lambda value: "2026 本試験型" if value == "main_2026" else "2026 追試験型",
            horizontal=True,
        )
        title = st.text_input(
            "模試名（可选）", placeholder="旅人教育 共通テスト中国語 模試 第1回"
        )
    with right:
        q4_topic = st.text_input("Q4 希望主题（可选）")
        q5_topic = st.text_input("Q5 希望主题（可选）")
        notes = st.text_input("教研备注（可选）")
    if st.button("＋ 新建完整模試", type="primary", width="stretch"):
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
        st.success("已创建 Exam project，并生成 Q1–Q5 五份独立 request。")
        st.rerun()


def _render_exam_qa(root: Path, manifest) -> None:
    existing = None
    path = exam_qa_path(root, manifest.exam_id)
    if path.exists():
        try:
            existing = ExamHumanQA.model_validate(load_json(path))
        except Exception:
            existing = None

    qa_values = {}
    for name in ExamQAChecks.model_fields:
        qa_values[name] = st.checkbox(
            name.replace("_", " "),
            value=bool(getattr(existing.checks, name)) if existing else False,
            key=f"examqa-{manifest.exam_id}-{name}",
        )

    st.markdown("**整卷返工时间（分钟）**")
    timing = existing.timing if existing else ExamQATiming()
    cols = st.columns(3)
    first_read = cols[0].number_input(
        "整卷初读", min_value=0, max_value=600, value=timing.full_exam_first_read_minutes,
        key=f"exam-time-read-{manifest.exam_id}"
    )
    layout_fix = cols[1].number_input(
        "版面修正", min_value=0, max_value=600, value=timing.layout_fix_minutes,
        key=f"exam-time-layout-{manifest.exam_id}"
    )
    cross_fix = cols[2].number_input(
        "跨大题修正", min_value=0, max_value=600, value=timing.cross_section_fix_minutes,
        key=f"exam-time-cross-{manifest.exam_id}"
    )
    reviewer = st.text_input(
        "Exam QA reviewer", value=existing.reviewer if existing else "TABITO 教研"
    )
    dispositions = ["revise", "approve", "reject"]
    disposition = st.selectbox(
        "Exam disposition",
        dispositions,
        index=dispositions.index(existing.disposition) if existing else 0,
    )
    defects = st.text_input(
        "整卷 defects（逗号分隔）",
        value=", ".join(existing.defects) if existing else "",
    )
    biggest = st.text_input(
        "整卷最大返工原因", value=existing.biggest_rework_cause if existing else ""
    )
    note = st.text_area("Final QA note", value=existing.note if existing else "", height=90)
    if st.button("保存 Final Exam QA", width="stretch"):
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
            defects=[value.strip() for value in defects.split(",") if value.strip()],
            biggest_rework_cause=biggest,
            note=note,
        )
        try:
            save_exam_human_qa(root, manifest.exam_id, qa)
            st.success("Final Exam QA 已绑定当前整卷 fingerprint")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_export(root: Path, manifest) -> None:
    if not all(ref.path for ref in manifest.sections):
        return
    if st.button("生成完整 TeX / PDF", width="stretch"):
        try:
            outputs = render_exam(root, manifest.exam_id, compile_pdf=True)
            generated_pdf = any(
                output is not None and output.suffix == ".pdf" for output in outputs.values()
            )
            if generated_pdf:
                st.success("整卷 TeX / PDF 已导出")
            else:
                st.warning("已生成完整 TeX；当前环境未找到 XeLaTeX，因此没有 PDF。")
            for key, output in outputs.items():
                if output and output.exists():
                    mime = "application/pdf" if output.suffix == ".pdf" else "text/plain"
                    st.download_button(
                        f"下载 {key}", output.read_bytes(), file_name=output.name, mime=mime
                    )
        except Exception as exc:
            st.error(str(exc))


def main() -> None:
    st.set_page_config(page_title="TABITO 中国語模試 Workbench", page_icon="📘", layout="wide")
    st.markdown(APP_CSS, unsafe_allow_html=True)
    root = _root()
    st.markdown(
        '<div class="tabito-kicker">TABITO EDUCATION · EXAM PRODUCTION</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tabito-title">共通テスト中国語 模試制作 Workbench</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tabito-sub">2026 本試験＋追試験を一次蓝本に、Q1–Q5を別々に作り、'
        '1冊の200点模試としてreleaseする。</div>',
        unsafe_allow_html=True,
    )

    exams = _discover_exams(root)
    sidebar_labels = ["＋ 新建完整模試", *exams]
    default = 0
    selected_id = st.session_state.get("selected_exam_id")
    if selected_id:
        for index, label in enumerate(sidebar_labels):
            if selected_id in label:
                default = index
                break
    selection = st.sidebar.selectbox("模試 project", sidebar_labels, index=default)

    if selection == "＋ 新建完整模試":
        _create_exam_panel(root)
        st.info("一套模試只创建一个 Exam project，但 Q1–Q5 会分别生成、审题和返修。")
        return

    exam_path = exams[selection]
    manifest = load_manifest(exam_path)
    is_approved = "approved" in exam_path.parts
    st.session_state["selected_exam_id"] = manifest.exam_id
    family_label = "2026 本試験型" if manifest.exam_family == "main_2026" else "2026 追試験型"
    st.markdown(f"## {html.escape(manifest.title_ja)}")
    st.markdown(
        '<div class="status-row">'
        + _status_badge(family_label)
        + _status_badge("200点")
        + _status_badge("80分")
        + _status_badge("50解答欄")
        + _status_badge(
            manifest.workflow.state.upper(), "ok" if manifest.workflow.state == "approved" else ""
        )
        + "</div>",
        unsafe_allow_html=True,
    )
    if is_approved:
        st.success("正式模試 · 已进入 Approved 库。此页面为只读审阅；如需改题，请创建新版本。")

    overview, section_tab, release_tab = st.tabs(["整卷概览", "当前大题", "Final Release"])
    with overview:
        st.markdown("### Q1–Q5 production status")
        for ref in manifest.sections:
            status, kind = _section_status(root, manifest, exam_path, ref)
            cols = st.columns([0.7, 2.4, 1.2, 1.3])
            cols[0].markdown(f"**{ref.section}**")
            cols[1].markdown(SECTION_LABELS[ref.section])
            cols[2].markdown(f"{ref.expected_score}点 · {ref.answer_start}–{ref.answer_end}")
            cols[3].markdown(_status_badge(status, kind), unsafe_allow_html=True)
        validation = validate_exam(exam_path)
        if validation.errors:
            st.error("整卷结构尚未通过")
            for error in validation.errors:
                st.markdown(f"- {error}")
        elif all(ref.path for ref in manifest.sections):
            st.success("整卷 deterministic validation 通过：200点 / 80分 / 1–50。")
        if validation.warnings:
            with st.expander(f"整卷 warning · {len(validation.warnings)}"):
                for warning in validation.warnings:
                    st.markdown(f"- {warning}")

        if all(ref.path and (exam_path.parent / ref.path).exists() for ref in manifest.sections):
            st.markdown("### 连续学生册预览")
            for ref in manifest.sections:
                _render_section_preview(load_section(exam_path.parent / ref.path), teacher=False)
                st.markdown("---")

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
                st.error(f"正式模試缺少 {section_name}，请检查 approved artifact。")
            else:
                st.warning(f"{section_name} 尚未导入。")
                request_path, _ = create_exam_section_request(root, manifest.exam_id, section_name)
                st.download_button(
                    "下载生成 Prompt",
                    request_path.read_text(encoding="utf-8"),
                    file_name=request_path.name,
                    width="stretch",
                )
                response = st.text_area(
                    "把 ChatGPT 返回的 JSON 粘贴到这里",
                    height=320,
                    key=f"response-{section_name}",
                )
                if st.button(
                    "导入并校验",
                    type="primary",
                    key=f"import-{section_name}",
                    width="stretch",
                ):
                    try:
                        _, result = import_section_response(
                            root, manifest.exam_id, section_name, response
                        )
                        if result.errors:
                            st.error("已保存 Draft，但结构校验未通过：" + " | ".join(result.errors))
                        else:
                            st.success("已导入 Draft")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        else:
            section = load_section(path)
            if is_approved:
                student_view, teacher_view = st.tabs(["学生预览", "教师标注"])
                with student_view:
                    _render_section_preview(section, teacher=False)
                with teacher_view:
                    _render_section_preview(section, teacher=True)
            else:
                student_view, teacher_view, review_view, revision_view = st.tabs(
                    ["学生预览", "教师标注", "Review / QA", "修订版导入"]
                )
                with student_view:
                    _render_section_preview(section, teacher=False)
                with teacher_view:
                    _render_section_preview(section, teacher=True)
                with review_view:
                    result = validate_section_file(path)
                    if result.passed:
                        st.success("Deterministic QA PASS")
                    else:
                        st.error("Deterministic QA FAIL")
                    for error in result.errors:
                        st.markdown(f"- {error}")
                    for warning in result.warnings:
                        st.caption("warning · " + warning)

                    review_request = create_section_review_request(
                        root, manifest.exam_id, section_name
                    )
                    st.download_button(
                        "下载 Blind Review Prompt",
                        review_request.read_text(encoding="utf-8"),
                        file_name=review_request.name,
                        width="stretch",
                    )
                    review_json = st.text_area(
                        "粘贴 reviewer JSON",
                        height=220,
                        key=f"review-json-{section_name}",
                    )
                    if st.button(
                        "导入 Blind Review",
                        key=f"review-import-{section_name}",
                        width="stretch",
                    ):
                        try:
                            import_section_review(
                                root, manifest.exam_id, section_name, review_json
                            )
                            st.success("Blind Review 已绑定当前版本")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                    try:
                        readiness = section_release_readiness(
                            root, manifest.exam_id, section_name
                        )
                        for gate in readiness.gates:
                            st.markdown(
                                _status_badge(
                                    ("✓ " if gate.passed else "○ ") + gate.name,
                                    "ok" if gate.passed else "warn",
                                ),
                                unsafe_allow_html=True,
                            )
                            if not gate.passed:
                                st.caption(gate.detail)
                        _section_human_qa_form(root, manifest, ref, section)
                        review_file = (
                            root
                            / "workspace"
                            / "exams"
                            / manifest.exam_id
                            / "reviews"
                            / f"{section_name.lower()}.review.json"
                        )
                        if not readiness.ready and review_file.exists():
                            if st.button(
                                "生成 Revision Prompt", key=f"revise-{section_name}"
                            ):
                                out = create_section_revision_request(
                                    root, manifest.exam_id, section_name
                                )
                                st.download_button(
                                    "下载 Revision Prompt",
                                    out.read_text(encoding="utf-8"),
                                    file_name=out.name,
                                )
                    except Exception as exc:
                        st.warning(str(exc))

                with revision_view:
                    st.markdown("### 导入修订版")
                    st.caption(
                        "粘贴使用 Revision Prompt 得到的完整 JSON。保存后该大题回到 Draft；"
                        "旧 Blind Review / Human QA 因 fingerprint 不同自动失效，其它大题不受影响。"
                    )
                    revised_json = st.text_area(
                        "修订版 JSON", height=340, key=f"revision-json-{section_name}"
                    )
                    if st.button(
                        "替换当前 Draft 并重新校验",
                        type="primary",
                        key=f"revision-import-{section_name}",
                        width="stretch",
                    ):
                        try:
                            _, result = import_section_response(
                                root, manifest.exam_id, section_name, revised_json
                            )
                            if result.errors:
                                st.error(
                                    "修订版已保存，但结构校验未通过："
                                    + " | ".join(result.errors)
                                )
                            else:
                                st.success("修订版已保存；该大题旧审题证据已自动 stale。")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))

    with release_tab:
        if is_approved:
            st.markdown("### Formal release")
            st.success("该模試已完成 release。Approved 内容不在原 ID 上覆盖。")
            _render_export(root, manifest)
        else:
            st.markdown("### Final Exam QA")
            st.caption(
                "所有 section ready 后，再从整卷角度检查80分钟负荷、跨大题重复、版面与统一性。"
            )
            _render_exam_qa(root, manifest)

            try:
                readiness = exam_release_readiness(root, manifest.exam_id)
                st.markdown("### Release readiness")
                for gate in readiness.gates:
                    st.markdown(
                        _status_badge(
                            ("✓ " if gate.passed else "○ ") + gate.name,
                            "ok" if gate.passed else "warn",
                        ),
                        unsafe_allow_html=True,
                    )
                    if not gate.passed:
                        st.caption(gate.detail)
                if readiness.ready and st.button(
                    "Approve → 正式模試库", type="primary", width="stretch"
                ):
                    target, _ = approve_exam(root, manifest.exam_id)
                    st.success(f"Approved: {target}")
                    st.rerun()
            except Exception as exc:
                st.warning(str(exc))

            _render_export(root, manifest)


if __name__ == "__main__":
    main()

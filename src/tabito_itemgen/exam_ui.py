from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from tabito_itemgen.exam_generate import (
    create_all_section_requests,
    create_exam_section_request,
    create_section_review_request,
    create_section_revision_request,
    create_section_structure_fix_request,
)
from tabito_itemgen.exam_models import ExamHumanQA, ExamQAChecks, ExamQATiming
from tabito_itemgen.exam_preview import render_simple_section_preview
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
    section_review_path,
)
from tabito_itemgen.exam_render import render_exam
from tabito_itemgen.exam_review_models import (
    SECTION_SPECIFIC_QA,
    SectionHumanQA,
    SectionQAChecks,
    SectionQATiming,
    SectionReview,
)
from tabito_itemgen.exam_validation import validate_exam, validate_section_file
from tabito_itemgen.io import load_json
from tabito_itemgen.model_policy import MIN_REASONING_LEVEL, PREFERRED_MODEL
from tabito_itemgen.models import Item
from tabito_itemgen.paths import find_project_root
from tabito_itemgen.section_io import load_section, section_fingerprint
from tabito_itemgen.ui_app import APP_CSS, _render_booklet_preview, _render_teacher_view

SECTION_LABELS = {
    "Q1": "発音・ピンイン",
    "Q2": "語句",
    "Q3": "表現力",
    "Q4": "複合的な資料の読み取り",
    "Q5": "長文読解",
}

SECTION_NAV_LABELS = {
    "Q1": "发音・拼音",
    "Q2": "词语",
    "Q3": "表达",
    "Q4": "综合资料",
    "Q5": "长文阅读",
}

STATUS_COPY = {
    "not_generated": ("未出题", "muted"),
    "needs_fix": ("需修正", "bad"),
    "draft": ("草稿", "muted"),
    "blind_review": ("待独立审题", "warn"),
    "review_failed": ("审题未通过", "bad"),
    "teacher_qa": ("待教师确认", "warn"),
    "ready": ("已就绪", "ok"),
    "approved": ("已定稿", "ok"),
}

COMMON_QA_LABELS = {
    "chinese_naturalness": "中文表达自然，没有生硬或歧义",
    "japanese_instruction_naturalness": "日语设问自然，符合考试语体",
    "answer_uniqueness": "正答唯一，答案依据充分",
    "distractors_plausible": "干扰项有迷惑性，没有明显送分项",
    "surface_fidelity_2026": "题型与 2026 共通考试风格一致",
    "official_difficulty_calibrated": "难度接近官方，不靠生僻词硬拉难度",
    "shortcut_resistance": "不能只靠关键词或形式特征直接猜答案",
    "originality_ok": "内容原创，不是官方题的换皮改写",
    "layout_readable": "题面排版清晰，学生阅读负担合理",
    "no_solution_leak": "题面没有答案或解法泄露",
}

SPECIFIC_QA_LABELS = {
    "pinyin_correctness": "拼音标注正确",
    "initial_final_analysis_correctness": "声母 / 韵母判断正确",
    "target_character_underlining_correct": "下划线字符位置正确",
    "pinyin_hidden_in_student_a_b_c": "学生版 A / B / C 不显示内部拼音",
    "tone_correctness": "声调判断正确",
    "yi_bu_tone_sandhi_handling": "「一 / 不」变调处理正确",
    "polyphone_context_unambiguous": "多音字语境明确，不会产生两种读法",
    "pinyin_diacritic_layout": "拼音声调符号显示正常",
    "dialogue_naturalness": "对话自然，像真实交际而不是练习句",
    "lexical_load_official_like": "词汇负荷接近官方题",
    "phonetic_confusability_sufficient": "辨音候选之间有足够竞争",
    "no_visual_counting_shortcut": "不能靠字形、字数等视觉特征直接数出答案",
    "lexical_usage_correct": "词汇用法与搭配正确",
    "inappropriate_rule_unambiguous": "「不适当」题只有一个明确答案",
    "ordering_unique": "语序题只有一种正确序列",
    "token_pool_natural": "语序题 token 池自然，没有垃圾选项",
    "ordering_token_granularity": "token 粒度合理，不是长句块拼接",
    "ordering_requires_syntax": "语序题确实需要句法判断",
    "distractor_tokens_locally_plausible": "干扰 token 在局部位置具有可接续性",
    "translation_semantics_correct": "翻译语义准确，没有范围或语气偏移",
    "distractor_error_taxonomy_correct": "干扰项错误类型标注与实际错误一致",
    "not_word_for_word_only": "不是只靠单词一一对应就能解",
    "near_miss_distractors": "至少有真正接近正答的 near-miss 干扰项",
    "no_keyword_shortcut": "不能靠一个关键词直接排除大多数选项",
    "semantic_operation_diversity": "整组题目的语义判断类型有变化",
    "information_journey": "资料与设问形成连贯的信息推进",
    "visual_materials_necessary": "图表 / 流程等资料确实参与解题",
    "source_integrity_ok": "资料内部一致，数值和事实无冲突",
    "surface_family_correct": "本试 / 追试 family 结构使用正确",
    "cross_source_dependency_real": "跨资料题确实需要多份资料才能确定答案",
    "cognitive_operation_diversity": "提取、比较、整合、应用等认知操作有变化",
    "template_repetition_risk_checked": "没有机械重复同一套资料与设问模板",
    "article_naturalness": "长文自然，像完整文章而不是为题目拼出的段落",
    "paragraph_coherence": "段落衔接自然，信息推进清楚",
    "anchor_accuracy": "下划线、空栏等 anchor 对应准确",
    "whole_text_reasoning_quality": "全文题确实需要跨段理解",
    "lexical_distractor_strength": "词汇题干扰项强度足够",
    "local_options_compete": "局部语境中至少有两个选项真正竞争",
    "late_question_operation_diversity": "后半题不是反复询问同一中心思想",
    "copyright_originality_check": "文章与官方材料保持原创边界",
    "long_text_pagination_readable": "长文分页不会打断阅读",
}

EXAM_QA_LABELS = {
    "timing_feasible_80_minutes": "整卷在 80 分钟内可合理完成",
    "score_structure_200_complete": "总分 200 分结构完整",
    "answer_numbers_1_to_50_continuous": "解答编号 1–50 连续无缺漏",
    "q1_to_q5_visual_hierarchy": "Q1–Q5 的视觉层级清楚一致",
    "difficulty_rhythm_reasonable": "难度节奏合理，没有某一段异常过易或过难",
    "q4_q5_topics_distinct": "Q4 / Q5 题材不过度重复",
    "no_cross_section_solution_leak": "大题之间没有相互泄露答案",
    "pinyin_style_consistent": "全卷拼音格式统一",
    "simplified_chinese_consistent": "简体字使用统一",
    "japanese_instruction_style_consistent": "日语设问语体统一",
    "numbers_punctuation_options_consistent": "数字、标点、选项格式统一",
    "pagination_readable": "分页自然，没有关键内容被不当拆开",
    "charts_readable": "图表尺寸与文字清晰可读",
    "long_text_pagination_readable": "长文分页适合连续阅读",
    "booklet_readable": "整本试卷整体易读、可直接印发",
}

DISPOSITION_LABELS = {
    "revise": "需要返修",
    "approve": "通过",
    "reject": "不采用",
}


def _root() -> Path:
    try:
        return find_project_root()
    except RuntimeError:
        return Path.cwd()


def _discover_exams(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    state_label = {"draft": "制作中", "approved": "已定稿"}
    for state in ("draft", "approved"):
        directory = root / "exam_bank" / state
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*/exam.json"), reverse=True):
            try:
                manifest = load_manifest(path)
            except Exception:
                continue
            label = f"{state_label[state]} · {manifest.title_ja}"
            if label in result:
                label += f" · {manifest.exam_id[-6:]}"
            result[label] = path
    return result


def _section_path(exam_path: Path, ref) -> Path | None:
    return exam_path.parent / ref.path if ref.path else None


def _current_review(root: Path, exam_id: str, section_name: str, fingerprint: str) -> SectionReview | None:
    path = section_review_path(root, exam_id, section_name)
    if not path.exists():
        return None
    try:
        review = SectionReview.model_validate(load_json(path))
    except Exception:
        return None
    return review if review.candidate_fingerprint == fingerprint else None


def _section_status(root: Path, manifest, exam_path: Path, ref) -> str:
    path = _section_path(exam_path, ref)
    if path is None or not path.exists():
        return "not_generated"
    if not validate_section_file(path).passed:
        return "needs_fix"
    if "approved" in exam_path.parts:
        return "approved"
    try:
        section = load_section(path)
        readiness = section_release_readiness(root, manifest.exam_id, ref.section)
    except Exception:
        return "draft"
    if readiness.ready:
        return "ready"
    blind = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
    if blind and blind.passed:
        return "teacher_qa"
    current_review = _current_review(
        root,
        manifest.exam_id,
        ref.section,
        section_fingerprint(section),
    )
    return "review_failed" if current_review is not None else "blind_review"


def _status_html(status: str) -> str:
    label, css_class = STATUS_COPY.get(status, (status, "muted"))
    return f'<span class="status-label {css_class}">{html.escape(label)}</span>'


def _gate_label(name: str) -> str:
    direct = {
        "deterministic validation": "格式与结构",
        "blind review": "独立审题",
        "human QA": "教师确认",
        "exam validation": "整卷结构",
        "artifact preflight": "PDF 检查",
        "exam human QA": "整卷教师确认",
    }
    if name in direct:
        return direct[name]
    if name.endswith(" release"):
        return name.removesuffix(" release")
    return name


def _humanize_review_detail(detail: str) -> str:
    if detail == "review JSON not saved":
        return "尚未导入独立审题结果。"
    parts: list[str] = []
    for raw in detail.split("; "):
        if raw == "review verdict is revise, not pass":
            parts.append("独立审题结论为「需要返修」。")
        elif raw == "review verdict is reject, not pass":
            parts.append("独立审题结论为「不采用」。")
        elif raw == "review contains high-severity issue":
            parts.append("审题报告包含严重问题，需要返修。")
        elif raw == "review task ids do not match candidate tasks":
            parts.append("审题结果的题目编号与当前版本不一致。")
        elif raw == "review section identity does not match candidate":
            parts.append("审题结果不是针对当前大题。")
        elif raw == "review fingerprint does not match current candidate":
            parts.append("这份审题结果属于上一版本，请对当前版本重新审题。")
        elif raw == "review execution record is stale":
            parts.append("审题执行记录属于上一版本，请重新审题。")
        elif raw == "blind review execution record not saved":
            parts.append("审题执行记录没有保存，请重新导入审题结果。")
        elif raw.startswith("blind review was not confirmed"):
            parts.append("没有确认使用独立上下文完成审题。")
        elif raw.startswith("blind review context mode"):
            parts.append("审题上下文没有被确认为记忆隔离模式。")
        elif raw.startswith("blind reviewer had access"):
            parts.append("审题上下文接触过出题或返修信息，不能作为独立审题证据。")
        elif ": reviewer answer " in raw and " != author key " in raw:
            task_id, rest = raw.split(": reviewer answer ", 1)
            reviewer_answer, author_answer = rest.split(" != author key ", 1)
            parts.append(
                f"{task_id}：独立作答 {reviewer_answer} 与命题答案 {author_answer} 不一致。"
            )
        else:
            parts.append(raw)
    return " ".join(parts)


def _next_action_text(ref, status: str) -> str:
    section = f"{ref.section} {SECTION_NAV_LABELS[ref.section]}"
    if status == "not_generated":
        return f"打开 {section}，先生成题目。"
    if status == "needs_fix":
        return f"打开 {section} 的「返修」，先修正结构校验问题。"
    if status in {"draft", "blind_review"}:
        return f"打开 {section} 的「质量检查」，完成独立审题。"
    if status == "review_failed":
        return f"打开 {section} 的「返修」，按审题意见修改后重新独立审题。"
    if status == "teacher_qa":
        return f"打开 {section} 的「质量检查」，完成教师确认。"
    return f"{section} 已就绪。"


def _section_view_key(exam_id: str, section_name: str, fingerprint: str, *, approved: bool = False) -> str:
    prefix = "approved-section-view" if approved else "section-view"
    return f"{prefix}-{exam_id}-{section_name}-{fingerprint[:8]}"


def _flash_key(exam_id: str, section_name: str) -> str:
    return f"section-flash-{exam_id}-{section_name}"


def _set_flash(exam_id: str, section_name: str, level: str, message: str) -> None:
    st.session_state[_flash_key(exam_id, section_name)] = (level, message)


def _show_flash(exam_id: str, section_name: str) -> None:
    payload = st.session_state.pop(_flash_key(exam_id, section_name), None)
    if not payload:
        return
    level, message = payload
    renderer = getattr(st, level, st.info)
    renderer(message)


def _render_header(manifest, family_label: str, ready_count: int, is_approved: bool) -> None:
    title = html.escape(manifest.title_ja)
    state_text = "已定稿" if is_approved else f"{ready_count}/5 大题已就绪"
    st.markdown(
        f'<div class="workspace-heading">{title}</div>'
        f'<div class="workspace-meta">{html.escape(family_label)}'
        f'<span>·</span>200 点<span>·</span>80 分钟<span>·</span>50 个解答栏'
        f'<span>·</span>{html.escape(state_text)}</div>',
        unsafe_allow_html=True,
    )


def _render_section_preview(section, teacher: bool) -> None:
    if isinstance(section, Item):
        _render_teacher_view(section) if teacher else _render_booklet_preview(section)
    else:
        render_simple_section_preview(section, teacher=teacher)


def _existing_section_qa(root: Path, exam_id: str, section_name: str, fingerprint: str):
    path = section_qa_path(root, exam_id, section_name)
    if not path.exists():
        return None
    try:
        qa = SectionHumanQA.model_validate(load_json(path))
    except Exception:
        return None
    return qa if qa.candidate_fingerprint == fingerprint else None


def _render_common_qa_checks(ref, fingerprint: str, existing) -> dict[str, bool]:
    values: dict[str, bool] = {}
    columns = st.columns(2)
    for index, field in enumerate(SectionQAChecks.model_fields):
        with columns[index % 2]:
            values[field] = st.checkbox(
                COMMON_QA_LABELS[field],
                value=bool(getattr(existing.checks, field)) if existing else False,
                key=f"qa-{ref.section}-{field}-{fingerprint[:8]}",
            )
    return values


def _section_human_qa_form(root: Path, manifest, ref, section) -> None:
    fingerprint = section_fingerprint(section)
    existing = _existing_section_qa(root, manifest.exam_id, ref.section, fingerprint)

    st.markdown("### 教师确认")
    st.caption("独立审题已经通过。这里由老师确认语言、答案、难度和考试感受。")

    st.markdown("#### 通用检查")
    common_values = _render_common_qa_checks(ref, fingerprint, existing)

    specific: dict[str, bool] = {}
    with st.expander("本大题专项检查", expanded=True):
        columns = st.columns(2)
        for index, field in enumerate(SECTION_SPECIFIC_QA[ref.section]):
            with columns[index % 2]:
                specific[field] = st.checkbox(
                    SPECIFIC_QA_LABELS.get(field, field.replace("_", " ")),
                    value=bool(existing.section_specific_checks.get(field, False)) if existing else False,
                    key=f"qas-{ref.section}-{field}-{fingerprint[:8]}",
                )

    col_reviewer, col_disposition = st.columns([1.2, 1])
    with col_reviewer:
        reviewer = st.text_input(
            "确认人",
            value=existing.reviewer if existing else "TABITO 教研",
            key=f"reviewer-{ref.section}-{fingerprint[:8]}",
        )
    with col_disposition:
        disposition_options = ["revise", "approve", "reject"]
        disposition = st.selectbox(
            "结论",
            disposition_options,
            index=(
                disposition_options.index(existing.disposition)
                if existing and existing.disposition in disposition_options
                else 0
            ),
            format_func=lambda value: DISPOSITION_LABELS[value],
            key=f"disp-{ref.section}-{fingerprint[:8]}",
        )

    note = st.text_area(
        "备注",
        value=existing.note if existing else "",
        placeholder="只记录需要返修或值得保留的要点即可。",
        height=90,
        key=f"qanote-{ref.section}-{fingerprint[:8]}",
    )

    timing = existing.timing if existing else SectionQATiming()
    with st.expander("返工时间（可选）"):
        cols = st.columns(4)
        first_read = cols[0].number_input(
            "初读 / 分钟",
            0,
            600,
            timing.first_read_minutes,
            key=f"time-read-{ref.section}-{fingerprint[:8]}",
        )
        language_edit = cols[1].number_input(
            "语言修改 / 分钟",
            0,
            600,
            timing.language_edit_minutes,
            key=f"time-lang-{ref.section}-{fingerprint[:8]}",
        )
        item_edit = cols[2].number_input(
            "命题修改 / 分钟",
            0,
            600,
            timing.item_edit_minutes,
            key=f"time-item-{ref.section}-{fingerprint[:8]}",
        )
        layout_edit = cols[3].number_input(
            "版面修改 / 分钟",
            0,
            600,
            timing.layout_edit_minutes,
            key=f"time-layout-{ref.section}-{fingerprint[:8]}",
        )
        biggest = st.text_input(
            "最大返工原因",
            value=existing.biggest_rework_cause if existing else "",
            key=f"biggest-{ref.section}-{fingerprint[:8]}",
        )

    if st.button("保存教师确认", type="primary", key=f"save-qa-{ref.section}-{fingerprint[:8]}"):
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
            _set_flash(manifest.exam_id, ref.section, "success", "教师确认已保存。")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _create_exam_panel(root: Path) -> None:
    st.markdown('<div class="workspace-heading">新建模试</div>', unsafe_allow_html=True)
    st.caption("选择本试或追试结构。Q4 / Q5 题材可以留空，让系统自动生成。")

    family = st.radio(
        "试卷结构",
        ["main_2026", "makeup_2026"],
        format_func=lambda value: "2026 本試験型" if value == "main_2026" else "2026 追試験型",
        horizontal=True,
    )
    title = st.text_input("模试名称", placeholder="旅人教育 共通テスト中国語 模試 第1回")
    q4_col, q5_col = st.columns(2)
    with q4_col:
        q4_topic = st.text_input("Q4 希望题材（可选）", placeholder="例如：校园活动、公共服务")
    with q5_col:
        q5_topic = st.text_input("Q5 希望题材（可选）", placeholder="例如：人物经历、社会生活")
    notes = st.text_input("教研备注（可选）", placeholder="只写这套卷需要特别注意的要求")

    if st.button("创建模试", type="primary"):
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
        st.caption("五个大题全部「已就绪」后，才进入整卷教师确认。")
        return

    artifact_gate = next((gate for gate in readiness.gates if gate.name == "artifact preflight"), None)
    if artifact_gate is None or not artifact_gate.passed:
        st.caption("先生成当前版本 PDF 并通过版面检查，再进行整卷教师确认。")
        return

    existing = None
    path = exam_qa_path(root, manifest.exam_id)
    if path.exists():
        try:
            existing = ExamHumanQA.model_validate(load_json(path))
        except Exception:
            existing = None

    st.markdown("### 整卷教师确认")
    st.caption("最后从整套试卷的时间、难度节奏、视觉和一致性进行一次检查。")

    qa_values: dict[str, bool] = {}
    columns = st.columns(2)
    for index, name in enumerate(ExamQAChecks.model_fields):
        with columns[index % 2]:
            qa_values[name] = st.checkbox(
                EXAM_QA_LABELS[name],
                value=bool(getattr(existing.checks, name)) if existing else False,
                key=f"examqa-{manifest.exam_id}-{name}",
            )

    col_reviewer, col_disposition = st.columns([1.2, 1])
    with col_reviewer:
        reviewer = st.text_input(
            "整卷确认人",
            value=existing.reviewer if existing else "TABITO 教研",
            key=f"exam-reviewer-{manifest.exam_id}",
        )
    with col_disposition:
        disposition_options = ["revise", "approve", "reject"]
        disposition = st.selectbox(
            "整卷结论",
            disposition_options,
            index=(
                disposition_options.index(existing.disposition)
                if existing and existing.disposition in disposition_options
                else 0
            ),
            format_func=lambda value: DISPOSITION_LABELS[value],
            key=f"exam-disposition-{manifest.exam_id}",
        )

    note = st.text_area(
        "整卷备注",
        value=existing.note if existing else "",
        height=90,
        key=f"exam-note-{manifest.exam_id}",
    )
    timing = existing.timing if existing else ExamQATiming()
    with st.expander("整卷返工时间（可选）"):
        cols = st.columns(3)
        first_read = cols[0].number_input(
            "整卷初读 / 分钟",
            0,
            600,
            timing.full_exam_first_read_minutes,
            key=f"exam-time-read-{manifest.exam_id}",
        )
        layout_fix = cols[1].number_input(
            "版面修改 / 分钟",
            0,
            600,
            timing.layout_fix_minutes,
            key=f"exam-time-layout-{manifest.exam_id}",
        )
        cross_fix = cols[2].number_input(
            "跨大题调整 / 分钟",
            0,
            600,
            timing.cross_section_fix_minutes,
            key=f"exam-time-cross-{manifest.exam_id}",
        )

    if st.button("保存整卷确认", type="primary", key=f"save-exam-qa-{manifest.exam_id}"):
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


def _render_pdf_downloads(directory: Path) -> None:
    files = (
        ("student.pdf", "学生版 PDF"),
        ("teacher.pdf", "教师版 PDF"),
        ("answer_sheet.pdf", "答题卡 PDF"),
        ("answer_key.json", "答案 JSON"),
    )
    existing = [(directory / filename, label) for filename, label in files if (directory / filename).exists()]
    if not existing:
        return

    st.markdown("#### 已生成文件")
    columns = st.columns(min(4, len(existing)))
    for index, (path, label) in enumerate(existing):
        mime = "application/pdf" if path.suffix == ".pdf" else "application/json"
        columns[index % len(columns)].download_button(
            label,
            path.read_bytes(),
            file_name=path.name,
            mime=mime,
            use_container_width=True,
            key=f"download-{directory.name}-{path.name}",
        )


def _render_export(root: Path, manifest, *, approved_dir: Path | None = None) -> None:
    if approved_dir is not None:
        _render_pdf_downloads(approved_dir / "artifacts")
        return

    if not all(ref.path for ref in manifest.sections):
        st.caption("五个大题都生成后即可输出完整试卷。")
        return

    output_dir = root / "output" / manifest.exam_id
    has_pdf = (output_dir / "student.pdf").exists()
    if st.button(
        "重新生成 PDF" if has_pdf else "生成完整 PDF",
        type="secondary" if has_pdf else "primary",
        key=f"render-pdf-{manifest.exam_id}",
    ):
        try:
            render_exam(root, manifest.exam_id, compile_pdf=True)
            st.success("PDF 已生成。")
        except Exception as exc:
            st.error(str(exc))

    _render_pdf_downloads(output_dir)


def _render_section_gate_summary(readiness) -> None:
    blind = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
    rows = []
    for gate in readiness.gates:
        label = _gate_label(gate.name)
        if gate.passed:
            mark, css_class, state = "✓", "ok", "已通过"
        elif gate.name == "blind review" and gate.detail != "review JSON not saved":
            mark, css_class, state = "!", "bad", "未通过"
        elif gate.name == "blind review":
            mark, css_class, state = "→", "muted", "待审题"
        elif gate.name == "human QA" and not (blind and blind.passed):
            mark, css_class, state = "○", "muted", "审题通过后开放"
        elif gate.name == "human QA":
            mark, css_class, state = "→", "muted", "待确认"
        else:
            mark, css_class, state = "—", "muted", "未完成"
        rows.append(
            f'<div class="gate-row"><span class="gate-mark {css_class}">{mark}</span>'
            f'<span>{html.escape(label)}　<small>{html.escape(state)}</small></span></div>'
        )
    st.markdown(
        f'<div class="workflow-list compact">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def _render_review_panel(root: Path, manifest, ref, section, path: Path) -> None:
    result = validate_section_file(path)
    if not result.passed:
        st.error("这道大题还有结构问题，先进入「返修」修正结构后再审题。")
        for error in result.errors:
            st.markdown(f"- {error}")
        return

    if result.warnings:
        with st.expander(f"结构提醒 · {len(result.warnings)}"):
            for warning in result.warnings:
                st.markdown(f"- {warning}")

    st.markdown("### 独立审题")
    st.caption(
        "用一个不带记忆和出题历史的 Temporary Chat 独立作答。"
        "审题模型只能看到学生题面，不能看到答案、解析和教师标注。"
    )

    review_request = create_section_review_request(root, manifest.exam_id, ref.section)
    with st.expander("复制独立审题指令"):
        st.code(review_request.read_text(encoding="utf-8"), language=None)
        st.download_button(
            "下载审题指令",
            review_request.read_text(encoding="utf-8"),
            file_name=review_request.name,
            key=f"download-review-prompt-{ref.section}",
        )

    fingerprint = section_fingerprint(section)
    isolated = st.checkbox(
        "我已在非个性化 Temporary Chat 中完成独立审题，且该对话没有看过本题答案或出题历史",
        key=f"isolated-review-{ref.section}-{fingerprint[:8]}",
    )
    review_json = st.text_area(
        "粘贴审题结果（JSON）",
        height=220,
        placeholder="把独立审题返回的完整 JSON 粘贴到这里。",
        key=f"review-json-{ref.section}-{fingerprint[:8]}",
    )
    if st.button(
        "导入审题结果",
        type="primary",
        key=f"review-import-{ref.section}-{fingerprint[:8]}",
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
            updated = section_release_readiness(root, manifest.exam_id, ref.section)
            blind_after = next(
                (gate for gate in updated.gates if gate.name == "blind review"),
                None,
            )
            if blind_after and blind_after.passed:
                _set_flash(
                    manifest.exam_id,
                    ref.section,
                    "success",
                    "独立审题已通过，教师确认已开放。",
                )
            else:
                detail = blind_after.detail if blind_after else "独立审题未通过。"
                _set_flash(
                    manifest.exam_id,
                    ref.section,
                    "warning",
                    "审题结果已导入，但当前版本未通过：" + _humanize_review_detail(detail),
                )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    blind_passed = False
    try:
        readiness = section_release_readiness(root, manifest.exam_id, ref.section)
        st.markdown("#### 当前检查状态")
        _render_section_gate_summary(readiness)
        blind = next((gate for gate in readiness.gates if gate.name == "blind review"), None)
        blind_passed = bool(blind and blind.passed)
        if blind and not blind.passed and blind.detail != "review JSON not saved":
            st.warning(_humanize_review_detail(blind.detail))
            with st.expander("查看技术详情"):
                st.code(blind.detail, language=None)
    except Exception as exc:
        st.warning(str(exc))

    if blind_passed:
        st.divider()
        _section_human_qa_form(root, manifest, ref, section)
    else:
        st.caption("独立审题通过后，这里会自动出现「教师确认」。")


def _render_structure_fix_import(root: Path, manifest, ref, section, path: Path) -> None:
    validation = validate_section_file(path)
    st.markdown("### 结构修正")
    st.caption("当前版本还没有通过格式与结构检查。先修正这些机器可确定的问题，不需要先做独立审题。")
    for error in validation.errors:
        st.markdown(f"- {error}")

    try:
        request = create_section_structure_fix_request(root, manifest.exam_id, ref.section)
    except Exception as exc:
        st.error(str(exc))
        return

    fingerprint = section_fingerprint(section)
    with st.expander("复制结构修正指令", expanded=True):
        st.code(request.read_text(encoding="utf-8"), language=None)
        st.download_button(
            "下载结构修正指令",
            request.read_text(encoding="utf-8"),
            file_name=request.name,
            key=f"download-structure-fix-{ref.section}-{fingerprint[:8]}",
        )

    fixed_json = st.text_area(
        "粘贴修正后的 JSON",
        height=340,
        placeholder="把结构修正后的完整 JSON 粘贴到这里。",
        key=f"structure-fix-json-{ref.section}-{fingerprint[:8]}",
    )
    if st.button(
        "导入结构修正版",
        type="primary",
        key=f"structure-fix-import-{ref.section}-{fingerprint[:8]}",
    ):
        try:
            fixed_path, result = import_section_response(
                root,
                manifest.exam_id,
                ref.section,
                fixed_json,
            )
            if result.errors:
                st.error("仍有结构问题：" + " | ".join(result.errors))
                return

            fixed = load_section(fixed_path)
            fixed_fingerprint = section_fingerprint(fixed)
            st.session_state[
                _section_view_key(manifest.exam_id, ref.section, fixed_fingerprint)
            ] = "质量检查"
            _set_flash(
                manifest.exam_id,
                ref.section,
                "success",
                "结构修正已导入并通过检查。下一步进行独立审题。",
            )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_revision_import(root: Path, manifest, ref, section, path: Path) -> None:
    validation = validate_section_file(path)
    if not validation.passed:
        _render_structure_fix_import(root, manifest, ref, section, path)
        return

    review_file = section_review_path(root, manifest.exam_id, ref.section)
    st.markdown("### 返修")
    if not review_file.exists():
        st.caption("先完成独立审题。需要修改时，系统会根据审题结果生成返修指令。")
        return

    fingerprint = section_fingerprint(section)
    try:
        review = SectionReview.model_validate(load_json(review_file))
    except Exception as exc:
        st.error("已保存的审题结果无法读取：" + str(exc))
        return

    if review.candidate_fingerprint != fingerprint:
        st.success("当前题目已经是返修后的新版本。旧审题意见已失效，请回到「质量检查」重新独立审题。")
        return

    try:
        revision_request = create_section_revision_request(root, manifest.exam_id, ref.section)
    except Exception as exc:
        st.warning(str(exc))
        return

    with st.expander("复制返修指令"):
        st.code(revision_request.read_text(encoding="utf-8"), language=None)
        st.download_button(
            "下载返修指令",
            revision_request.read_text(encoding="utf-8"),
            file_name=revision_request.name,
            key=f"download-revision-prompt-{ref.section}-{fingerprint[:8]}",
        )

    revised_json = st.text_area(
        "粘贴返修后的 JSON",
        height=340,
        placeholder="把返修后的完整 JSON 粘贴到这里。",
        key=f"revision-json-{ref.section}-{fingerprint[:8]}",
    )
    if st.button(
        "导入返修版",
        type="primary",
        key=f"revision-import-{ref.section}-{fingerprint[:8]}",
    ):
        try:
            revised_path, result = import_section_response(
                root,
                manifest.exam_id,
                ref.section,
                revised_json,
            )
            if result.errors:
                revised = load_section(revised_path)
                revised_fingerprint = section_fingerprint(revised)
                st.session_state[
                    _section_view_key(manifest.exam_id, ref.section, revised_fingerprint)
                ] = "返修"
                _set_flash(
                    manifest.exam_id,
                    ref.section,
                    "warning",
                    "返修版已导入，但仍有结构问题。请继续完成结构修正。",
                )
                st.rerun()

            revised = load_section(revised_path)
            revised_fingerprint = section_fingerprint(revised)
            if revised_fingerprint == fingerprint:
                st.warning("返修版与当前版本完全相同，没有产生实际修改。请检查返修结果后再导入。")
                return

            next_view_key = _section_view_key(
                manifest.exam_id,
                ref.section,
                revised_fingerprint,
            )
            st.session_state[next_view_key] = "质量检查"
            _set_flash(
                manifest.exam_id,
                ref.section,
                "success",
                "返修版已导入。上一版审题证据已失效，请对新版本重新进行独立审题。",
            )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_generation_panel(root: Path, manifest, ref) -> None:
    st.markdown("### 出题")
    st.caption(
        f"使用 {PREFERRED_MODEL} · {MIN_REASONING_LEVEL.title()} 生成这一大题。"
        "先复制出题指令，再把模型返回的完整 JSON 粘贴回来。"
    )
    request_path, _ = create_exam_section_request(root, manifest.exam_id, ref.section)
    with st.expander("复制出题指令"):
        st.code(request_path.read_text(encoding="utf-8"), language=None)
        st.download_button(
            "下载出题指令",
            request_path.read_text(encoding="utf-8"),
            file_name=request_path.name,
            key=f"download-generation-prompt-{ref.section}",
        )

    response = st.text_area(
        "粘贴生成结果（JSON）",
        height=340,
        placeholder="把 ChatGPT 返回的完整 JSON 粘贴到这里。",
        key=f"response-{ref.section}",
    )
    if st.button("导入题目", type="primary", key=f"import-{ref.section}"):
        try:
            path, result = import_section_response(root, manifest.exam_id, ref.section, response)
            fingerprint = section_fingerprint(load_section(path))
            if result.errors:
                st.session_state[
                    _section_view_key(manifest.exam_id, ref.section, fingerprint)
                ] = "返修"
                _set_flash(
                    manifest.exam_id,
                    ref.section,
                    "warning",
                    "题目已导入，但还有结构问题。请先完成结构修正。",
                )
                st.rerun()
            else:
                st.session_state[
                    _section_view_key(manifest.exam_id, ref.section, fingerprint)
                ] = "质量检查"
                _set_flash(
                    manifest.exam_id,
                    ref.section,
                    "success",
                    "题目已导入并通过格式与结构检查。下一步进行独立审题。",
                )
                st.rerun()
        except Exception as exc:
            st.error(str(exc))


def _render_overview(root: Path, manifest, exam_path: Path, statuses: dict[str, str]) -> None:
    st.markdown("### 制作进度")
    rows = []
    for ref in manifest.sections:
        rows.append(
            '<div class="workflow-row">'
            f'<div class="workflow-code">{ref.section}</div>'
            f'<div class="workflow-name">{html.escape(SECTION_LABELS[ref.section])}</div>'
            f'<div class="workflow-score">{ref.expected_score} 点 · {ref.answer_start}–{ref.answer_end}</div>'
            f'<div class="workflow-status">{_status_html(statuses[ref.section])}</div>'
            "</div>"
        )
    st.markdown(f'<div class="workflow-list">{"".join(rows)}</div>', unsafe_allow_html=True)

    next_ref = next(
        (ref for ref in manifest.sections if statuses[ref.section] not in {"ready", "approved"}),
        None,
    )
    if next_ref is None:
        next_text = "五个大题都已就绪。可以进入「定稿发布」生成 PDF 并做整卷确认。"
    else:
        next_text = _next_action_text(next_ref, statuses[next_ref.section])
    st.markdown(
        f'<div class="next-action"><b>下一步</b><span>{html.escape(next_text)}</span></div>',
        unsafe_allow_html=True,
    )

    validation = validate_exam(exam_path)
    if validation.errors:
        st.error("整卷结构尚未通过。")
        for error in validation.errors:
            st.markdown(f"- {error}")
    if validation.warnings:
        with st.expander(f"整卷提醒 · {len(validation.warnings)}"):
            for warning in validation.warnings:
                st.markdown(f"- {warning}")

    if all(ref.path and (exam_path.parent / ref.path).exists() for ref in manifest.sections):
        with st.expander("查看整卷学生版预览"):
            for index, ref in enumerate(manifest.sections):
                if index:
                    st.divider()
                _render_section_preview(load_section(exam_path.parent / ref.path), teacher=False)


def _render_section_workspace(
    root: Path,
    manifest,
    exam_path: Path,
    ref,
    status: str,
    *,
    is_approved: bool,
) -> None:
    st.markdown(
        f'<div class="section-workspace-heading">{ref.section}　'
        f'{html.escape(SECTION_LABELS[ref.section])}</div>'
        f'<div class="section-workspace-meta">{ref.expected_score} 点 · '
        f'解答 {ref.answer_start}–{ref.answer_end}　{_status_html(status)}</div>',
        unsafe_allow_html=True,
    )
    _show_flash(manifest.exam_id, ref.section)

    path = _section_path(exam_path, ref)
    if path is None or not path.exists():
        if is_approved:
            st.error(f"正式模试缺少 {ref.section}。")
            return
        st.markdown(
            f'<div class="next-action"><b>当前</b><span>{html.escape(_next_action_text(ref, status))}</span></div>',
            unsafe_allow_html=True,
        )
        _render_generation_panel(root, manifest, ref)
        return

    section = load_section(path)
    fingerprint = section_fingerprint(section)
    if not is_approved and status not in {"ready"}:
        st.markdown(
            f'<div class="next-action"><b>当前</b><span>{html.escape(_next_action_text(ref, status))}</span></div>',
            unsafe_allow_html=True,
        )

    if is_approved:
        options = ["学生题面", "答案与解析"]
        view_key = _section_view_key(
            manifest.exam_id,
            ref.section,
            fingerprint,
            approved=True,
        )
        if view_key not in st.session_state:
            st.session_state[view_key] = "学生题面"
        view = st.radio(
            "查看内容",
            options,
            horizontal=True,
            label_visibility="collapsed",
            key=view_key,
        )
        _render_section_preview(section, teacher=view == "答案与解析")
        return

    options = ["学生题面", "答案与解析", "质量检查", "返修"]
    view_key = _section_view_key(manifest.exam_id, ref.section, fingerprint)
    if view_key not in st.session_state:
        st.session_state[view_key] = (
            "返修"
            if status in {"review_failed", "needs_fix"}
            else "质量检查"
            if status in {"blind_review", "teacher_qa", "draft"}
            else "学生题面"
        )
    view = st.radio(
        "当前页面",
        options,
        horizontal=True,
        label_visibility="collapsed",
        key=view_key,
    )

    # Render exactly one surface. Streamlit tabs execute every tab body on each
    # rerun, which made revision imports appear to hang as all previews/prompts
    # were rebuilt at once.
    if view == "学生题面":
        _render_section_preview(section, teacher=False)
    elif view == "答案与解析":
        _render_section_preview(section, teacher=True)
    elif view == "质量检查":
        _render_review_panel(root, manifest, ref, section, path)
    else:
        _render_revision_import(root, manifest, ref, section, path)


def _render_release_workspace(
    root: Path,
    manifest,
    *,
    is_approved: bool,
    approved_dir: Path | None = None,
) -> None:
    st.markdown("### 定稿发布")
    if is_approved:
        st.markdown(
            '<div class="next-action"><b>状态</b><span>这套模试已定稿，当前为只读版本。</span></div>',
            unsafe_allow_html=True,
        )
        _render_export(root, manifest, approved_dir=approved_dir)
        return

    try:
        readiness = exam_release_readiness(root, manifest.exam_id)
    except Exception as exc:
        readiness = None
        st.warning(str(exc))

    if readiness is not None:
        rows = []
        for gate in readiness.gates:
            label = _gate_label(gate.name)
            mark = "✓" if gate.passed else "—"
            css_class = "ok" if gate.passed else "muted"
            rows.append(
                '<div class="release-row">'
                f'<div class="release-mark {css_class}">{mark}</div>'
                f'<div class="release-name">{html.escape(label)}</div>'
                f'<div class="release-state">{"通过" if gate.passed else "未完成"}</div>'
                "</div>"
            )
        st.markdown(f'<div class="release-list">{"".join(rows)}</div>', unsafe_allow_html=True)

        failed = [gate for gate in readiness.gates if not gate.passed]
        if failed:
            with st.expander("查看未完成项目"):
                for gate in failed:
                    st.markdown(f"**{_gate_label(gate.name)}**")
                    detail = (
                        _humanize_review_detail(gate.detail)
                        if gate.name == "blind review"
                        else gate.detail
                    )
                    st.caption(detail)

    st.divider()
    st.markdown("### PDF")
    _render_export(root, manifest)

    st.divider()
    _render_exam_qa(root, manifest)

    if readiness is not None and readiness.ready:
        st.divider()
        if st.button(
            "定稿并存入正式题库",
            type="primary",
            key=f"approve-exam-{manifest.exam_id}",
        ):
            approve_exam(root, manifest.exam_id)
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="TABITO 中国語模試", page_icon="📘", layout="wide")
    st.markdown(APP_CSS, unsafe_allow_html=True)
    root = _root()

    exams = _discover_exams(root)
    choices = ["＋ 新建模试", *exams]
    default = 0
    selected_id = st.session_state.get("selected_exam_id")
    if selected_id:
        for index, label in enumerate(choices):
            path = exams.get(label)
            if path is not None and path.parent.name == selected_id:
                default = index
                break

    st.sidebar.markdown(
        '<div class="sidebar-brand">TABITO</div>'
        '<div class="sidebar-title">中国語模試制作</div>',
        unsafe_allow_html=True,
    )
    selection = st.sidebar.selectbox(
        "模试",
        choices,
        index=default,
        label_visibility="collapsed",
    )
    if selection == "＋ 新建模试":
        _create_exam_panel(root)
        return

    exam_path = exams[selection]
    manifest = load_manifest(exam_path)
    is_approved = "approved" in exam_path.parts
    st.session_state["selected_exam_id"] = manifest.exam_id
    family_label = "2026 本試験型" if manifest.exam_family == "main_2026" else "2026 追試験型"

    statuses = {
        ref.section: _section_status(root, manifest, exam_path, ref)
        for ref in manifest.sections
    }
    ready_count = sum(status in {"ready", "approved"} for status in statuses.values())
    _render_header(manifest, family_label, ready_count, is_approved)

    st.sidebar.markdown('<div class="sidebar-rule"></div>', unsafe_allow_html=True)
    st.sidebar.caption(f"大题就绪　{ready_count} / 5")

    nav_options = ["overview", *[ref.section for ref in manifest.sections], "release"]
    nav = st.sidebar.radio(
        "制作流程",
        nav_options,
        format_func=lambda value: (
            "总览"
            if value == "overview"
            else "定稿发布"
            if value == "release"
            else f"{value}　{SECTION_NAV_LABELS[value]} · {STATUS_COPY[statuses[value]][0]}"
        ),
        label_visibility="collapsed",
        key=f"workspace-nav-{manifest.exam_id}",
    )

    if nav == "overview":
        _render_overview(root, manifest, exam_path, statuses)
        return

    if nav == "release":
        _render_release_workspace(
            root,
            manifest,
            is_approved=is_approved,
            approved_dir=exam_path.parent if is_approved else None,
        )
        return

    ref = next(ref for ref in manifest.sections if ref.section == nav)
    _render_section_workspace(
        root,
        manifest,
        exam_path,
        ref,
        statuses[ref.section],
        is_approved=is_approved,
    )


if __name__ == "__main__":
    main()

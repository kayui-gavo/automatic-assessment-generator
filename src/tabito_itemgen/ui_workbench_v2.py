from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from pydantic import ValidationError

from tabito_itemgen.generate_request import (
    BLUEPRINT_VERSION,
    create_q4_request,
    create_review_request,
    create_revision_request,
)
from tabito_itemgen.models import HumanQA, HumanQAChecks, HumanQATiming, Item, Review
from tabito_itemgen.presentation import FAMILY_LABELS, FAMILY_SUMMARIES
from tabito_itemgen.production import (
    approve_item,
    human_qa_binding_status,
    import_item_response,
    import_review_response,
    item_fingerprint,
    load_human_qa_if_present,
    load_review_if_present,
    release_readiness,
    review_binding_status,
    save_draft,
    save_human_qa,
)
from tabito_itemgen.render import compile_xelatex, render_item_tex
from tabito_itemgen.ui_app import (
    APP_CSS,
    _discover_items,
    _download_file,
    _parse_item,
    _render_booklet_preview,
    _render_structure_view,
    _render_teacher_view,
    _render_validation,
    _root,
    _status_pills,
    _validation_result,
    _write_ui_temp,
)
from tabito_itemgen.validate import compare_review

WORKBENCH_CSS = """
<style>
.pipeline {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.55rem; margin:.7rem 0 1rem 0;}
.stage {border:1px solid #d8d4c8; background:#fffdf8; padding:.62rem .72rem; border-radius:6px; min-height:72px;}
.stage .n {font-size:.72rem; color:#7a746a; letter-spacing:.08em; text-transform:uppercase;}
.stage .t {font-weight:700; color:#18324e; margin-top:.15rem;}
.stage .s {font-size:.8rem; color:#66717f; margin-top:.15rem;}
.stage.ok {border-color:#b8d1c4; background:#f6faf7;}
.stage.bad {border-color:#e1c0c0; background:#fff7f7;}
.release-ready {border:1px solid #b8d1c4; background:#f3f8f5; padding:.85rem 1rem; border-radius:6px;}
.release-blocked {border:1px solid #dec8a8; background:#fff9ef; padding:.85rem 1rem; border-radius:6px;}
.fp {font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.78rem; color:#6d737a;}
</style>
"""

DEFECT_OPTIONS = [
    "Chinese naturalness",
    "Japanese instruction naturalness",
    "answer ambiguity / multiple answers",
    "weak distractors",
    "distractor too obviously false",
    "correct answer too obvious from wording",
    "material not actually needed",
    "fake integration",
    "scenario progression feels artificial",
    "excessive complexity / too many conditions",
    "too easy / too shallow",
    "source-integrity problem",
    "official-item surface reskin risk",
    "pre-2026 architecture drift",
    "renderer / page break / figure problem",
    "schema friction",
    "option-language mismatch",
    "A/B intro leaks or over-explains",
]

CHECK_LABELS = {
    "chinese_naturalness": "中文自然",
    "japanese_instruction_naturalness": "日语设问自然",
    "answer_uniqueness": "正答唯一",
    "distractors_plausible": "误答项有合理误读路径",
    "surface_fidelity_2026": "2026 题型 fidelity",
    "information_journey": "信息旅程自然",
    "visual_materials_necessary": "图表 / 资料确有必要",
    "originality_ok": "原创性 / 非换皮",
    "source_integrity_ok": "来源完整性",
    "layout_readable": "题面可读",
    "no_solution_leak": "无解法 / 答案泄漏",
}


def _load_current_source(root: Path) -> tuple[str, str]:
    st.sidebar.markdown("### 命題ライブラリ")
    show_history = st.sidebar.toggle("历史 / 失败样本", value=False)
    items = _discover_items(root, show_history=show_history)
    if not items:
        st.error("题目 JSON 未找到。请从 repository root 启动 UI。")
        st.stop()

    labels = list(items)
    preferred_id = st.session_state.get("preferred_item_id")
    preferred = 0
    if preferred_id:
        preferred = next((i for i, label in enumerate(labels) if preferred_id in label), 0)
    else:
        preferred = next(
            (
                i
                for i, label in enumerate(labels)
                if "q4_pilot_002_library_study_main2026.json" in label
            ),
            0,
        )

    selected_label = st.sidebar.selectbox("当前题目", labels, index=preferred)
    selected_path = items[selected_label]

    with st.sidebar.expander("上传 Item JSON", expanded=False):
        uploaded = st.file_uploader("item JSON", type=["json"], label_visibility="collapsed")
    st.sidebar.caption("默认只显示 active / approved / draft。失败样本默认隐藏。")

    if uploaded is not None:
        source_key = f"upload:{uploaded.name}:{uploaded.size}"
        source_text = uploaded.getvalue().decode("utf-8")
        source_name = uploaded.name
    else:
        source_key = str(selected_path)
        source_text = selected_path.read_text(encoding="utf-8")
        source_name = selected_path.name

    if st.session_state.get("editor_source") != source_key:
        st.session_state["editor_source"] = source_key
        st.session_state["editor_text"] = source_text

    return source_name, st.session_state["editor_text"]


def _candidate_path(root: Path, text: str) -> Path:
    return _write_ui_temp(root, text, "release_candidate.json")


def _show_review(item: Item, review: Review | None, root: Path) -> None:
    if review is None:
        st.caption("尚未保存 blind review。")
        return
    bound, binding_detail = review_binding_status(root, item)
    errors, warnings = compare_review(item, review)
    if bound and not errors:
        st.success("Blind review：当前版本通过")
    else:
        st.error("Blind review：当前版本未通过")
    st.caption(binding_detail)
    for error in errors:
        st.markdown(f"- {error}")
    for warning in warnings:
        st.warning(warning)
    if review.issues:
        with st.expander(f"Reviewer issues · {len(review.issues)}", expanded=True):
            for issue in review.issues:
                st.markdown(
                    f"- `{issue.severity}` **{issue.category}** — "
                    f"{issue.description} → {issue.suggested_fix}"
                )
    st.caption(review.overall_comment_ja)


def _human_qa_form(root: Path, item: Item) -> HumanQA | None:
    existing = load_human_qa_if_present(root, item.item_id)
    defaults = existing.checks.model_dump() if existing else {}
    if existing:
        bound, detail = human_qa_binding_status(root, item)
        if not bound:
            st.warning(detail)

    with st.form(f"human_qa_{item.item_id}"):
        c1, c2 = st.columns([2, 1])
        reviewer = c1.text_input("Reviewer", value=existing.reviewer if existing else "")
        dispositions = ["revise", "approve", "reject"]
        current = existing.disposition if existing else "revise"
        disposition = c2.selectbox("Disposition", dispositions, index=dispositions.index(current))

        st.markdown("**最终人工检查**")
        left, right = st.columns(2)
        check_values: dict[str, bool] = {}
        for index, (field, label) in enumerate(CHECK_LABELS.items()):
            box = left if index % 2 == 0 else right
            check_values[field] = box.checkbox(label, value=defaults.get(field, False))

        defects = st.multiselect(
            "本轮实际发生的返工问题",
            DEFECT_OPTIONS,
            default=existing.defects if existing else [],
        )

        st.markdown("**返工时间（分钟）**")
        timing = existing.timing if existing else HumanQATiming()
        t1, t2, t3, t4 = st.columns(4)
        first_read = t1.number_input("首次通读", 0, 600, timing.first_read_minutes)
        chinese_edit = t2.number_input("中文修改", 0, 600, timing.chinese_edit_minutes)
        item_edit = t3.number_input("命题修改", 0, 600, timing.item_edit_minutes)
        layout_edit = t4.number_input("版面修改", 0, 600, timing.layout_edit_minutes)

        r1, r2 = st.columns(2)
        tasks_rewritten = r1.number_input(
            "实质改写 tasks",
            0,
            len(item.tasks),
            existing.tasks_materially_rewritten if existing else 0,
        )
        materials_rewritten = r2.number_input(
            "实质改写 materials",
            0,
            len(item.materials),
            existing.materials_materially_rewritten if existing else 0,
        )

        b1, b2 = st.columns(2)
        answer_changed = b1.checkbox(
            "正答 key 修改过", value=existing.answer_key_changed if existing else False
        )
        blind_disagreed = b2.checkbox(
            "blind reviewer 曾与 key 不一致",
            value=existing.blind_reviewer_disagreed if existing else False,
        )
        b3, b4 = st.columns(2)
        high_ambiguity = b3.checkbox(
            "blind review 后仍发现高严重度歧义",
            value=existing.high_severity_ambiguity_after_blind if existing else False,
        )
        tex_repair = b4.checkbox(
            "需要人工修 TeX",
            value=existing.manual_tex_repair_required if existing else False,
        )

        biggest_rework = st.text_area(
            "最主要返工原因",
            value=existing.biggest_rework_cause if existing else "",
            height=72,
        )
        tool_change = st.text_area(
            "下一版工具最该改什么",
            value=existing.tool_change_note if existing else "",
            height=72,
        )
        submitted = st.form_submit_button("保存 Human QA", type="primary", use_container_width=True)

    if not submitted:
        return existing
    if not reviewer.strip():
        st.error("Reviewer 不能为空。")
        return existing

    qa = HumanQA(
        item_id=item.item_id,
        reviewer=reviewer.strip(),
        disposition=disposition,
        checks=HumanQAChecks(**check_values),
        defects=defects,
        timing=HumanQATiming(
            first_read_minutes=int(first_read),
            chinese_edit_minutes=int(chinese_edit),
            item_edit_minutes=int(item_edit),
            layout_edit_minutes=int(layout_edit),
        ),
        tasks_materially_rewritten=int(tasks_rewritten),
        materials_materially_rewritten=int(materials_rewritten),
        answer_key_changed=answer_changed,
        blind_reviewer_disagreed=blind_disagreed,
        high_severity_ambiguity_after_blind=high_ambiguity,
        manual_tex_repair_required=tex_repair,
        biggest_rework_cause=biggest_rework.strip(),
        tool_change_note=tool_change.strip(),
    )
    path = save_human_qa(root, qa, item=item)
    st.success(f"Human QA 已保存：{path.relative_to(root)}")
    return qa


def _pipeline_html(readiness) -> str:
    labels = ["结构校验", "Blind review", "Human QA", "题库相似度"]
    stages = []
    for index, gate in enumerate(readiness.gates):
        css = "ok" if gate.passed else "bad"
        status = "PASS" if gate.passed else "WAIT"
        stages.append(
            f'<div class="stage {css}"><div class="n">STEP {index + 1}</div>'
            f'<div class="t">{labels[index] if index < len(labels) else gate.name}</div>'
            f'<div class="s">{status}</div></div>'
        )
    return '<div class="pipeline">' + "".join(stages) + "</div>"


def _render_gates(readiness) -> None:
    st.markdown(_pipeline_html(readiness), unsafe_allow_html=True)
    with st.expander("查看 gate 详情", expanded=not readiness.ready):
        for gate in readiness.gates:
            icon = "✅" if gate.passed else "⛔"
            st.markdown(f"{icon} **{gate.name}** — {gate.detail}")


def main() -> None:
    st.set_page_config(
        page_title="TABITO 中国語命題 Workbench",
        page_icon="📘",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(APP_CSS + WORKBENCH_CSS, unsafe_allow_html=True)
    root = _root()
    source_name, current_text = _load_current_source(root)

    item, parse_error = _parse_item(current_text)
    validated_item, errors, warnings = _validation_result(root, current_text)
    if item is None and validated_item is not None:
        item = validated_item

    st.markdown(
        '<div class="tabito-kicker">TABITO EDUCATION · CONTENT PRODUCTION</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tabito-title">共通テスト中国語 命題 Workbench</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tabito-sub">2026 本試験・追試験を一次蓝本にした命題 → 审题 → Release</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="status-row">{_status_pills(item, errors, warnings)}</div>',
        unsafe_allow_html=True,
    )
    if item:
        st.markdown(
            f'<div class="fp">content fingerprint · {item_fingerprint(item)[:16]}</div>',
            unsafe_allow_html=True,
        )

    preview_tab, generate_tab, review_tab, release_tab, edit_tab = st.tabs(
        ["📄 试卷", "✨ 命题", "✅ 审题", "🚀 Release", "🛠 编辑 / 导出"]
    )

    with preview_tab:
        if item is None:
            st.error("当前 JSON 无法解析。")
            st.code(parse_error or "unknown parse error", language=None)
        else:
            view = st.radio(
                "视图",
                ["学生册", "教师标注", "结构检查"],
                horizontal=True,
                label_visibility="collapsed",
            )
            if view == "学生册":
                st.caption("先从考生视角判断：题面是否真的像 2026 共通。")
                with st.container(border=True):
                    _render_booklet_preview(item)
            elif view == "教师标注":
                _render_teacher_view(item)
            else:
                _render_structure_view(item)

    with generate_tab:
        st.subheader("1 · 创建命题请求")
        family_choice = st.radio(
            "2026 family",
            ["main_2026", "makeup_2026"],
            format_func=lambda value: FAMILY_LABELS[value],
            horizontal=True,
        )
        st.info(FAMILY_SUMMARIES[family_choice])
        with st.form("new_item_form"):
            topic = st.text_input("主题 / 情境", placeholder="例如：地域施設の利用改善")
            notes = st.text_area("补充要求", height=90)
            with st.expander("高级设置", expanded=False):
                c1, c2, c3 = st.columns(3)
                difficulty = c1.selectbox("难度", ["official_like", "easy", "medium", "hard"])
                scope = c2.selectbox("范围", ["full", "mini"])
                domain = c3.text_input("domain", value="auto")
            make_prompt = st.form_submit_button("生成 Prompt", type="primary", use_container_width=True)

        if make_prompt:
            if not topic.strip():
                st.error("请输入主题。")
            else:
                item_id, request_path, spec_path = create_q4_request(
                    root,
                    topic=topic.strip(),
                    difficulty=difficulty,
                    domain=domain.strip() or "auto",
                    scope=scope,
                    notes=notes.strip() or None,
                    surface_family=family_choice,
                )
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
                st.session_state["request_binding"] = spec
                st.session_state["last_request"] = request_path.read_text(encoding="utf-8")
                st.session_state["last_request_path"] = str(request_path)
                st.session_state["last_spec_path"] = str(spec_path)
                st.success(f"已生成 {item_id}")

        if st.session_state.get("last_request"):
            st.text_area(
                "复制到 ChatGPT",
                st.session_state["last_request"],
                height=285,
                key="request_preview",
            )
            c1, c2 = st.columns(2)
            with c1:
                _download_file(Path(st.session_state["last_request_path"]), "下载 request.md", "text/markdown")
            with c2:
                _download_file(Path(st.session_state["last_spec_path"]), "下载 spec.json", "application/json")

        st.divider()
        st.subheader("2 · 导入生成结果")
        binding = st.session_state.get("request_binding")
        if binding:
            st.caption(
                f"当前绑定：{binding['item_id']} · {FAMILY_LABELS[binding['surface_family']]} · "
                f"{binding['blueprint_version']}"
            )
        else:
            st.warning("当前没有本 session 的 request 绑定；仍可导入，但不会核对 request ID。")

        response_text = st.text_area(
            "Generated item JSON",
            height=300,
            key="generated_response_text",
            label_visibility="collapsed",
            placeholder='{"schema_version":"0.2", ...}',
        )
        if st.button("导入为 Draft 并校验", type="primary", use_container_width=True):
            if not response_text.strip():
                st.error("请先粘贴生成结果。")
            else:
                try:
                    kwargs = {}
                    if binding:
                        kwargs = {
                            "expected_item_id": binding["item_id"],
                            "expected_surface_family": binding["surface_family"],
                            "expected_blueprint_version": binding["blueprint_version"],
                        }
                    imported, response_path, draft_path, import_errors, import_warnings = (
                        import_item_response(root, response_text, **kwargs)
                    )
                    st.success(f"已导入 Draft：{draft_path.relative_to(root)}")
                    st.caption(f"原始响应保留：{response_path.relative_to(root)}")
                    _render_validation(import_errors, import_warnings)
                    st.session_state["preferred_item_id"] = imported.item_id
                    st.session_state.pop("editor_source", None)
                except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                    st.error(str(exc))

    with review_tab:
        if item is None:
            st.warning("先导入或修正 Item JSON。")
        else:
            candidate_path = _candidate_path(root, current_text)
            st.subheader("1 · Deterministic QA")
            _render_validation(errors, warnings)

            st.divider()
            st.subheader("2 · Blind Review")
            saved_review = load_review_if_present(root, item.item_id)
            _show_review(item, saved_review, root)

            if st.button("生成 Blind Review Prompt", use_container_width=True):
                prompt_path = create_review_request(root, candidate_path)
                st.session_state["blind_prompt"] = prompt_path.read_text(encoding="utf-8")
                st.session_state["blind_prompt_path"] = str(prompt_path)
            if st.session_state.get("blind_prompt"):
                st.text_area(
                    "复制到独立 ChatGPT 对话",
                    st.session_state["blind_prompt"],
                    height=260,
                )
                _download_file(
                    Path(st.session_state["blind_prompt_path"]),
                    "下载 review_request.md",
                    "text/markdown",
                )

            review_text = st.text_area(
                "粘贴 reviewer JSON",
                height=210,
                key="review_response_text",
                placeholder='{"schema_version":"0.2", ...}',
            )
            if st.button("保存并检查 Blind Review", type="primary", use_container_width=True):
                if not review_text.strip():
                    st.error("请先粘贴 reviewer JSON。")
                else:
                    try:
                        review, path = import_review_response(root, review_text, item=item)
                        st.success(f"Review 已保存：{path.relative_to(root)}")
                        _show_review(item, review, root)
                    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                        st.error(str(exc))

            active_review = load_review_if_present(root, item.item_id)
            if active_review:
                bound, _ = review_binding_status(root, item)
                if bound and (active_review.verdict != "pass" or active_review.issues):
                    if st.button("根据当前 review 生成修订 Prompt", use_container_width=True):
                        review_file = root / "workspace" / "reviews" / f"{item.item_id}.review.json"
                        revision_path = create_revision_request(root, candidate_path, review_file)
                        st.text_area(
                            "Revision prompt",
                            revision_path.read_text(encoding="utf-8"),
                            height=280,
                        )
                        _download_file(revision_path, "下载 revision_request.md", "text/markdown")

            st.divider()
            st.subheader("3 · Human QA")
            qa = _human_qa_form(root, item)
            if qa:
                st.caption(
                    f"累计人工返工：{qa.timing.total_minutes} min · disposition={qa.disposition}"
                )

    with release_tab:
        if item is None:
            st.warning("当前没有可发布的 item。")
        else:
            candidate_path = _candidate_path(root, current_text)
            readiness = release_readiness(root, candidate_path)
            st.subheader("Release readiness")
            _render_gates(readiness)
            st.markdown(
                f'<div class="fp">current fingerprint · {readiness.fingerprint}</div>',
                unsafe_allow_html=True,
            )

            if readiness.ready:
                st.markdown(
                    '<div class="release-ready"><b>可以发布</b><br>'
                    '当前版本的结构校验、blind review、human QA、题库相似度全部通过。</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Approve → 进入正式题库", type="primary", use_container_width=True):
                    try:
                        target, _ = approve_item(root, candidate_path)
                        st.session_state["preferred_item_id"] = item.item_id
                        st.session_state.pop("editor_source", None)
                        st.success(f"已进入正式题库：{target.relative_to(root)}")
                    except ValueError as exc:
                        st.error(str(exc))
            else:
                st.markdown(
                    '<div class="release-blocked"><b>暂不可发布</b><br>'
                    '先处理上方未通过的 gate；题目内容一旦修改，旧 review / QA 会自动失效。</div>',
                    unsafe_allow_html=True,
                )

    with edit_tab:
        st.subheader("高级 JSON 编辑")
        st.caption("这里只用于精确修字段。保存后 workflow 会回到 draft，旧审题证据按 fingerprint 自动失效。")
        edited = st.text_area(
            "Item JSON",
            key="editor_text",
            height=500,
            label_visibility="collapsed",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("重新校验", use_container_width=True):
                _, edit_errors, edit_warnings = _validation_result(root, edited)
                _render_validation(edit_errors, edit_warnings)
        with c2:
            if st.button("保存为 Draft", use_container_width=True):
                try:
                    candidate = Item.model_validate(json.loads(edited))
                    path = save_draft(root, candidate)
                    st.session_state["editor_text"] = path.read_text(encoding="utf-8")
                    st.session_state["preferred_item_id"] = candidate.item_id
                    st.success(f"已保存：{path.relative_to(root)}")
                except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                    st.error(str(exc))

        st.divider()
        st.subheader("PDF / TeX")
        st.caption("网页预览不依赖 LaTeX；PDF 编译需要本机 XeLaTeX。")
        if item and st.button("生成学生版 / 教师版", use_container_width=True):
            try:
                out_dir = root / "output" / item.item_id
                student_tex = render_item_tex(item, out_dir, teacher=False)
                teacher_tex = render_item_tex(item, out_dir, teacher=True)
                student_pdf = compile_xelatex(student_tex)
                teacher_pdf = compile_xelatex(teacher_tex)
                c1, c2 = st.columns(2)
                with c1:
                    _download_file(
                        student_pdf or student_tex,
                        "学生版 PDF" if student_pdf else "学生版 TeX",
                        "application/pdf" if student_pdf else "text/plain",
                    )
                with c2:
                    _download_file(
                        teacher_pdf or teacher_tex,
                        "教师版 PDF" if teacher_pdf else "教师版 TeX",
                        "application/pdf" if teacher_pdf else "text/plain",
                    )
            except Exception as exc:
                st.error(f"导出失败：{exc}")

        with st.expander("当前系统信息", expanded=False):
            st.json(
                {
                    "source": source_name,
                    "blueprint": item.workflow.blueprint_version if item else BLUEPRINT_VERSION,
                    "surface_family": item.surface_family if item else None,
                    "workflow_state": item.workflow.state if item else None,
                }
            )


if __name__ == "__main__":
    main()

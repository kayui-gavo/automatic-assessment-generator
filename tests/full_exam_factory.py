from __future__ import annotations

from pathlib import Path

from tabito_itemgen.exam_models import (
    ArticleAnchor,
    ArticleParagraph,
    ExamManifest,
    OrderingToken,
    PinyinDialogueLine,
    PinyinWord,
    Q1DialogueTask,
    Q1PhoneticCountTask,
    Q1Section,
    Q2FillTask,
    Q2OrderingTask,
    Q2Section,
    Q3Section,
    Q3TranslationTask,
    Q5AnswerSlot,
    Q5Section,
    Q5Task,
)
from tabito_itemgen.exam_production import create_exam_project, import_section_response, manifest_path
from tabito_itemgen.io import load_json
from tabito_itemgen.models import AnswerSlot, Item

ROOT = Path(__file__).resolve().parents[1]


def q1(section_id: str) -> Q1Section:
    count_options = ["一つ", "二つ", "三つ", "四つ", "なし"]
    words = [
        PinyinWord(label="a", hanzi="看", pinyin="kàn"),
        PinyinWord(label="b", hanzi="高", pinyin="gāo"),
        PinyinWord(label="c", hanzi="课", pinyin="kè"),
        PinyinWord(label="d", hanzi="好", pinyin="hǎo"),
    ]
    tasks = [
        Q1PhoneticCountTask(
            task_id="Q1-A",
            subsection="A",
            order=1,
            target="initial",
            prompt_ja="見出し語と声母が同じものはいくつあるか。",
            headword=PinyinWord(label="見出し", hanzi="开", pinyin="kāi"),
            candidates=words,
            options=count_options,
            answer_slot=AnswerSlot(slot_id="Q1-1", answer_number=1, correct_option=3),
            rationale_ja="kで始まる語が三つある。",
        ),
        Q1PhoneticCountTask(
            task_id="Q1-B",
            subsection="B",
            order=2,
            target="final",
            prompt_ja="声調を除き、見出し語と韻母が同じものはいくつあるか。",
            headword=PinyinWord(label="見出し", hanzi="忙", pinyin="máng"),
            candidates=[
                PinyinWord(label="a", hanzi="长", pinyin="cháng"),
                PinyinWord(label="b", hanzi="能", pinyin="néng"),
                PinyinWord(label="c", hanzi="房", pinyin="fáng"),
                PinyinWord(label="d", hanzi="冷", pinyin="lěng"),
            ],
            options=count_options,
            answer_slot=AnswerSlot(slot_id="Q1-2", answer_number=2, correct_option=2),
            rationale_ja="-angが二つ。",
        ),
        Q1PhoneticCountTask(
            task_id="Q1-C1",
            subsection="C",
            order=3,
            target="tone_pattern",
            prompt_ja="見出し語と声調の組合せが同じものはいくつあるか。",
            headword=PinyinWord(label="見出し", hanzi="明天", pinyin="míngtiān"),
            candidates=[
                PinyinWord(label="a", hanzi="时间", pinyin="shíjiān"),
                PinyinWord(label="b", hanzi="学生", pinyin="xuéshēng"),
                PinyinWord(label="c", hanzi="昨天", pinyin="zuótiān"),
                PinyinWord(label="d", hanzi="学校", pinyin="xuéxiào"),
            ],
            options=count_options,
            answer_slot=AnswerSlot(slot_id="Q1-3", answer_number=3, correct_option=3),
            rationale_ja="二声＋一声が三つ。",
        ),
        Q1PhoneticCountTask(
            task_id="Q1-C2",
            subsection="C",
            order=4,
            target="tone_pattern",
            prompt_ja="見出し語と声調の組合せが同じものはいくつあるか。",
            headword=PinyinWord(label="見出し", hanzi="下午", pinyin="xiàwǔ"),
            candidates=[
                PinyinWord(label="a", hanzi="电脑", pinyin="diànnǎo"),
                PinyinWord(label="b", hanzi="电影", pinyin="diànyǐng"),
                PinyinWord(label="c", hanzi="饭馆", pinyin="fànguǎn"),
                PinyinWord(label="d", hanzi="朋友", pinyin="péngyou"),
            ],
            options=count_options,
            answer_slot=AnswerSlot(slot_id="Q1-4", answer_number=4, correct_option=3),
            rationale_ja="四声＋三声が三つ。",
        ),
        Q1DialogueTask(
            task_id="Q1-D1",
            order=5,
            lines=[
                PinyinDialogueLine(speaker="A", pinyin="Nǐ míngtiān yǒu shíjiān ma?"),
                PinyinDialogueLine(speaker="B", pinyin="Shàngwǔ yào shàngkè, xiàwǔ kěyǐ."),
            ],
            prompt_ja="Bが会えるのはいつか。",
            options=["今日の午前", "今日の午後", "明日の午前", "明日の午後"],
            answer_slot=AnswerSlot(slot_id="Q1-5", answer_number=5, correct_option=4),
            rationale_ja="午後なら会えると答えている。",
        ),
        Q1DialogueTask(
            task_id="Q1-D2",
            order=6,
            lines=[
                PinyinDialogueLine(speaker="A", pinyin="Wǒmen zuò dìtiě qù ba."),
                PinyinDialogueLine(speaker="B", pinyin="Jīntiān xià yǔ, wǒ xiǎng zuò gōnggòng qìchē."),
            ],
            prompt_ja="Bは何を提案しているか。",
            options=["歩く", "地下鉄に乗る", "バスに乗る", "予定をやめる"],
            answer_slot=AnswerSlot(slot_id="Q1-6", answer_number=6, correct_option=3),
            rationale_ja="雨なのでバスに乗りたいと言っている。",
        ),
    ]
    return Q1Section(section_id=section_id, tasks=tasks)


def q2(section_id: str) -> Q2Section:
    fill_a = Q2FillTask(
        task_id="Q2-A",
        subsection="A",
        order=1,
        selection_rule="appropriate",
        sentence_zh="今天有点冷，你＿＿＿多穿一件衣服。",
        prompt_ja="空欄に入れるのに最も適当なものを選べ。",
        options=["应该", "已经", "一直", "一起"],
        answer_slot=AnswerSlot(slot_id="Q2-7", answer_number=7, correct_option=1),
        rationale_ja="助言には“应该”が自然。",
    )
    fill_b = Q2FillTask(
        task_id="Q2-B",
        subsection="B",
        order=2,
        selection_rule="inappropriate",
        sentence_zh="他＿＿＿喜欢在图书馆学习。",
        prompt_ja="空欄に入れるのに適当でないものを選べ。",
        options=["很", "也", "不", "把"],
        answer_slot=AnswerSlot(slot_id="Q2-8", answer_number=8, correct_option=4),
        rationale_ja="“把”はこの述語の前に単独では置けない。",
    )
    order1 = Q2OrderingTask(
        task_id="Q2-C1",
        order=3,
        source_ja="私は昨日、友達と一緒に新しい本屋へ行きました。",
        sentence_frame_zh="我昨天 ＿＿ ＿＿ ＿＿ ＿＿ 。",
        prompt_ja="八つの語句から四つを選び、正しい中国語文を作れ。指定位置の語句番号を答えよ。",
        token_pool=[
            OrderingToken(token_id=1, text_zh="跟朋友"),
            OrderingToken(token_id=2, text_zh="一起"),
            OrderingToken(token_id=3, text_zh="去了"),
            OrderingToken(token_id=4, text_zh="新书店"),
            OrderingToken(token_id=5, text_zh="正在"),
            OrderingToken(token_id=6, text_zh="因为"),
            OrderingToken(token_id=7, text_zh="把"),
            OrderingToken(token_id=8, text_zh="才"),
        ],
        correct_sequence=[1, 2, 3, 4],
        answer_positions=[2, 4],
        answer_slots=[
            AnswerSlot(slot_id="Q2-9", answer_number=9, correct_option=2),
            AnswerSlot(slot_id="Q2-10", answer_number=10, correct_option=4),
        ],
        rationale_ja="跟朋友一起去了新书店。",
    )
    order2 = Q2OrderingTask(
        task_id="Q2-C2",
        order=4,
        source_ja="先生は私たちに授業の前にこの文章を読むように言いました。",
        sentence_frame_zh="老师 ＿＿ ＿＿ ＿＿ ＿＿ 。",
        prompt_ja="八つの語句から四つを選び、正しい中国語文を作れ。指定位置の語句番号を答えよ。",
        token_pool=[
            OrderingToken(token_id=1, text_zh="让我们"),
            OrderingToken(token_id=2, text_zh="上课以前"),
            OrderingToken(token_id=3, text_zh="读"),
            OrderingToken(token_id=4, text_zh="这篇文章"),
            OrderingToken(token_id=5, text_zh="被"),
            OrderingToken(token_id=6, text_zh="虽然"),
            OrderingToken(token_id=7, text_zh="已经"),
            OrderingToken(token_id=8, text_zh="从"),
        ],
        correct_sequence=[1, 2, 3, 4],
        answer_positions=[1, 3],
        answer_slots=[
            AnswerSlot(slot_id="Q2-11", answer_number=11, correct_option=1),
            AnswerSlot(slot_id="Q2-12", answer_number=12, correct_option=3),
        ],
        rationale_ja="老师让我们上课以前读这篇文章。",
    )
    return Q2Section(section_id=section_id, tasks=[fill_a, fill_b, order1, order2])


def _q3_task(task_id: str, subsection: str, direction: str, answer: int, correct: int) -> Q3TranslationTask:
    if direction == "ja_to_zh":
        source = f"例文{answer}：今日は時間があれば図書館へ行きます。"
        options = [
            "Jīntiān yǒu shíjiān dehuà, wǒ jiù qù túshūguǎn.",
            "Jīntiān méiyǒu shíjiān, wǒ yě qù túshūguǎn.",
            "Zuótiān yǒu shíjiān dehuà, wǒ jiù qù túshūguǎn.",
            "Jīntiān yǒu shíjiān, túshūguǎn jiù lái wǒ.",
        ]
    else:
        source = "Rúguǒ míngtiān bú xià yǔ, wǒmen jiù qù gōngyuán ba."
        options = ["明日雨が降らなければ、公園へ行きましょう。", "明日雨なら、公園へ行きません。", "昨日雨が降らなかったので、公園へ行きました。", "公園へ行けば、明日は雨です。"]
    wrong = {str(index) for index in range(1, 5) if index != correct}
    error_types = {key: ["lexical_meaning"] for key in wrong}
    reasons = {key: "原文の条件・時間・主体のいずれかが一致しない。" for key in wrong}
    return Q3TranslationTask(
        task_id=task_id,
        subsection=subsection,
        order=answer,
        direction=direction,
        source_text=source,
        prompt_ja="最も適当な対応を選べ。",
        options=options,
        answer_slot=AnswerSlot(slot_id=f"Q3-{answer}", answer_number=answer, correct_option=correct),
        rationale_ja="文全体の条件関係と意味が一致する。",
        distractor_error_types=error_types,
        distractor_rationales_ja=reasons,
    )


def q3(section_id: str) -> Q3Section:
    tasks = [
        _q3_task(f"Q3-A{index}", "A", "ja_to_zh", answer, 1)
        for index, answer in enumerate(range(13, 17), start=1)
    ]
    tasks += [
        _q3_task(f"Q3-B{index}", "B", "zh_to_ja", answer, 1)
        for index, answer in enumerate(range(17, 21), start=1)
    ]
    return Q3Section(section_id=section_id, tasks=tasks)


def q4(section_id: str, family: str = "main_2026") -> Item:
    source = ROOT / "pilots" / (
        "q4_pilot_002_library_study_main2026.json"
        if family == "main_2026"
        else "q4_pilot_003_stargazing_makeup2026_v2.json"
    )
    item = Item.model_validate(load_json(source)).model_copy(deep=True)
    item.item_id = section_id
    item.surface_family = family
    return item


def q5(section_id: str, family: str = "main_2026") -> Q5Section:
    paragraphs = [
        ArticleParagraph(paragraph_id="P1", text_zh="周末，林悦第一次参加社区的旧书交换活动。她原来只想把家里的几本书送出去，却发现很多人会先读书里留下的小纸条。"),
        ArticleParagraph(paragraph_id="P2", text_zh="一位老人告诉她，这些纸条记录了上一位读者为什么喜欢这本书。林悦开始觉得，交换的不只是书，也是读书时留下的想法。"),
        ArticleParagraph(paragraph_id="P3", text_zh="活动结束时，她没有急着拿走最热门的书，而是选了一本几乎没人注意的小册子。她想先看看陌生人的一句话，会不会让自己用新的眼光读它。"),
    ]
    anchors = [
        ArticleAnchor(anchor_id=f"A{index}", paragraph_id=f"P{min(index, 3)}", kind="phrase", marker_label=f"下線部{index}")
        for index in range(1, 4)
    ]
    if family == "main_2026":
        groups = {
            1: [37, 38], 2: [39], 3: [40], 4: [41], 5: [42], 6: [43],
            7: [44], 8: [45], 9: [46], 10: [47, 48], 11: [49, 50],
        }
    else:
        groups = {
            1: [37], 2: [38], 3: [39], 4: [40, 41], 5: [42], 6: [43],
            7: [44], 8: [45, 46], 9: [47, 48], 10: [49, 50],
        }
    tasks: list[Q5Task] = []
    for qno, numbers in groups.items():
        multi = len(numbers) > 1
        operation = "whole_text_consistency" if qno == max(groups) else (
            "lexical_choice" if qno in {2, 3, 4, 5, 6, 7, 8, 9, 10} and qno % 3 == 1 else "content_understanding"
        )
        slots = [
            Q5AnswerSlot(slot_id=f"Q5-{number}", answer_number=number, correct_option=index + 1)
            for index, number in enumerate(numbers)
        ]
        options = ["内容に合う選択肢A", "内容に合う選択肢B", "内容に合う選択肢C", "内容に合う選択肢D", "内容に合う選択肢E"]
        tasks.append(
            Q5Task(
                task_id=f"Q5-Q{qno}",
                question_no=qno,
                order=qno,
                prompt_ja="本文の内容に照らして最も適当なものを選べ。" if not multi else "本文の内容に合うものを二つ選べ。",
                options=options,
                response_mode="multi_select" if multi else "single_choice",
                answer_slots=slots,
                anchor_refs=["A1"] if qno < max(groups) else [],
                operation=operation,
                rationale_ja="本文の情報を統合するとこの選択肢になる。",
            )
        )
    return Q5Section(
        section_id=section_id,
        surface_family=family,
        topic="社区旧书交换与阅读体验",
        paragraphs=paragraphs,
        anchors=anchors,
        tasks=tasks,
        originality_statement="社区旧书交换这一原创情境独立设计，人物、事件、段落推进均不复用2026官方题。",
    )


def build_exam(root: Path, family: str = "main_2026") -> tuple[ExamManifest, Path]:
    manifest, path = create_exam_project(root, exam_family=family, title_ja="Schema Fixture 模試")
    builders = {"Q1": q1, "Q2": q2, "Q3": q3}
    for ref in manifest.sections:
        if ref.section in builders:
            section = builders[ref.section](ref.section_id)
        elif ref.section == "Q4":
            section = q4(ref.section_id, family)
        else:
            section = q5(ref.section_id, family)
        import_section_response(root, manifest.exam_id, ref.section, section.model_dump_json())
    return ExamManifest.model_validate(load_json(manifest_path(root, manifest.exam_id))), path

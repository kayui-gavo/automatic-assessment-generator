from __future__ import annotations

from collections import defaultdict

from .models import Item, Task

FAMILY_LABELS = {
    "main_2026": "2026 本試験型",
    "makeup_2026": "2026 追試験型",
}

FAMILY_SUMMARIES = {
    "main_2026": "会話→調査資料→説明→条件照合→プロフィール→フロー／case適用",
    "makeup_2026": "会話→調査→説明+図→メモ→日時計画→複合資料→安全情報→振り返り",
}


def answer_numbers(task: Task) -> tuple[int, ...]:
    return tuple(sorted(slot.answer_number for slot in task.answer_slots))


def question_number(surface_family: str | None, subsection: str, task: Task) -> int:
    first = min(answer_numbers(task))
    if subsection == "A":
        if first <= 22:
            return 1
        if first <= 26:
            return 2
        return 3

    if surface_family == "main_2026":
        if first <= 30:
            return 1
        if first <= 33:
            return 2
        return 3

    if first <= 30:
        return 1
    if first <= 34:
        return 2
    return 3


def tasks_for_subsection(item: Item, subsection: str) -> list[Task]:
    return sorted(
        [task for task in item.tasks if task.subsection == subsection],
        key=lambda task: task.order,
    )


def task_groups(item: Item, subsection: str) -> dict[int, list[Task]]:
    groups: dict[int, list[Task]] = defaultdict(list)
    for task in tasks_for_subsection(item, subsection):
        groups[question_number(item.surface_family, subsection, task)].append(task)
    return dict(sorted(groups.items()))


def owner_task_for_order(tasks: list[Task], order: int) -> Task:
    later = [task for task in tasks if task.order >= order]
    if later:
        return min(later, key=lambda task: task.order)
    return max(tasks, key=lambda task: task.order)


def subquestion_index(item: Item, task: Task) -> int | None:
    group = task_groups(item, task.subsection).get(
        question_number(item.surface_family, task.subsection, task), []
    )
    if len(group) <= 1:
        return None
    return group.index(task) + 1


def subsection_intro(item: Item, subsection: str) -> str:
    explicit = item.subsection_intros_ja.get(subsection)
    if explicit:
        return explicit
    if subsection == "A":
        return (
            f"高校生が「{item.title_ja}」について調べている。"
            "次の会話や資料を読み，後の問い（問1～3）に答えよ。"
        )
    return (
        f"引き続き「{item.title_ja}」について，別の場面で資料を利用する。"
        "次の問い（問1～3）に答えよ。"
    )


def timeline(item: Item, subsection: str) -> list[tuple[int, str, object]]:
    blocks: list[tuple[int, str, object]] = []
    blocks.extend(
        (material.order, "material", material)
        for material in item.materials
        if material.subsection == subsection
    )
    blocks.extend(
        (task.order, "task", task)
        for task in item.tasks
        if task.subsection == subsection
    )
    return sorted(blocks, key=lambda value: value[0])


def slot_group_summary(item: Item) -> str:
    parts: list[str] = []
    for subsection in ("A", "B"):
        groups = task_groups(item, subsection)
        rendered = []
        for qno, tasks in groups.items():
            slots = ["-".join(map(str, answer_numbers(task))) for task in tasks]
            rendered.append(f"問{qno}: {' / '.join(slots)}")
        parts.append(f"{subsection} {' | '.join(rendered)}")
    return "  ·  ".join(parts)

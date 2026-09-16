from __future__ import annotations

from dataclasses import dataclass

from .exam_models import ArticleParagraph, Q2OrderingTask, Q5Section

SECTION_INSTRUCTIONS: dict[int, str] = {
    1: "次の問い（A～D）に答えよ。",
    2: "次の問い（A～C）に答えよ。",
    3: "次の問い（A・B）に答えよ。",
    4: "次の問い（A・B）に答えよ。",
    5: "次の問いに答えよ。",
}


@dataclass(frozen=True)
class OrderingSurfacePart:
    text: str = ""
    answer_number: int | None = None


@dataclass(frozen=True)
class Q5SurfaceSegment:
    text: str
    kind: str = "plain"
    marker_label: str | None = None


def section_instruction(number: int) -> str:
    return SECTION_INSTRUCTIONS[number]


def ordering_surface_parts(task: Q2OrderingTask) -> tuple[OrderingSurfacePart, ...]:
    """Expose the four ordering blanks with answer boxes at asked positions.

    This helper is deliberately renderer-agnostic so Streamlit and XeLaTeX
    cannot disagree about which physical blank corresponds to answer 9/10/11/12.
    """

    parts = task.sentence_frame_zh.split("＿＿")
    blank_count = len(parts) - 1
    if blank_count != len(task.correct_sequence):
        raise ValueError(
            f"{task.task_id}: sentence frame has {blank_count} blanks but "
            f"correct_sequence has {len(task.correct_sequence)} positions"
        )
    if len(task.answer_positions) != len(task.answer_slots):
        raise ValueError(f"{task.task_id}: answer_positions and answer_slots must have the same length")

    slot_by_position = {
        position: slot.answer_number
        for position, slot in zip(task.answer_positions, task.answer_slots, strict=True)
    }
    result: list[OrderingSurfacePart] = [OrderingSurfacePart(text=parts[0])]
    for position in range(1, blank_count + 1):
        result.append(OrderingSurfacePart(answer_number=slot_by_position.get(position)))
        result.append(OrderingSurfacePart(text=parts[position]))
    return tuple(result)


def _next_anchor_position(
    section: Q5Section,
    paragraph: ArticleParagraph,
    cursor: int,
) -> tuple[int, object, str] | None:
    candidates = []
    for anchor in section.anchors:
        if anchor.paragraph_id != paragraph.paragraph_id:
            continue
        if anchor.marker_label:
            token = f"〔{anchor.marker_label}〕"
            position = paragraph.text_zh.find(token, cursor)
            if position >= 0:
                candidates.append((position, anchor, token))
    if not candidates:
        return None
    return min(candidates, key=lambda value: value[0])


def q5_surface_segments(section: Q5Section, paragraph: ArticleParagraph) -> tuple[Q5SurfaceSegment, ...]:
    """Turn visible Q5 marker metadata into renderer-neutral text segments.

    The marker remains visible, while a blank gains a real blank segment and a
    source_excerpt gains an underline segment.  Both PDF and browser preview
    use the same source-to-surface interpretation.
    """

    source = paragraph.text_zh
    result: list[Q5SurfaceSegment] = []
    cursor = 0
    while True:
        found = _next_anchor_position(section, paragraph, cursor)
        if found is None:
            if cursor < len(source):
                result.append(Q5SurfaceSegment(source[cursor:]))
            break
        position, anchor, marker = found
        if position > cursor:
            result.append(Q5SurfaceSegment(source[cursor:position]))
        result.append(Q5SurfaceSegment(marker, kind="marker", marker_label=anchor.marker_label))
        cursor = position + len(marker)

        if anchor.kind == "blank":
            result.append(Q5SurfaceSegment("", kind="blank", marker_label=anchor.marker_label))
            continue

        if anchor.source_excerpt and source.startswith(anchor.source_excerpt, cursor):
            result.append(
                Q5SurfaceSegment(
                    anchor.source_excerpt,
                    kind="underline",
                    marker_label=anchor.marker_label,
                )
            )
            cursor += len(anchor.source_excerpt)

    return tuple(result)

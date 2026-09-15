from __future__ import annotations

from .exam_models import Q1PhoneticCountTask, Q1Section

# Author-side fields that must never be shown to an independent solver.
# This list is shared by the legacy Q4 workflow and the full Q1-Q5 workflow so
# the two review paths cannot silently drift apart.
HIDDEN_AUTHOR_KEYS = frozenset(
    {
        "correct_option",
        "rationale_ja",
        "distractor_rationales_ja",
        "slot_distractor_rationales_ja",
        "distractor_error_types",
        "token_rationales_ja",
        "correct_sequence",
        "quality_notes",
        "workflow",
        "originality_statement",
        "surface_family",
        "topic",
        "scenario_summary_ja",
        "difficulty",
        "dependency_mode",
        "bundle_id",
        "evidence",
        "operations",
        "anchor_refs",
        "operation",
        # Pure authoring / transport metadata. These are never printed on the
        # student booklet and therefore must not bias an independent solver.
        "schema_version",
        "section_id",
        "item_id",
        "slot_id",
    }
)


def _strip_author_keys(value):
    if isinstance(value, dict):
        return {
            key: _strip_author_keys(child)
            for key, child in value.items()
            if key not in HIDDEN_AUTHOR_KEYS
        }
    if isinstance(value, list):
        return [_strip_author_keys(child) for child in value]
    return value


def _q1_blind_surface(section: Q1Section) -> dict:
    """Return Q1 as booklet-visible content plus minimal review bookkeeping.

    Q1 is especially easy to leak because ``PinyinWord`` contains authoring
    labels, pinyin and a semantic ``target`` field. The booklet only shows the
    Hanzi, the visible underline position, fixed candidate labels a-d, prompts,
    options and answer-box numbers. Build that surface explicitly instead of
    serializing the internal model and trying to blacklist fields afterwards.
    """

    tasks: list[dict] = []
    for task in section.tasks:
        if isinstance(task, Q1PhoneticCountTask):
            tasks.append(
                {
                    "task_id": task.task_id,
                    "subsection": task.subsection,
                    "prompt_ja": task.prompt_ja,
                    "headword": {
                        "hanzi": task.headword.hanzi,
                        "target_index": task.headword.target_index,
                    },
                    "candidates": [
                        {
                            # Candidate labels are a presentation convention, not
                            # trusted model content. Derive a-d from list position.
                            "label": chr(ord("a") + index),
                            "hanzi": candidate.hanzi,
                            "target_index": candidate.target_index,
                        }
                        for index, candidate in enumerate(task.candidates)
                    ],
                    "options": list(task.options),
                    "answer_slot": {"answer_number": task.answer_slot.answer_number},
                }
            )
            continue

        tasks.append(
            {
                "task_id": task.task_id,
                "subsection": task.subsection,
                "lines": [
                    {"speaker": line.speaker, "pinyin": line.pinyin}
                    for line in task.lines
                ],
                "prompt_ja": task.prompt_ja,
                "options": list(task.options),
                "answer_slot": {"answer_number": task.answer_slot.answer_number},
            }
        )

    return {
        "section": "Q1",
        "title_ja": section.title_ja,
        "score": section.score,
        "tasks": tasks,
    }


def blind_section_dict(section) -> dict:
    """Return only information an independent solver may legitimately see.

    The result is stricter than merely deleting answer keys: answer-side
    rationales, evidence links, intended cognitive-operation labels and pure
    transport metadata are removed. Metadata that is necessary to reconstruct
    an actually visible booklet feature may remain. For example, Q5
    ``source_excerpt`` identifies the span visibly underlined after its marker.

    Q1 receives an explicit allow-list surface because its internal model also
    stores hidden pronunciation data and authoring labels such as ``見出し``.
    """

    if isinstance(section, Q1Section):
        return _q1_blind_surface(section)

    return _strip_author_keys(section.model_dump())

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
        # Q5 source_excerpt is author-side anchor metadata. The visible passage
        # still contains the actual text; the reviewer must read it rather than
        # receiving a pre-linked evidence excerpt.
        "source_excerpt",
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


def blind_section_dict(section) -> dict:
    """Return the candidate information an independent solver may see.

    The result is deliberately stricter than merely deleting answer keys. It
    removes authoring metadata that can reveal where evidence lives or what
    semantic operation was intended.

    Q1 needs one section-specific rule: pinyin is internal metadata for A/B/C
    and must be hidden, while D is itself a pinyin-dialogue task and therefore
    keeps the pinyin that candidates actually read.
    """

    data = _strip_author_keys(section.model_dump())

    if isinstance(section, Q1Section):
        for source_task, blind_task in zip(section.tasks, data["tasks"], strict=True):
            if not isinstance(source_task, Q1PhoneticCountTask):
                continue
            blind_task["headword"].pop("pinyin", None)
            for candidate in blind_task["candidates"]:
                candidate.pop("pinyin", None)

    return data

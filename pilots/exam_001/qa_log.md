# Pilot Exam 001 QA log

## Whole-exam status

- production state: full Q1–Q5 candidate generated; editorial revision pass in progress
- exam family: main_2026
- deterministic whole-exam QA: **recheck pending for active v2 revisions**
- last confirmed deterministic PASS: pre-v2 candidate, GitHub Actions tests run 142
- PDF compile/visual QA: dependency repair in progress (`xeCJK` bundle added after first compile failure)
- blind review: pending
- human content QA: pending
- release state: **not eligible**

## Section log

| Section | Active candidate | Generation | Deterministic QA | Blind review | Human QA | Measured rework minutes | Biggest rework cause so far |
|---|---|---|---|---|---|---:|---|
| Q1 | `q1_v1.json` | complete | PASS | pending | pending | — | |
| Q2 | `q2_v2.json` | complete | recheck pending | pending | pending | — | v1 ordering task had avoidable word-order ambiguity |
| Q3 | `q3_v2.json` | complete | recheck pending | pending | pending | — | v1 had unnatural Chinese collocations in two translation items |
| Q4 | `q4_v2.json` | complete | PASS | pending | pending | — | v1 schema friction: unsupported operation enum `apply` |
| Q5 | `q5_v2.json` | complete | recheck pending | pending | pending | — | v1 mixed Japanese summary syntax with Chinese fill options; lexical item also needed tightening |

Superseded files are intentionally retained as pilot history. The active exam manifest points to Q1 v1, Q2 v2, Q3 v2, Q4 v2 and Q5 v2.

## Confirmed defects and revisions

### Q2 v1 → v2

The second ordering task allowed too much mobility between the time phrase and modal phrase. It was replaced with a more strongly constrained sequence:

`到了车站以后 → 我又看了一遍 → 朋友发给我的地图 → 才找到入口`

This is a content-quality correction, not a schema change.

### Q3 v1 → v2

Two expressions were revised during non-blind editorial reading:

- the museum-reservation item was rewritten to refer naturally to a booked museum visit;
- the `而反而`-like redundancy in a Chinese source sentence was removed.

### Q4 v1 → v2

The first draft used an unsupported operation enum `apply`. The active v2 uses only the frozen Q4 operation vocabulary and preserves the intended reasoning structure.

### Q5 v1 → v2

- the two-slot summary is now a Chinese summary sentence with Chinese fill options rather than Chinese options inserted into Japanese syntax;
- the `临时` lexical item now uses cleaner near-meaning distractors (`暂时 / 短暂 / 一时 / 永远`);
- one Japanese distractor was normalized from mixed Chinese/Japanese wording to `色付きクリップ`.

## Deterministic findings already established before the latest revisions

- answer numbers 1–50 were present exactly once across the full candidate
- section score/range allocation was structurally valid
- Q4 followed the `main_2026` slot grouping and surface-family contract
- Q5 used 37–50 and declared anchors were visibly locatable in the article
- Q3 answer positions were balanced: each of 1–4 appeared twice

The active v2 set must pass the same checks again before these claims are treated as current.

These checks establish structural validity only. They do **not** establish pinyin correctness, language naturalness, answer uniqueness under expert reading, official-level difficulty, or measured student difficulty.

## Defect taxonomy

Record defects using these labels when possible:

- chinese_naturalness
- japanese_instruction_naturalness
- pinyin_correctness
- ambiguity_or_multiple_answers
- weak_distractors
- official_surface_mismatch
- official_reskin_risk
- decorative_material
- weak_cross_material_reasoning
- artificial_scenario_progression
- q5_anchor_or_reference_error
- long_text_coherence
- repeated_cross_section_pattern
- difficulty_rhythm
- pagination_or_layout
- schema_friction

## Whole-exam observations

The first complete candidate exists and has already produced useful rework signals in Q2, Q3, Q4 and Q5. The next valid evidence is the deterministic recheck of the active versions, successful PDF compilation/visual inspection, then a separate blind-review context and human editorial read-through. Do not mark the pilot approved before those stages.

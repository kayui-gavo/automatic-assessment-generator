# Pilot Exam 001 QA log

## Whole-exam status

- production state: full Q1–Q5 candidate generated
- exam family: main_2026
- deterministic whole-exam QA: **PASS** (`validate_exam`, GitHub Actions tests run 142)
- PDF compile/visual QA: pending current CI result
- blind review: pending
- human content QA: pending
- release state: **not eligible**

## Section log

| Section | Active candidate | Generation | Deterministic QA | Blind review | Human QA | Rework minutes | Biggest rework cause |
|---|---|---|---|---|---|---:|---|
| Q1 | `q1_v1.json` | complete | PASS | pending | pending | 0 | |
| Q2 | `q2_v1.json` | complete | PASS | pending | pending | 0 | |
| Q3 | `q3_v1.json` | complete | PASS | pending | pending | 0 | |
| Q4 | `q4_v2.json` | complete | PASS | pending | pending | 0 | schema friction in v1: invalid operation enum `apply` |
| Q5 | `q5_v1.json` | complete | PASS | pending | pending | 0 | |

`q4_v1.json` is intentionally retained as superseded pilot history. It failed the schema contract because it used an unsupported operation enum. The active exam manifest points to `q4_v2.json`.

## Deterministic findings so far

- answer numbers 1–50 are present exactly once across the active exam
- section score/range allocation is structurally valid
- Q4 active candidate follows the main_2026 slot grouping and surface-family contract
- Q5 uses 37–50 and all declared anchors are visibly locatable in the article
- Q3 answer positions are deliberately balanced: each of 1–4 appears twice

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

The first complete candidate now exists. The next valid evidence comes from PDF compilation/visual inspection, then a separate blind-review context and human editorial read-through. Do not mark the pilot approved before those stages.

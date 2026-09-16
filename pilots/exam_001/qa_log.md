# Pilot Exam 001 QA log

## Whole-exam status

- production state: full Q1–Q5 candidate generated; quality-calibration revision pass in progress
- exam family: main_2026
- active set: **Q1 v3 / Q2 v4 / Q3 v5 / Q4 v3 / Q5 v4**
- deterministic whole-exam QA: recheck pending for the active set
- PDF compile/visual QA: real XeLaTeX gate active; Q1 student-surface regression now explicitly checks that A/B/C pinyin is not printed
- blind review: pending for the active fingerprints
- human content QA: pending for the active fingerprints
- release state: **not eligible**

The release standard now treats official-like difficulty and shortcut resistance as hard Human-QA gates. Structural validity alone is not sufficient.

## Section log

| Section | Active candidate | Generation | Deterministic QA | Blind review | Human QA | Biggest rework cause so far |
|---|---|---|---|---|---|---|
| Q1 | `q1_v3.json` | complete | recheck pending | pending | pending | v2 modeled A/B as elementary single-character drills and the student renderer exposed pinyin that should have remained internal metadata |
| Q2 | `q2_v4.json` | complete | recheck pending | pending | pending | earlier ordering tasks pre-packaged too much syntax inside long clause-sized tokens |
| Q3 | `q3_v5.json` | complete | recheck pending | pending | pending | earlier distractors often moved too far from the key and could be eliminated from one lexical difference |
| Q4 | `q4_v3.json` | complete | recheck pending | pending | pending | v2 contained Japanese-surface and nominal cross-source defects; v3 remains the current candidate |
| Q5 | `q5_v4.json` | complete | recheck pending | pending | pending | v3 contained a giveaway lexical item and late questions that repeated the same central thesis too closely |

Superseded files are intentionally retained as pilot history.

## Confirmed defects and revisions

### Q1 v1 → v2 → v3

The original dialogue-timeline defect from v1 was fixed in v2, but official-surface auditing exposed a deeper modeling problem.

A/B in the official 2026 surface compare the pronunciation of an **underlined target character inside a lexical item**. The old schema had no target-character position, which encouraged single-character beginner-drill items. Worse, browser/PDF preview printed A/B/C pinyin even though those sections are meant to test the learner's pronunciation knowledge; this leaked the information being tested.

v3 therefore changes both data and presentation:

- `PinyinWord.target_index` stores the 1-based target character for Q1 A/B.
- multi-character A/B words fail deterministic validation if `target_index` is missing.
- student browser and LaTeX surfaces show Hanzi only for A/B/C; pinyin remains internal validation/rationale metadata.
- A/B now use ordinary multi-character vocabulary rather than all-single-character sets.
- C uses natural two-syllable words and compares the full tone pattern.
- D1/D2 require evidence from multiple utterances rather than a single keyword or final line.

This is treated as a solution-leak and construct-fidelity issue, not a cosmetic layout change.

### Q2 v1 → v2/v3 → v4

Earlier revisions fixed ambiguity and answer-box placement, but a difficulty audit found that the ordering tasks still behaved too much like rearranging four already-complete clauses. That surface resembles Q2 while reducing the actual syntactic work.

v4 replaces both ordering tasks with token pools where the learner must resolve real dependencies:

- `惊讶得 → 好一会儿 → 什么 → 都说不出来`, competing with a locally grammatical alternative path meaning that speech became possible later;
- `得 → 先 → 做完作业 → 才能`, competing with a grammatical but semantically opposite path.

Generation/review rules now reject clause-shuffling shortcuts, and deterministic validation warns when a pool contains too many long clause-sized tokens.

### Q3 v1–v4 → v5

Language-naturalness corrections in earlier revisions were necessary but not enough. A new item-quality pass focused on distractor distance.

v5 is rebuilt around near-miss alternatives. Wrong options preserve most of the proposition and change one decisive dimension such as:

- concession vs simple condition;
- `不一定` vs `一定不`;
- current possibility vs certainty;
- later realization vs knowledge from the beginning;
- reason/scope reversal while keeping the same actors and event.

The new Human-QA gates explicitly require near-miss distractors, no keyword shortcut and semantic-operation diversity.

### Q4 v1 → v2 → v3

The existing v3 remains active. It already fixed the main pilot defects:

- student-facing Japanese prompt language;
- real cross-source dependency rather than a `cross_source` label on a one-graph question;
- normalized wording and student-facing names.

The next Q4 risk is set-level template repetition across future exams, not a major rewrite of this candidate.

### Q5 v1 → v2/v3 → v4

The article itself remained useful, but v3 still had item-writing weaknesses.

v4 makes two targeted changes:

- replaces the giveaway `临时` item whose incorrect choice was simply the opposite word `永远` with a polysemy question on `留`, where all four choices are natural Chinese and the learner must identify the matching sense;
- separates the cognitive function of the final three questions. Q9 integrates the rainy-day information-sharing experience with the tea-order example, Q10 summarizes two procedural improvements from separated paragraphs, and Q11 remains the whole-text consistency task.

This prevents the end of the section from asking the same central thesis three times in different wording.

### Renderer and UI quality

The browser and XeLaTeX paths now share the same Q1 surface semantics. A regression test rejects A/B/C pinyin leakage in the student booklet and checks target-character underlining.

The full-exam Streamlit chrome is also moving away from product-marketing/dashboard styling: no slogan header, no large promotional subtitle, plain text status labels instead of pill walls, and a flat editorial stylesheet that keeps the exam surface visually dominant.

## Current quality gates

Every section now requires common Human QA for:

- Chinese naturalness
- Japanese instruction naturalness
- answer uniqueness
- distractor plausibility
- 2026 surface fidelity
- **official difficulty calibration**
- **shortcut resistance**
- originality
- readable layout
- no solution leak

Section-specific checks add Q1 target underlining/pinyin visibility, Q2 ordering granularity, Q3 near-miss distractors, Q4 real cross-source dependency and Q5 lexical/late-question quality.

These checks are intentionally human. Passing schema/pytest does **not** establish real pronunciation correctness, native naturalness, answer uniqueness under expert reading, official-level difficulty, or student difficulty.

## Defect taxonomy

Record defects using these labels when possible:

- chinese_naturalness
- japanese_instruction_naturalness
- pinyin_correctness
- ambiguity_or_multiple_answers
- weak_distractors
- official_surface_mismatch
- official_difficulty_mismatch
- solution_shortcut
- solution_leak
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

## Next evidence required before approval

1. deterministic PASS for Q1 v3 / Q2 v4 / Q3 v5 / Q4 v3 / Q5 v4;
2. successful student/teacher PDF compile and visual inspection;
3. independent blind review for each active fingerprint, including shortcut audit;
4. native/human content QA with all new difficulty gates checked;
5. final 80-minute whole-exam read.

Do not mark Pilot 001 approved before those stages.

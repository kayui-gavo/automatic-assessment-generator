# Pilot Exam 001 QA log

## Whole-exam status

- production state: full Q1–Q5 candidate generated; editorial revision pass in progress
- exam family: main_2026
- deterministic whole-exam QA: **recheck pending for active v3 revisions**
- last confirmed deterministic PASS: active v2 candidate before the current Q3/Q5 v3 edits
- PDF compile/visual QA: portability repair in progress; `xeCJK` dependency and font fallback regressions were both exposed by real XeLaTeX CI
- blind review: pending
- human content QA: pending
- release state: **not eligible**

## Section log

| Section | Active candidate | Generation | Deterministic QA | Blind review | Human QA | Measured rework minutes | Biggest rework cause so far |
|---|---|---|---|---|---|---:|---|
| Q1 | `q1_v1.json` | complete | PASS | pending | pending | — | |
| Q2 | `q2_v2.json` | complete | PASS before v3 manifest switch | pending | pending | — | v1 ordering task had avoidable word-order ambiguity |
| Q3 | `q3_v3.json` | complete | recheck pending | pending | pending | — | v1/v2 exposed unnatural Chinese collocations and one unnatural Japanese translation option |
| Q4 | `q4_v2.json` | complete | PASS | pending | pending | — | v1 schema friction: unsupported operation enum `apply` |
| Q5 | `q5_v3.json` | complete | recheck pending | pending | pending | — | v1 mixed-language summary syntax; v2 still had unnatural relationship wording and an imprecise colloquial phrase |

Superseded files are intentionally retained as pilot history. The active exam manifest points to Q1 v1, Q2 v2, Q3 v3, Q4 v2 and Q5 v3.

## Confirmed defects and revisions

### Q2 v1 → v2

The second ordering task allowed too much mobility between the time phrase and modal phrase. It was replaced with a more strongly constrained sequence:

`到了车站以后 → 我又看了一遍 → 朋友发给我的地图 → 才找到入口`

This is a content-quality correction, not a schema change.

### Q3 v1 → v2 → v3

The first editorial pass removed two conspicuous collocation problems. A second pass then found that the museum-reservation item was still formally understandable but not native enough: `已经预约好的博物馆参观` was replaced with the more natural `按约去博物馆参观` pattern across all four options. The B2 Japanese key was also normalized from the awkward `迷惑を増やしやすい` to `相手に迷惑をかけやすい`, and the Chinese source sentence was adjusted to make the causal link explicit.

The answer-position distribution remains intentionally balanced: ①②③④ each appear twice.

### Q4 v1 → v2

The first draft used an unsupported operation enum `apply`. The active v2 uses only the frozen Q4 operation vocabulary and preserves the intended reasoning structure.

### Q5 v1 → v2 → v3

The first revision fixed mixed Japanese/Chinese summary syntax and tightened the `临时` lexical item. The second editorial pass found two remaining native-language defects:

- `顾客会不会觉得店里的人离自己越来越陌生` was grammatically interpretable but unnatural as a relationship description. It is now `顾客会不会觉得自己和店里人的关系越来越〔空欄A〕`, with `疏远` as the key and grammatically compatible distractors.
- `到处找消息` was too colloquial and underspecified for the shared-delivery context. It is now `四处打听订单进度`, and the underlined-meaning item was rewritten so its evidence matches the revised text exactly.

### Renderer portability regression

Real XeLaTeX CI exposed two independent problems that schema/render-string tests could not catch:

1. Ubuntu did not have `xeCJK.sty`; the PDF workflow now installs the Chinese TeX language bundle.
2. The v0.5 renderer had regressed to a `TeX Gyre Termes → Times New Roman` fallback, even though an earlier version had already learned that this is not portable. The renderer now prefers `Liberation Serif` before checking Times New Roman and has a final Latin Modern fallback. `compile_xelatex()` now surfaces the last 80 log lines on failure instead of discarding the diagnostic output.

These are production defects, not cosmetic CI issues, because local/Linux rendering must not depend on proprietary fonts being preinstalled.

## Deterministic findings established before the current v3 edits

- answer numbers 1–50 were present exactly once across the full candidate
- section score/range allocation was structurally valid
- Q4 followed the `main_2026` slot grouping and surface-family contract
- Q5 used 37–50 and declared anchors were visibly locatable in the article
- Q3 answer positions were balanced: each of 1–4 appeared twice

The active v3 set must pass the same checks again before these claims are treated as current.

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

The first complete candidate has already produced useful rework signals in Q2, Q3, Q4, Q5 and the renderer itself. The next valid evidence is the deterministic recheck of the active v3 set and successful PDF compilation. After that, the real Pilot 001 booklet must be inspected end-to-end before blind review and human QA. Do not mark the pilot approved before those stages.

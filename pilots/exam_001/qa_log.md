# Pilot Exam 001 QA log

## Whole-exam status

- production state: full Q1–Q5 candidate generated; editorial revision pass in progress
- exam family: main_2026
- deterministic whole-exam QA: **recheck pending for active Q1 v2 / Q2 v2 / Q3 v3 / Q4 v3 / Q5 v3 set**
- last confirmed deterministic PASS: active set before the current Q4 v3 and renderer-newline edits
- PDF compile/visual QA: real XeLaTeX gate active; dependency, font fallback and literal-`\\n` renderer regressions have all been exposed by CI and repaired, latest verification pending
- blind review: pending
- human content QA: pending
- release state: **not eligible**

## Section log

| Section | Active candidate | Generation | Deterministic QA | Blind review | Human QA | Measured rework minutes | Biggest rework cause so far |
|---|---|---|---|---|---|---:|---|
| Q1 | `q1_v2.json` | complete | recheck pending | pending | pending | — | v1 D2 had a dialogue-timeline wording mismatch (`零食有点多` before shopping) |
| Q2 | `q2_v2.json` | complete | recheck pending | pending | pending | — | v1 ordering ambiguity; later visual QA found answer-position boxes were not tied to the requested blanks |
| Q3 | `q3_v3.json` | complete | recheck pending | pending | pending | — | v1/v2 exposed unnatural Chinese collocations and one unnatural Japanese translation option |
| Q4 | `q4_v3.json` | complete | recheck pending | pending | pending | — | v2 still contained Chinese text in `prompt_ja` and one nominal cross-source task whose key could be solved from one graph alone |
| Q5 | `q5_v3.json` | complete | recheck pending | pending | pending | — | v1 mixed-language summary syntax; v2 still had unnatural relationship wording and an imprecise colloquial phrase |

Superseded files are intentionally retained as pilot history. The active exam manifest points to Q1 v2, Q2 v2, Q3 v3, Q4 v3 and Q5 v3.

## Confirmed defects and revisions

### Q1 v1 → v2

The second pinyin-dialogue item originally said `零食有点多，拿着去车站不方便` before the speakers had gone shopping. The intended logic was that they expected to buy many things, so the dialogue now says `要买的东西有点多`, preserving the answer while fixing the event timeline.

### Q2 v1 → v2 + renderer correction

The second ordering task allowed too much mobility between the time phrase and modal phrase. It was replaced with a more strongly constrained sequence:

`到了车站以后 → 我又看了一遍 → 朋友发给我的地图 → 才找到入口`

A later booklet-level read found a separate presentation defect: the JSON correctly stored `answer_positions=[2,4]`, but the renderer placed both answer-number boxes away from the four sentence blanks. The renderer now embeds the relevant answer-number box directly in the requested second and fourth blank positions while leaving the other blanks as ordinary underlines.

### Q3 v1 → v2 → v3

The first editorial pass removed two conspicuous collocation problems. A second pass then found that the museum-reservation item was still formally understandable but not native enough: `已经预约好的博物馆参观` was replaced with the more natural `按约去博物馆参观` pattern across all four options. The B2 Japanese key was also normalized from the awkward `迷惑を増やしやすい` to `相手に迷惑をかけやすい`, and the Chinese source sentence was adjusted to make the causal link explicit.

The answer-position distribution remains intentionally balanced: ①②③④ each appear twice.

### Q4 v1 → v2 → v3

The first draft used an unsupported operation enum `apply`. v2 fixed the schema vocabulary but a full student-facing read exposed three remaining content defects:

- `A2b` and `B3a` stored Chinese questions inside `prompt_ja`, which would have surfaced directly on the student booklet. Both prompts are now concise Japanese exam instructions.
- `A2c` was labeled `cross_source`, but its old key could be selected merely by calculating the increase in A-M5; A-M4 was effectively decorative evidence. v3 rewrites all four options as two-clause claims. The correct option now requires confirming both that `不知道活动内容` is the most common non-participation reason in A-M4 and that all four activities gained registrations after the explanation change in A-M5.
- the student-facing name form is kept consistent as `陈晨`, and teacher-side `搬運能力` wording is normalized to `運搬能力`.

This revision changes the cognitive dependency, not merely the label: A2c should now fail if either graph is ignored.

### Q5 v1 → v2 → v3

The first revision fixed mixed Japanese/Chinese summary syntax and tightened the `临时` lexical item. The second editorial pass found two remaining native-language defects:

- `顾客会不会觉得店里的人离自己越来越陌生` was grammatically interpretable but unnatural as a relationship description. It is now `顾客会不会觉得自己和店里人的关系越来越〔空欄A〕`, with `疏远` as the key and grammatically compatible distractors.
- `到处找消息` was too colloquial and underspecified for the shared-delivery context. It is now `四处打听订单进度`, and the underlined-meaning item was rewritten so its evidence matches the revised text exactly.

### Renderer portability and compile regressions

Real XeLaTeX CI has now exposed three independent problems that schema/render-string tests did not catch:

1. Ubuntu did not have `xeCJK.sty`; the PDF workflow now installs the Chinese TeX language bundle.
2. The v0.5 renderer had regressed to a `TeX Gyre Termes → Times New Roman` fallback, even though an earlier version had already learned that this is not portable. The renderer now prefers `Liberation Serif` before checking Times New Roman and has a final Latin Modern fallback. `compile_xelatex()` now surfaces the last 80 log lines on failure instead of discarding the diagnostic output.
3. The continuous full-exam renderer used raw f-strings ending in `\\n`, which emitted the literal TeX command `\n` after constructs such as `\par`. XeLaTeX therefore failed at the title before any page was produced. Dynamic lines now go through `_tex_line()`, which appends a real newline character; regression tests explicitly reject `\par\n`, `\clearpage\n` and `\smallskip\n` pseudo-command sequences.

These are production defects, not cosmetic CI issues, because local/Linux rendering and the final student booklet must compile reproducibly.

## Deterministic findings established before the latest Q4 v3 / renderer edits

- answer numbers 1–50 were present exactly once across the full candidate
- section score/range allocation was structurally valid
- Q4 followed the `main_2026` slot grouping and surface-family contract
- Q5 used 37–50 and declared anchors were visibly locatable in the article
- Q3 answer positions were balanced: each of 1–4 appeared twice

The current active set must pass the same checks again before these claims are treated as current.

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

The first complete candidate has already produced useful rework signals in every section except no major structural rewrite was needed in Q1, and the renderer itself has now been exercised by real XeLaTeX. The next valid evidence is a deterministic PASS for the active v2/v3 section set plus successful student/teacher PDF compilation of the real Pilot 001 booklet. Only after the compiled booklet is visually inspected end-to-end should blind review and human QA begin. Do not mark the pilot approved before those stages.

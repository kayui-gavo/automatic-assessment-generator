# Pilot 001 content-QA log — 学校リユースステーション

Status: **author-side revision completed; blind review + external human QA still pending**

This log intentionally distinguishes deterministic validation from actual item quality. Passing pytest/validator is not treated as evidence that the item is good enough for students.

## v1 author-side audit

### What worked

- A/B form one continuing activity: investigate barriers → run trial → improve operation.
- The scenario is not a noun-swap of either 2026 Tier-1 paper.
- A contains direct comprehension, compound survey reading, numerical comparison and cross-source planning.
- B contains chronological notices, acceptance rules, case matching and a final reflection/synthesis.
- 16 answer slots and multi-answer formats are naturally motivated rather than inserted only to match counts.

### Defects found before blind review

1. **Decorative visual** — B-M3 was an `annotated_diagram` containing only three labelled boxes (station/category/location). No spatial or relational reasoning depended on the diagram. A table expressed the information more honestly and compactly.
2. **Mixed-language option style** — A2 and A4 unnecessarily wrapped Chinese phrases inside Japanese option sentences. This weakened the Chinese-reading task and looked unlike polished exam copy.
3. **Shared-option instruction ambiguity** — B2/B4 used shared options but the item face did not explicitly state whether options could be reused.
4. **Chinese phrasing polish** — `学校账号` was understandable but `学校官方账号` is more natural in this context; `募集数量有限时` was semantically vague.
5. **B3 was too shallow** — v1 mostly required noticing a temporary closure time. It did not justify three source dependencies strongly enough.

## v2 changes

- B-M3 changed from decorative `annotated_diagram` to a table. This directly caused a generator/reviewer rule change: visual form must be justified by spatial, route, causal, hierarchical or procedural information.
- A2/A4 options rewritten as complete Chinese statements.
- `学校账号` → `学校官方账号`.
- A-M5 wording changed to make the priority-publicity condition explicit.
- B2/B4 prompts now explicitly state that shared options may be reused, matching `option_reuse=allowed`.
- B3 now requires simultaneous use of:
  - daily maximum of three donated items,
  - category-to-station mapping,
  - the temporary 16:00–16:30 registration pause.
  This makes `cross_source` substantive rather than metadata-only.
- Generator and blind-review prompts were updated from this observed defect pattern rather than from abstract preference.

## Current author-side critique of v2

### Strengths

- Information forms follow function rather than a material-type quota.
- A2 is a genuine compound-source task: graph values cannot be interpreted safely without the survey-method note.
- A4 uses demand/supply data and policy text for a decision, not just data extraction.
- B3 has a clear three-condition reasoning chain.
- B4 changes the use of earlier information: the student must connect pre-trial demand, operational notices and post-trial reflection to future improvements.

### Remaining concerns to test in blind review

- **Overall difficulty may still be slightly easy.** A1, A3 and B1 are deliberately accessible, but B2 may also be too direct. Do not increase difficulty merely for appearance; first see whether B3/B4 produce enough upper-range discrimination in teacher judgment.
- **B4 may be over-explicit.** The Japanese labels `文具不足 / 受入可否への質問 / 臨時停止時の無駄足` summarize the problems for the examinee. A later revision may instead require the examinee to infer one or more of these problem categories from the reflection itself.
- **A4 option 5 is strongly cued by A-M5.** The task is still cross-source as a two-answer set, but the distractor quality should be checked independently.
- **Synthetic realism.** The school reuse scheme is plausible but still constructed. Human QA should judge whether the notices, survey and reflection sound like materials students would naturally encounter rather than materials written only to host questions.
- **Japanese instruction register.** Needs a final check against actual 2026 wording conventions before any student use.

## Quality decision

Current status: **REVISE/REVIEW, not APPROVED**.

Do not copy this item to `benchmarks/` or `item_bank/approved/` until:

1. a blind solver answers all tasks without seeing metadata/key;
2. answer-key agreement is checked;
3. a Chinese-language human review is completed;
4. a Common Test item-writing review is completed;
5. student and teacher PDFs are visually inspected.

## System lessons extracted from Pilot 001

- A validator can confirm structure but cannot detect a decorative visual.
- `dependency_mode=cross_source` should be judged semantically, not celebrated merely because three evidence IDs exist.
- Shared-option reuse rules belong on the student-facing item, not only in JSON metadata.
- Real content pilots are already producing more useful prompt improvements than another round of abstract architecture work.

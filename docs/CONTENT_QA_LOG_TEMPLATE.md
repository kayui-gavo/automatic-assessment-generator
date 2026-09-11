# Full Q4 content-QA record

This is the human release gate for a generated full-Q4 candidate. The goal is practical: record what a teacher actually had to fix, and prevent a structurally valid but weak item from entering `approved/`.

The UI now saves the canonical machine-readable record to:

```text
workspace/human_qa/<item_id>.human_qa.json
```

Current blueprint baseline: `R8-2026-main-tsui-v3`.

## Required release checks

Every item marked `approve` must pass all of these:

- Chinese naturalness
- Japanese instruction naturalness
- answer uniqueness
- plausible distractors
- 2026 surface-family fidelity
- coherent information journey
- every visual/material has a real information function
- originality / no semantic reskin concern
- source integrity
- booklet/layout readability
- no solution leakage from prompt, figure or wording

If any required check fails, disposition must remain `revise` or `reject`.

## Defect tags

Use any that actually caused rework:

- Chinese naturalness
- Japanese instruction naturalness
- answer ambiguity / multiple answers
- weak distractors
- distractor too obviously false
- correct answer too obvious from wording
- material not actually needed
- fake integration
- scenario progression feels artificial
- excessive complexity / too many conditions
- too easy / too shallow
- source-integrity problem
- official-item surface reskin risk
- pre-2026 architecture drift
- renderer / page break / figure problem
- schema friction
- option-language mismatch
- A/B intro leaks or over-explains

## Rework time

Record minutes separately for:

- first human read
- Chinese-language edits
- item-writing / answer edits
- layout edits

The production system sums these as the candidate's total human correction time. This is one of the most useful metrics for deciding what the tool should improve next.

## Revision size

Also record:

- tasks materially rewritten
- materials materially rewritten
- whether answer key changed
- whether blind reviewer disagreed
- whether a high-severity ambiguity was found after blind review
- whether manual TeX repair was required

## Final notes

Keep two short notes:

1. What caused the most rework?
2. What should the tool change before the next candidate?

These records should be reviewed across several pilots before adding new architecture. Frequent human rework is stronger evidence than speculative feature requests.

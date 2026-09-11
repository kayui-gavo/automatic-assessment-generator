# Pilot 001 content-QA log — 学校リユースステーション

Status: **REJECTED as a 2026 Q4 likeness benchmark**

## Final decision after human review

Pilot 001 is **not suitable as a model of the 2026 Common Test Chinese Q4**.

The earlier engineering review focused too much on generic qualities such as:

- one continuing scenario,
- multiple information sources,
- cross-source reasoning,
- non-decorative visuals,
- answer uniqueness.

Those are useful, but they are not enough. The item still did not resemble the actual 2026 Q4 closely enough at the student-facing level.

The decisive defect was **loss of the 2026 surface grammar**.

2026 main and makeup both show a much stronger observable scaffold:

- A 21–22: Chinese dialogue + choose two
- A 23–26: research/data/document block with four answer slots
- A 27–28: lecture summary / structured memo + choose two
- B 29–36: one of two recognizable 2026 families

Pilot 001 instead treated Q4 as a generic sequence of materials and tasks. It therefore passed an overly abstract validator while still feeling unlike the official exam.

## Why the previous audit was insufficient

The previous v1→v2 revisions were still useful locally:

1. decorative visual → table;
2. mixed Japanese/Chinese option style → cleaner Chinese;
3. shared-option reuse rule made explicit;
4. Chinese phrasing polished;
5. some cross-source reasoning strengthened.

However, these were second-order defects. The first-order problem was the architecture itself.

## New system lesson

For this project, originality means:

- new topic,
- new passages,
- new numbers,
- new cases,
- new distractors,
- new answer logic,

**while preserving the current 2026 item grammar closely enough that a teacher immediately recognizes it as the same exam family.**

Avoiding a noun-swap reskin must not become an excuse to abandon the official task scaffold.

## Consequence

Pilot 001 remains in `pilots/` only as a **failed calibration example**. It must not be moved to `benchmarks/` or `item_bank/approved/`.

From blueprint v3 onward, full Q4 generation must declare one of:

- `main_2026`
- `makeup_2026`

and deterministic validation checks the answer-slot grouping against that family.

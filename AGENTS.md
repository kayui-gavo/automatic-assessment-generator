# AGENTS.md

This repository is an internal authoring tool for TABITO Education.

## Product goal

Reduce the time required to create high-quality original Common Test Chinese mock items while preserving human editorial control.

The product is judged by three practical outcomes:

1. shorter authoring/revision time,
2. closer fidelity to the current Common Test item-writing direction,
3. lower human rework rate without sacrificing answer uniqueness or language quality.

## Current scope

- Current production focus: 共通テスト中国語 第4問 (Q4).
- Manual ChatGPT Plus workflow. Do not add a paid LLM API dependency unless explicitly requested.
- JSON is the source of truth for an item.
- Human approval is required before an item enters `item_bank/approved/`.
- `examples/` contains schema/regression fixtures unless explicitly marked otherwise; it is not a gold-quality item bank.

## Reference hierarchy

### Tier 0 — normative boundary

Use the University Entrance Examination Center's 2026 problem-making policy to define the construct boundary: communication purpose/situation, accurate understanding of information and intent, organization/judgment of understood information, and supporting language knowledge/skills.

Tier 0 does **not** define the surface item architecture.

### Tier 1 — item-writing blueprint

The co-equal primary item-writing references are:

- R8 / 2026 main examination, Chinese
- R8 / 2026 makeup/re-examination, Chinese

Shared features define the required 2026 core. Differences between the two define legitimate design variation. Never turn either official paper into a surface template.

### Tier 2 — historical reference only

2025 and earlier examinations may inform language level, stable constructs, distractor plausibility and Japanese instruction conventions. They must not override the 2026 pair or restore an older default architecture.

## Engineering constraints

- Prefer small, explicit Python modules over frameworks.
- Do not introduce LangChain, vector DBs, RAG, fine-tuning, IRT, or a web UI without a demonstrated workflow need.
- Generated/transient files under `workspace/` and `output/` should not be committed except `.gitkeep`.
- Keep validation deterministic where possible.
- The renderer must not alter item content.
- Separate hard constraints backed by the 2026 pair from soft heuristics used only to catch likely quality problems.
- Do not encode an arbitrary numeric quota as a hard rule unless it is supported by both 2026 primary references or is required for schema integrity.

## Assessment constraints

- Reproduce constructs and information-processing patterns, never copy official wording, data, characters, topics, or distinctive scenario sequences.
- A full Q4 uses answer numbers 21–36 exactly once and has A/B progression.
- A/B must represent a meaningful change in information use; B may be practical application, recontextualization, or reflective synthesis. Do not force every B section into a service-planning template.
- Heterogeneous materials should be introduced because the scenario requires them, not to satisfy a type-count quota.
- At least one genuinely integrative task should appear in each subsection of a full Q4. Integration may occur across separate sources or within a deliberately compound source bundle.
- Direct extraction is allowed and appears in the official papers, but it must not dominate the whole section.
- Multi-answer selection is prominent in both 2026 primary references, but do not add it mechanically when the construct does not justify it.
- Distractors must represent plausible reading/interpretation errors rather than arbitrary falsehoods.
- Do not invent statistics and attribute them to real institutions. Synthetic data should be clearly synthetic in the internal source metadata or scenario design.
- Never treat LLM-estimated difficulty as measured student difficulty.

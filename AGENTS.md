# AGENTS.md

This repository is an internal authoring tool for TABITO Education.

## Product goal

Reduce the time required to create high-quality original Common Test Chinese mock items while preserving human editorial control.

## Current scope

- v0.1 targets only 共通テスト中国語 第4問.
- Manual ChatGPT Plus workflow. Do not add a paid LLM API dependency unless explicitly requested.
- JSON is the source of truth for an item.
- Human approval is required before an item enters `item_bank/approved/`.

## Engineering constraints

- Prefer small, explicit Python modules over frameworks.
- Do not introduce LangChain, vector DBs, RAG, fine-tuning, IRT, or a web UI without a demonstrated workflow need.
- Generated/transient files under `workspace/` and `output/` should not be committed except `.gitkeep`.
- Keep validation deterministic where possible.
- The renderer must not alter item content.

## Assessment constraints

- Reproduce constructs and information-processing patterns, never copy official wording or scenarios.
- Q4 must require cross-material reasoning in at least one question.
- Distractors must represent plausible reading errors rather than arbitrary falsehoods.
- Never treat LLM-estimated difficulty as measured student difficulty.

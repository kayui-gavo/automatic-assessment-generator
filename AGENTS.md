# AGENTS.md

This repository is an internal authoring tool for TABITO Education.

## Product goal

Produce complete, original **大学入学共通テスト 中国語 模擬試験** while preserving human editorial control.

The primary production object is now an **Exam**, not a Q4 item:

```text
Exam
├── Q1  発音・ピンイン             24点   1–6
├── Q2  語句                       16点   7–12
├── Q3  表現力                     40点  13–20
├── Q4  複合的な資料の読み取り     60点  21–36
└── Q5  長文読解                   60点  37–50

TOTAL 200点 / 80分 / 50解答欄
```

The product is judged by practical outcomes:

1. shorter full-exam authoring and revision time,
2. closer fidelity to the current 2026 Common Test item-writing direction,
3. lower human rework without sacrificing answer uniqueness, language quality, originality, or booklet readability,
4. a traceable reason why every released section/exam was approved.

## Current scope

- Current production focus: **full Q1–Q5 Common Test Chinese mock exams**.
- Q4 is the most structurally complex section, but it is only Section 4 of the Exam.
- Manual ChatGPT Plus workflow. Do not add a paid LLM API dependency unless explicitly requested.
- JSON + filesystem are the source of truth. Do not add a database without demonstrated need.
- Q1–Q5 are generated/reviewed separately; never ask one LLM call to generate the whole 200-point exam.
- Human approval is required at both section level and final full-exam level before release.
- `examples/` contains schema/regression fixtures unless explicitly marked otherwise; it is not a gold-quality item bank.
- `pilots/` contains content-QA candidates and may intentionally contain rejected/superseded work.
- `benchmarks/` is reserved for future human-approved gold exemplars only.

## Reference hierarchy

### Tier 0 — normative boundary

Use the University Entrance Examination Center's 2026 problem-making policy to define construct boundaries. Tier 0 does **not** define surface item architecture.

### Tier 1 — current item-writing blueprint

The co-equal primary surface references are:

- R8 / 2026 main examination, Chinese
- R8 / 2026 makeup/re-examination, Chinese

Shared features define stable 2026 structure. Differences define legitimate family variation.

Q1–Q3 are structurally stable across the pair. Q4 and Q5 preserve explicit `main_2026` / `makeup_2026` families.

Do not copy official wording, article text, characters, data, topics, distinctive scenario sequences, or copyrighted passages. Reproduce question architecture and constructs with original content.

### Tier 2 — historical reference only

2025 and earlier examinations may inform language level, long-term constructs, distractor plausibility and Japanese instruction conventions. They must not override the 2026 pair or restore an older default architecture.

## Architecture constraints

- `ExamManifest` is the top-level production object.
- Keep Q4's existing rich `Item` / Material / Task / A-B model intact for backward compatibility.
- Q1, Q2, Q3 and Q5 have native section models; do not flatten them into Q4's generic task model merely for aesthetic uniformity.
- Q2 ordering must remain structurally explicit: token pool, correct sequence, answer positions.
- Q5 article references must use stable anchors, never ad-hoc substring lookup at review/render time.
- Section fingerprints bind section Blind Review and Human QA.
- Exam fingerprint is derived from exam metadata plus current Q1–Q5 fingerprints.
- Editing one section invalidates that section's evidence and final Exam QA, but must not invalidate unrelated section review/QA.
- Approved content is immutable under the same ID. Create a new version/ID for substantive edits.

## Production workflow

Normal full-exam workflow:

```text
create Exam
  ↓
Q1..Q5 generation requests (separate)
  ↓
per-section deterministic validation
  ↓
per-section blind solve/review
  ↓
per-section Human QA
  ↓
full-exam deterministic validation
  ↓
Final Exam Human QA
  ↓
release transaction
```

Do not add release bypass flags. A UI path and CLI path must enforce the same release invariants.

Human QA must record actual rework when possible (first read, language edit, item edit, layout edit, largest rework cause). Future system changes should be driven by repeated real rework causes, not speculative architecture.

## Engineering constraints

- Prefer small, explicit Python modules over frameworks.
- Keep Python / Pydantic / YAML / JSON / Streamlit / XeLaTeX as the default stack.
- Do not introduce LangChain, multi-agent frameworks, vector DBs, RAG, fine-tuning, IRT, SQL, authentication, cloud deployment, React/Next.js, or automated difficulty prediction without demonstrated workflow need.
- Generated/transient files under `workspace/`, `output/`, and live `exam_bank/` production folders should not be committed except `.gitkeep`.
- Keep validation deterministic where the program can actually know the answer; do not pretend code can verify Chinese pronunciation/naturalness that requires human judgment.
- The renderer must not alter assessment content.
- Separate hard constraints backed by official 2026 structure/schema integrity from soft warnings/heuristics.
- Do not encode arbitrary numeric quotas as hard rules merely to make generated papers look complex.

## Whole-exam invariants

A complete 2026-style Exam must contain exactly:

- Q1 answers 1–6, score 24
- Q2 answers 7–12, score 16
- Q3 answers 13–20, score 40
- Q4 answers 21–36, score 60
- Q5 answers 37–50, score 60
- total 200, duration 80 minutes, answers 1–50 exactly once

Exam-level QA should catch or flag:

- missing/duplicated answer numbers,
- family mismatch,
- stale section fingerprints,
- Q4/Q5 topic overlap,
- cross-section solution leakage,
- excessive repetition of names/topics/expressions,
- implausible difficulty rhythm,
- pinyin/simplified-Chinese/Japanese-instruction style inconsistency,
- pagination, chart, long-text and booklet readability problems.

## Section-specific constraints

### Q1

Deterministic code may verify structure and visible Unicode tone marks, but not full phonological correctness. Human QA must verify pinyin, initials/finals, tone patterns, 一/不 tone sandhi, polyphones, dialogue naturalness and layout.

### Q2

`selection_rule=appropriate/inappropriate` must be explicit. Ordering questions must preserve token identity and answer-position order. Token IDs are not ordinary multiple-choice positions and must not be included in whole-exam answer-position balance statistics.

### Q3

13–16 are Japanese → tone-marked pinyin Chinese choices; 17–20 are tone-marked pinyin Chinese → Japanese choices. Distractors should record concrete semantic error types rather than generic "wrong meaning" labels where possible.

### Q4

Retain the existing `main_2026` / `makeup_2026` surface grammar, rich materials, A/B progression, compound sources, response modes and information-dependency model. Do not simplify Q4 just to fit a shared section schema.

### Q5

The article must be 100% original. Official/public copyrighted article text must never be reconstructed or copied. Stable anchors must correspond to something a student can actually locate in the visible article. Q5 must include both language-form reading and whole-text reasoning; family-specific answer-slot/question-number structure must remain explicit.

## Review semantics

Blind reviewers must not see author answers, rationales, distractor labels, family self-labels, difficulty self-ratings, dependency metadata, originality notes or other author-side conclusions.

Only true `multi_select` answers are unordered sets. Q2 ordering and other multi-slot responses are ordered by answer slot; reversing the answers is wrong.

## Rendering

The target output is one continuous student booklet and one teacher edition, not five unrelated PDFs.

```text
output/<exam_id>/
├── student.tex / student.pdf
├── teacher.tex / teacher.pdf
└── answer_key.json
```

Internal IDs/fingerprints/dependency metadata must never appear in the student booklet.

## Backward compatibility

Existing Q4 pilots/item bank/tests must continue to load, validate, preview and render. Do not delete working Q4 infrastructure merely to make the new architecture cleaner. The old Q4-only workflow is a supported standalone/legacy path, not the product center.

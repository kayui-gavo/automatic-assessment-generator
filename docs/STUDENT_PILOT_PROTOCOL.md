# Student pilot protocol

This protocol is the minimum evidence collection needed before treating a generated full exam as empirically calibrated.

It is intentionally simple. Pilot 001 does not need IRT, a student account system, per-keystroke telemetry, or a dashboard.

## 1. Freeze the tested version

Before any student attempt, record the exact `exam_id` and `exam_fingerprint` from the released exam evidence.

Never merge responses from different fingerprints into one item analysis. If any section is revised, the revised exam is a new empirical version even when the public title is unchanged.

## 2. Participant privacy

Use an anonymous `participant_id` such as `P001`, `P002`, ... .

Do not put student names, email addresses, phone numbers, school IDs, or other identifying information in the repository.

## 3. Test conditions

Default condition for a full-exam trial:

- 80 minutes
- student booklet only
- no answer key or teacher view
- same calculator/dictionary/reference rules intended for the real course use case
- record section transition times when practical
- do not coach individual items during the attempt

If the condition differs, record it in the trial notes rather than silently mixing the data.

## 4. Files

Use two tables.

### `student_trial_answers.csv`

One row per participant × answer number. Every participant must have all 50 answer rows. An item the student did not reach is still recorded as an explicit omission rather than being deleted from the table.

Required columns:

- `participant_id`
- `exam_id`
- `exam_fingerprint`
- `answer_number` — 1 through 50
- `section` — Q1 through Q5
- `selected_option` — blank when omitted
- `omitted` — `1` or `0`
- `ambiguity_flag` — `1` only when the student reports that the item itself was ambiguous
- `note` — short free text only when needed

Do **not** type the correct option, an `is_correct` flag, or points into the student CSV. Correctness and the 200-point score are derived from the released, hash-bound answer/scoring artifacts. This avoids turning answer-key or point-weight transcription into a new source of empirical-data error.

Preserve the actual selected option so distractor frequencies can be calculated later.

### `student_trial_sections.csv`

One row per participant × section, plus one optional `TOTAL` row. Q1 through Q5 must all be present for every participant.

Required columns:

- `participant_id`
- `exam_id`
- `exam_fingerprint`
- `section` — Q1, Q2, Q3, Q4, Q5, or TOTAL
- `elapsed_seconds`
- `completed` — `1` or `0`
- `perceived_difficulty_1_5` — optional; 1 easiest, 5 hardest
- `note`

For paper trials, section time may be recorded from section-transition timestamps. Do not fabricate item-level timing when it was not measured.

## 5. Bind the trial to released evidence

Run student trials only against a frozen released exam version. Use that approved exam's:

```text
exam_bank/approved/<exam_id>/release.json
```

The analyzer verifies the complete release chain before scoring any response:

```text
release.json
  → release gates all passed
  → artifact_manifest.json SHA-256
  → student / teacher / answer-sheet PDF SHA-256
  → answer_key.json SHA-256
  → scoring_scheme.json SHA-256
  → answer numbers 1–50
  → scoring family matches approved exam family
```

The `exam_id` and `exam_fingerprint` in the release evidence must exactly match both student CSV files. If the wrong release record is supplied, a released artifact was modified, the scoring file belongs to another family, or the CSV fingerprint belongs to another candidate version, analysis stops with an error.

## 6. 200-point scoring contract

`scoring_scheme.json` is generated automatically during PDF/artifact preflight from the frozen 2026 family-specific scoring contract. It is not teacher-entered metadata.

The scoring contract reproduces the official 2026 answer-table semantics rather than assigning a naive weight to every answer box:

- ordinary single answer: independent points
- `＊` linked answers: all linked answers must be correct to receive the group's points
- hyphen-linked correct answers: order does not matter
- `各N`: each correct selection in that unordered group earns N points
- starred pairs without a hyphen remain order-sensitive

`main_2026` and `makeup_2026` have different Q4/Q5 grouping, so they use separate scoring schemes. Both sum to:

```text
Q1  24
Q2  16
Q3  40
Q4  60
Q5  60
TOTAL 200
```

The released `scoring_scheme.json` is itself hash-bound. Historical pilot analysis uses that released scheme directly; it does not silently substitute whatever scoring code happens to be current later.

## 7. Run the analyzer

Copy the templates in `pilots/exam_001/`, remove `_template` from the filenames, and enter the trial data. Then run:

```bash
python -m tabito_itemgen.pilot_analysis pilots/exam_001/student_trial_answers.csv pilots/exam_001/student_trial_sections.csv --release-record exam_bank/approved/<EXAM_ID>/release.json --out-dir pilots/exam_001/analysis
```

The analyzer rejects mixed fingerprints, incomplete 1–50 answer records, wrong answer-number/section mappings, malformed omission records, missing Q1–Q5 timing rows, mismatched participant sets, failed release evidence, artifact identity mismatches, PDF hash mismatches, answer-key hash mismatches, scoring-scheme hash mismatches, and scoring-family mismatches.

It writes:

- `item_summary.csv` — bound correct option, correct rate, omission rate, ambiguity reports, and option-selection counts for each answer number
- `participant_summary.csv` — correct-answer count, **official-rule score / 200**, omissions, and ambiguity reports per participant
- `section_summary.csv` — median elapsed time, completion rate, and median perceived difficulty
- `pilot_summary.json` — tested exam identity/family/scoring version, participant count, correct-answer-count range/median, and 200-point score range/median

Keep both `correct / 50` and `score / 200`. They answer different questions: raw answer-slot accuracy is useful for item diagnostics, while the 200-point score follows the official grouped scoring rules.

## 8. Minimum analysis after the trial

For each answer number inspect:

- number attempted
- omission rate
- correct rate
- count/share for every selected option

After enough participants are available, split participants by whole-exam score and inspect upper/lower-group item performance. Do not fit IRT for Pilot 001.

For each section inspect:

- median elapsed time
- completion rate
- median perceived difficulty when collected

For the whole exam inspect:

- `score / 200` distribution
- `correct / 50` distribution
- whether 80 minutes was feasible
- items with unusually high omission
- distractors almost nobody selected
- distractors selected heavily by stronger students
- items with repeated ambiguity reports

## 9. What triggers revision

Student data is a diagnostic signal, not an automatic rewrite rule. Prioritize review when an item shows one or more of:

- repeated ambiguity reports
- answer-key concern
- a supposedly competitive distractor is effectively never selected
- a distractor attracts many stronger students for a defensible reading
- extreme omission not explained by reaching the end of the 80-minute test
- section timing strongly inconsistent with the intended whole-exam rhythm

Any substantive revision creates a new candidate fingerprint and requires the normal independent-review and teacher-QA chain again.

## 10. Pilot 001 output

Pilot 001 should end with a short evidence summary containing:

- participant count
- tested exam fingerprint
- scoring family/version
- 200-point score distribution
- correct-answer-count distribution
- section timing summary
- item correct/omission rates
- distractor frequencies
- ambiguity reports
- teacher rework observations
- concrete changes, if any, proposed for Pilot 002

The purpose is to discover recurring production defects. It is not to make a claim that one small pilot has established population-level difficulty parameters.

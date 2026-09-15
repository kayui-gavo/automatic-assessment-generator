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

Do **not** type the correct option or an `is_correct` flag into the student CSV. The analyzer derives correctness from the released, hash-bound answer artifact. This avoids turning answer-key transcription into a new source of empirical-data error.

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

## 5. Bind the trial to released answer evidence

Run student trials only against a frozen released exam version. Use that approved exam's:

```text
exam_bank/approved/<exam_id>/artifacts/artifact_manifest.json
```

The analyzer reads `exam_id` and `exam_fingerprint` from this manifest, verifies that they match the CSV data, then verifies the SHA-256 of the adjacent `answer_key.json` before scoring any response.

If the wrong artifact manifest is supplied, the answer key was changed, or the CSV fingerprint belongs to another candidate version, analysis stops with an error.

## 6. Run the analyzer

Copy the templates in `pilots/exam_001/`, remove `_template` from the filenames, and enter the trial data. Then run:

```bash
python -m tabito_itemgen.pilot_analysis pilots/exam_001/student_trial_answers.csv pilots/exam_001/student_trial_sections.csv --artifact-manifest exam_bank/approved/<EXAM_ID>/artifacts/artifact_manifest.json --out-dir pilots/exam_001/analysis
```

The analyzer rejects mixed fingerprints, incomplete 1–50 answer records, wrong answer-number/section mappings, malformed omission records, missing Q1–Q5 timing rows, mismatched participant sets, artifact identity mismatches, and answer-key hash mismatches.

It writes:

- `item_summary.csv` — bound correct option, correct rate, omission rate, ambiguity reports, and option-selection counts for each answer number
- `participant_summary.csv` — correct-answer count, omissions, and ambiguity reports per participant
- `section_summary.csv` — median elapsed time, completion rate, and median perceived difficulty
- `pilot_summary.json` — tested exam identity, participant count, and correct-answer-count range/median

### Scoring note

The current exam schema stores the correct option for each of the 50 answer slots but does not yet store a point value for each slot. Therefore the analyzer reports **correct-answer count out of 50**, not an invented 200-point score.

Do not label this count as the official exam score. A true 200-point student score should only be calculated after answer-slot scoring weights become part of the canonical exam schema / answer artifact. The artifact layer already permits a future `scoring_scheme.json`, but no production scoring scheme is generated yet.

## 7. Minimum analysis after the trial

For each answer number inspect:

- number attempted
- omission rate
- correct rate
- count/share for every selected option

After enough participants are available, split participants by whole-exam correct-answer count and inspect upper/lower-group item performance. Do not fit IRT for Pilot 001.

For each section inspect:

- median elapsed time
- completion rate
- median perceived difficulty when collected

For the whole exam inspect:

- correct-answer-count distribution
- whether 80 minutes was feasible
- items with unusually high omission
- distractors almost nobody selected
- distractors selected heavily by stronger students
- items with repeated ambiguity reports

## 8. What triggers revision

Student data is a diagnostic signal, not an automatic rewrite rule. Prioritize review when an item shows one or more of:

- repeated ambiguity reports
- answer-key concern
- a supposedly competitive distractor is effectively never selected
- a distractor attracts many stronger students for a defensible reading
- extreme omission not explained by reaching the end of the 80-minute test
- section timing strongly inconsistent with the intended whole-exam rhythm

Any substantive revision creates a new candidate fingerprint and requires the normal independent-review and teacher-QA chain again.

## 9. Pilot 001 output

Pilot 001 should end with a short evidence summary containing:

- participant count
- tested exam fingerprint
- section timing summary
- item correct/omission rates
- distractor frequencies
- ambiguity reports
- teacher rework observations
- concrete changes, if any, proposed for Pilot 002

The purpose is to discover recurring production defects. It is not to make a claim that one small pilot has established population-level difficulty parameters.

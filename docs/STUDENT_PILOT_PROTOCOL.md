# Student pilot protocol

This protocol is the minimum evidence collection needed before treating a generated full exam as empirically calibrated.

It is intentionally simple. Pilot 001 does not need IRT, a student account system, per-keystroke telemetry, or a dashboard.

## 1. Freeze the tested version

Before any student attempt, record the exact `exam_id` and `exam_fingerprint` from the release/readiness output.

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

One row per participant × answer number.

Required columns:

- `participant_id`
- `exam_id`
- `exam_fingerprint`
- `answer_number` — 1 through 50
- `section` — Q1 through Q5
- `selected_option` — blank when omitted
- `correct_option`
- `is_correct` — `1` or `0`
- `omitted` — `1` or `0`
- `ambiguity_flag` — `1` only when the student reports that the item itself was ambiguous
- `note` — short free text only when needed

Do not convert a wrong answer into a category by hand. Preserve the actual selected option so distractor frequencies can be calculated later.

### `student_trial_sections.csv`

One row per participant × section, plus one optional `TOTAL` row.

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

## 5. Minimum analysis after the trial

For each answer number calculate:

- number attempted
- omission rate
- correct rate
- count/share for every selected option

After enough participants are available, split participants by whole-exam score and inspect upper/lower-group item performance. Do not fit IRT for Pilot 001.

For each section calculate:

- median elapsed time
- completion rate
- median perceived difficulty when collected

For the whole exam inspect:

- total score distribution
- whether 80 minutes was feasible
- items with unusually high omission
- distractors almost nobody selected
- distractors selected heavily by high-scoring students
- items with repeated ambiguity reports

## 6. What triggers revision

Student data is a diagnostic signal, not an automatic rewrite rule. Prioritize review when an item shows one or more of:

- repeated ambiguity reports
- answer-key concern
- a supposedly competitive distractor is effectively never selected
- a distractor attracts many high-scoring students for a defensible reading
- extreme omission not explained by reaching the end of the 80-minute test
- section timing strongly inconsistent with the intended whole-exam rhythm

Any substantive revision creates a new candidate fingerprint and requires the normal independent-review and teacher-QA chain again.

## 7. Pilot 001 output

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

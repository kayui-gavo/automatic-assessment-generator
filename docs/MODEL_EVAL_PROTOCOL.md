# Model Evaluation Protocol

This project does not choose a production model because it is newest, most expensive, or self-reports the highest confidence. Model choice is an empirical part of item-production QA.

## Current baseline

```text
Author / revision: GPT-5.6 Sol · High
Blind Review:      GPT-5.6 Sol · High or stronger allowed pair
Human QA:          required
```

The baseline is intentionally conservative for Pilot-stage work. A cheaper or stronger configuration may replace it only after a controlled comparison.

## What is being evaluated

The target is not generic language-model quality. The target is the amount of trustworthy Common Test Chinese production obtained per unit of human editorial work.

Evaluate model configurations on the exact tasks that matter here:

- Q1 phonetic accuracy, lexical load, confusability and dialogue integration
- Q2 lexical naturalness, inappropriate-item uniqueness and syntax-level ordering
- Q3 semantic fidelity and near-miss distractor quality
- Q4 information journey, genuine cross-source dependence and shortcut resistance
- Q5 article naturalness, local distractor competition and whole-text reasoning

## Frozen comparison design

For one comparison round:

1. Freeze the repository revision, section blueprint, request text and requested topic.
2. Generate the same section request independently with each candidate model/configuration.
3. Never let one candidate see another candidate's output.
4. Run deterministic validation on every output.
5. Run Blind Review in a **memory-isolated context**: non-personalized Temporary Chat for manual ChatGPT operation, or a stateless isolated API request. An ordinary new chat is not sufficient evidence of isolation when cross-chat memory may apply.
6. Give the reviewer only the student-visible candidate surface. Do not expose answer keys, rationales, evidence locators, intended cognitive-operation labels, or internal Q1 A/B/C pinyin.
7. Have the Human QA reviewer evaluate candidates without being told which model produced which candidate whenever practical.
8. Record rework time and defect categories before revising anything.
9. Do not promote a model based on one unusually good item. Repeat across multiple sections and at least several independent exam projects.

Do not use the generating model's self-rating as an evaluation metric.

## Candidate configurations

The current useful comparison set is small:

```text
GPT-5.6 Sol · Medium      efficiency challenger
GPT-5.6 Sol · High        production baseline
GPT-5.6 Sol · Extra High  optional quality challenger when available
Pro model                 optional ceiling check when available
```

A cost-optimized model such as Terra may be tested as a challenger, but it must pass the same blinded editorial criteria. It is not automatically suitable just because the surface text is fluent.

## Metrics

Collect per section and per full exam:

### Hard failure

- schema / deterministic-validation failure
- wrong answer key or multiple valid answers
- high-severity Blind Review issue
- factual/material inconsistency
- pinyin or language error that changes the tested construct
- fake cross-source task that can be solved after removing a claimed required source
- solution leakage

Any recurring hard failure blocks promotion regardless of speed or cost.

### Editorial quality

- Human QA disposition: approve / revise / reject
- number of language edits
- number of item-design edits
- number of distractor rewrites
- number of layout edits
- biggest rework cause
- first-read minutes
- language-edit minutes
- item-edit minutes
- layout-edit minutes

### Student evidence

Once timed pilots exist, add:

- item correct rate
- response-time distribution
- distractor selection frequency
- upper-group vs lower-group correct-rate difference
- omitted / unfinished rate by section
- qualitative reports of ambiguity or unnatural wording

The model that produces the prettiest prose is not necessarily the better assessment author. Difficulty and discrimination must eventually be grounded in student responses.

## Decision rule

Keep GPT-5.6 Sol High as the baseline until a challenger has enough repeated evidence.

A challenger can replace the baseline only if:

- it does not introduce a new recurring hard-failure class;
- Human QA rework is no worse in the dimensions that affect validity;
- final accepted items retain 2026 surface fidelity and shortcut resistance;
- any claimed efficiency gain is material in the real workflow, not only in raw generation latency.

A more expensive model should not be promoted merely because it is stronger in general benchmarks. A cheaper model should not be promoted merely because most drafts look fluent.

## Reviewer diversity

Memory-isolated context is mandatory. Model diversity is useful but secondary.

Using a different strong reviewer model for Q4/Q5 can be an additional audit when available, especially for high-stakes releases, but it is not a substitute for Human QA. Requiring a second paid model for every section before there is evidence of measurable benefit would add process cost without proving better items.

## API migration trigger

Move generation/review from manual ChatGPT operation to the Responses API when at least one of these becomes the bottleneck:

- model/version provenance cannot be managed reliably by operators;
- copy/paste volume dominates production time;
- repeated model comparisons need automated batch execution;
- enough gold Human-QA outcomes exist to run regression evals automatically.

When that happens, preserve the current gates. API automation should replace manual transport, not remove Blind Review, Human QA, fingerprint binding or PDF preflight.

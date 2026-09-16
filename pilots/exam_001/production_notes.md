# Pilot Exam 001 production notes

## Generation rule

Generate and audit one section at a time. Do not ask one model response to produce all five sections at once.

Recommended order:

1. Q1 — fastest surface sanity check
2. Q2 — ordering uniqueness check
3. Q3 — translation/pinyin quality check
4. Q5 — long-text coherence and anchor stress test
5. Q4 — most complex multi-source section, generated after the rest of the booklet so its scenario does not accidentally duplicate another section

## Cross-section anti-repetition check

Before final exam QA, explicitly search for repeated patterns such as:

- every section using school clubs or event planning,
- repeated names/roles across unrelated sections,
- the same Japanese instruction phrase appearing unnaturally often,
- correct answers clustering in the same option position,
- repeated distractor strategy,
- Q4 and Q5 both following compare → choose → later-use narrative logic.

## What not to optimize during Pilot 001

- measured difficulty models,
- automatic topic recommendation,
- RAG over past papers,
- automatic human-QA completion,
- one-click LLM API orchestration,
- item-bank analytics dashboards.

Pilot 001 exists to expose content-production friction first.

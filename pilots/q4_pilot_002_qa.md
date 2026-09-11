# Pilot 002 QA — 市立図書館の学習スペース

Status: **ACTIVE CANDIDATE — main_2026 family**

Pilot 002 was created after Pilot 001 was rejected for being only a generic multi-source reading set. Its purpose is to test whether the system can reproduce the actual 2026 main-exam Q4 surface grammar while keeping the topic and item content original.

## Structural target

- A 21–22: Chinese dialogue + choose two
- A 23–24: paired/shared-option data task
- A 25: chart reading
- A 26: related visual/data comparison
- A 27–28: longer explanation / memo + choose two
- B 29–30: checklist / conditions + choose two
- B 31–32: person/profile × option matching
- B 33: identify missing information needed for the match
- B 34: infer a rule from a process/flow
- B 35–36: apply the same process to two concrete cases

## Revision already made after human feedback

The first Pilot 002 draft still looked too much like our own generic generator because option-language distribution was flattened. It has now been revised so that:

- A1, A3 and B1 use Japanese options, closer to the 2026 main-paper reading experience.
- A2 data/graph judgment remains mainly Chinese.
- B2 matching uses Chinese labels/items, while the missing-information question uses Japanese options.
- B3 keeps the rule judgment in Chinese and changes the case application to A–D classification rather than a generic list of actions.

This is deliberate: reproducing the exam's surface grammar includes not only answer-slot grouping but also the relationship among Japanese instructions, Chinese stimuli and the option language.

## Current strengths

- The 21–36 grouping now visibly resembles the 2026 main Q4 rather than merely having 16 slots.
- B is a real change of use: conditions → matching → missing information → process rule → two cases.
- The topic is not a noun-swap of the official pet/adoption scenario.
- The flow task is no longer just another prose question; the final two slots reuse one rule structure on two cases.

## Remaining concerns

- The library topic may still feel slightly too clean/constructed; human review should judge whether the materials feel like actual Common Test source packets rather than instructional examples.
- A2a is logically valid but the hidden-label reconstruction may feel more puzzle-like than the real paper if the surrounding table presentation is not polished.
- The flowchart wording and page layout still need visual comparison against the official booklet.
- Difficulty is uncalibrated; `official_like` only describes intended structure, not measured item difficulty.
- Chinese/Japanese typography and spacing must be checked in the rendered student view.

## Decision

Keep as an **active pilot**, not a benchmark and not approved. It should be the default UI sample until a stronger main_2026 candidate replaces it.

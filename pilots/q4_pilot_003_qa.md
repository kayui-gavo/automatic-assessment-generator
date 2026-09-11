# Pilot 003 QA — 街の明かりと星空観察

Status: **ACTIVE CANDIDATE — makeup_2026 family**

Current candidate: `q4_pilot_003_stargazing_makeup2026_v2.json`

Pilot 003 is the first candidate that deliberately follows the 2026 makeup/re-examination Q4 family instead of the main-exam family.

## Structural target

- A 21–22: discussion dialogue + choose two
- A 23–24: survey/chart statements + choose two
- A 25–26: explanatory text + annotated diagram + choose two
- A 27–28: structured lecture memo + choose two
- B 29–30: chronological notices + date/time conditions + choose two
- B 31–32: route/site map + operational memo + system/lighting diagram + choose two
- B 33–34: safety instructions + choose two
- B 35–36: post-activity reflection + choose two

## v1 → v2 correction after direct official-paper comparison

The first version reproduced the answer-slot rhythm but still flattened the option language toward Chinese. Direct comparison with the 2026 makeup booklet showed that this was wrong.

The current v2 deliberately follows the observed exam-face distribution:

- 21–22: Japanese options
- 23–24: Chinese graph-verification options
- 25–26: Japanese options
- 27–28: Japanese options
- 29–30: Japanese date/time options
- 31–32: Japanese options
- 33–34: Japanese options
- 35–36: Japanese options

This matters because Common Test Chinese is not visually or cognitively equivalent to a worksheet in which every option is Chinese. The Japanese-instruction / Chinese-stimulus / task-dependent option-language relationship is part of the 2026 surface grammar.

During the v2 author audit, A23–24 initially had more than two false statements despite asking for two inappropriate choices. This was caught manually and corrected before treating v2 as the active candidate. The incident is retained as a reminder that structural validation cannot prove semantic answer uniqueness.

## Why this topic was selected

The official makeup paper uses autonomous-driving research and field application. This pilot deliberately uses a different information journey — urban lighting and a public stargazing event — so that the surface grammar can be reproduced without copying the official topic, nouns, data, or case logic.

## Current strengths

- Every answer pair follows the makeup-family 2-slot rhythm rather than importing the main-paper matching/flow family.
- B1 genuinely combines event posts, arrival times and cancellation thresholds.
- B2 uses a compound source in which map relations, operational notes and lighting information each contribute different information.
- B3 closes with reflection rather than forcing another practical decision, matching the makeup-family ending mode.
- The option-language distribution now mirrors the actual 2026 makeup exam much more closely.
- The science content is explicitly stated in the materials; no external astronomy knowledge is required.

## Remaining concerns

- The A2 explanatory diagram is intentionally simple; human review should confirm that it is visually necessary rather than decorative.
- B2 could still be too easy if the correct statements are visually obvious from one component; blind review must test whether all three components are genuinely needed.
- The safety-instruction pair is comparatively direct and may lower the difficulty too much in the middle of B.
- The final reflection may still be more explicit than the official paper and could over-cue the two correct statements.
- The current Streamlit card preview does not yet resemble the dense black-and-white DNC booklet page. Booklet-style rendering must be reviewed separately from item semantics.

## Decision

Keep v2 as the **active makeup-family pilot**. Do not promote to benchmark until blind review, Chinese-language review, Common Test item-writing review and rendered-page inspection are complete.

# Common Test Chinese Q4 reference spec (R8 / 2026)

This file records the **functional structure** used to constrain internal original-item generation. It intentionally stores structure rather than official passages/options.

Current blueprint version: `R8-2026-main-tsui-v2`.

## Reference hierarchy

### Tier 0 — normative construct boundary

The 2026 DNC problem-making policy for non-English foreign languages emphasizes:

- understanding information, main points, details and speaker/writer intent according to purpose/situation;
- organizing understood information and deciding what/how to take up;
- assessing the language knowledge/skills supporting communication;
- considering examinees who may begin non-English foreign-language study only in high school.

This constrains **what should be measured**, not the exact Q4 surface form.

### Tier 1 — co-equal item-writing blueprints

1. R8 / 2026 main examination, Chinese
2. R8 / 2026 makeup/re-examination, Chinese

Shared features define the hard 2026 core. Differences define legitimate variation.

### Tier 2 — 2025 and earlier

Historical reference only: language level, stable constructs, distractor conventions, Japanese instruction wording and longitudinal continuity. Pre-2026 architecture never overrides Tier 1.

## Hard facts shared by both 2026 Q4 papers

- 60 points.
- Answer numbers 21–36: 16 answer slots.
- Two subsections, A and B.
- One continuing context/purpose across the section.
- Heterogeneous information sources rather than one long passage only.
- Substantial use of multiple-answer selection.
- Tasks require more than vocabulary/keyword matching: statement verification, comparison, organization, integration or contextual judgment.
- The role of information changes as the scenario develops.

These are the strongest candidates for hard constraints.

## What is **not** a hard fact

Do not infer the following as mandatory merely because it appears in one paper or one internal prototype:

- an exact number of materials;
- four or more material types;
- exactly three cross-source tasks;
- mandatory flowchart, map, table or chart;
- B must always end in practical action;
- the final task must always be case matching;
- a fixed single-choice/multi-select ratio beyond the clear prominence of multi-answer selection.

## Main examination: structural profile

The main paper moves from an everyday consultation into quantitative/statistical and institutional information, then recontextualizes the topic into service participation, profile/condition matching and process/case reasoning.

Useful abstractions:

- contextual dialogue comprehension;
- table/graph interpretation;
- comparison across related visuals;
- explanatory/institutional text comprehension;
- checklist application;
- profile + preference matching;
- identifying missing decision-relevant information;
- process/flow application to cases.

Do **not** copy the pet/animal-protection/adoption sequence.

## Makeup examination: structural profile

The makeup paper moves from inquiry/discussion into survey data, explanatory text + diagram and structured notes, then recontextualizes the topic into practical schedule planning, map/system interpretation, safety-rule verification and finally reflective synthesis.

Useful abstractions:

- organizing viewpoints/concerns from dialogue;
- verifying statements against quantitative data;
- integrating prose with diagrams;
- reading hierarchical notes;
- combining date/time/weather/crowding information;
- integrating route, reservation, operational and system information;
- interpreting action/safety rules;
- synthesizing a reflection after presentation/discussion.

Do **not** copy the autonomous-driving / municipal-bus sequence.

## Correct A/B abstraction

The earlier internal shorthand “A = receive, B = act” is too narrow.

Use:

```text
A = establish context / investigate / understand / compare / organize

B = recontextualize / apply / plan / match / reason about cases or rules / synthesize / reflect
```

The key change is **information use**, not necessarily physical action.

## Compound sources

Official-style tasks may combine several visible components into one functional source unit, e.g. prose + diagram or route map + notes + system diagram.

Internal representation uses `bundle_id` to distinguish:

- `within_compound` integration inside one source bundle;
- `cross_source` integration across independent sources/bundles.

This prevents the validator from treating every multi-component official-style source as arbitrary “cross-material reasoning”.

## Machine-readable structural metadata

See:

`blueprints/q4_2026_reference_patterns.yaml`

It records the answer-number / response-pattern / information-family structure of both 2026 Q4 papers without storing copyrighted passages.

## Sources

- University Entrance Examination Center, R8 main examination questions:  
  https://www.dnc.ac.jp/kyotsu/kakomondai/r8/r8_honshiken_mondai.html
- University Entrance Examination Center, R8 makeup/re-examination questions:  
  https://www.dnc.ac.jp/kyotsu/kakomondai/r8/r8_tuisaishiken_mondai.html
- University Entrance Examination Center, R8 problem-making policy:  
  https://www.dnc.ac.jp/news/albums/abm.php?d=355&f=abm00004500.pdf

For detailed internal interpretation, see `docs/ITEM_WRITING_DIRECTION_2026.md`.

# v0.2 end-to-end audit — 2026 baseline fidelity

## Executive verdict

v0.2 is a credible production skeleton, but it still over-encoded internal heuristics as if they were official 2026 facts.

Approximate practical score before this refactor: **7/10**.

The strongest parts were the manual-LLM workflow, answer-slot schema, blind review gate, approval gate and structured rendering. The weakest part was the boundary between **official evidence** and **our own design preference**.

## 1. Reference hierarchy

### Problem

The repository had already declared 2026 main + makeup as the primary baseline, but several files still behaved as though the main examination were the canonical template.

Examples:

- B was described mainly as practical action/decision.
- flow/process/profile matching received disproportionate emphasis.
- makeup-specific source families were not first-class schema types.

### Fix

- Tier 0: DNC 2026 problem-making policy = construct boundary only.
- Tier 1: 2026 main + makeup = co-equal item-writing blueprints.
- Tier 2: 2025 and earlier = historical reference only.

## 2. Hard rules vs internal heuristics

### Problem

v0.2 encoded several arbitrary quotas:

- minimum 3 cross-material tasks;
- minimum 4 material types;
- 6–12 materials as if near-mandatory;
- B strongly biased toward practical application.

These are useful editorial signals but are not shared official hard facts.

### Fix

Hard constraints are now limited to the strongest dual-baseline facts and schema integrity. Material count/type are soft guidance. Integration is evaluated by information dependency rather than raw source count.

## 3. Incorrect model of integration

### Problem

The validator treated “two material IDs” as the definition of integration. That misrepresents compound official sources such as:

- explanatory text + diagram;
- route map + field notes + system diagram;
- multi-post social updates.

### Fix

Add:

- `bundle_id`
- `dependency_mode = single_source | within_compound | cross_source | scenario_plus_source`

Full Q4 now requires at least one genuinely integrative task in each subsection, not an arbitrary count of three cross-source tasks.

## 4. Missing 2026 makeup material families

### Problem

The schema could represent tables/charts/flowcharts but not the makeup paper's important information forms without forcing them into the wrong type.

### Fix

Add first-class support for:

- `social_feed`
- `schematic_map`
- `annotated_diagram`
- `memo`
- `reflection`
- `interview`
- `instructions`

Also expand chart styles and allow explicit node coordinates for flow/schematic rendering.

## 5. Generation prompt

### Problem

The prompt encouraged quota satisfaction: “N materials, N types, N cross-material tasks”. This can produce synthetic-looking exam design even when all constraints pass.

### Fix

The v0.3 prompt prioritizes an information journey. Material variety must emerge from scenario needs. It explicitly distinguishes main/makeup shared core from paper-specific variation and requires every task to declare information dependency.

## 6. Blind review

### Strength

v0.2 correctly removed answer keys, evidence and rationales from the review packet.

### Remaining problem

The reviewer did not receive the full dual-baseline reference context, so “Common Test likeness” could drift according to model memory.

### Fix

Review prompts now include the blueprint, machine-readable reference patterns, Q4 template and detailed item-writing direction while remaining answer-blind.

## 7. Revision stage

### Critical problem

The old revision prompt referred to the Q4 template but did not actually inject the template/blueprint/direction. A good first draft could therefore be revised into a generic reading set.

### Fix

Generation, blind review and revision now receive the same baseline context.

## 8. Difficulty

### Problem

Default `medium` encourages a flat full section.

### Fix

Default is now `official_like`, meaning a mixed internal gradient from direct understanding to integration/application/synthesis. This is an editorial target, not a measured student difficulty estimate.

## 9. Renderer

### Strength

v0.2 already rendered table/chart/flowchart materials and answer boxes.

### Problems

- no social-feed/map/system-diagram rendering;
- flowchart coordinates were fully automatic and often visually awkward;
- teacher output omitted distractor rationales.

### Fix

Add renderers for the new material families, optional node coordinates, horizontal/stacked chart forms and richer teacher notes.

## 10. Example fixture

### Problem

`examples/q4_example_response.json` is schema-valid but not a gold-quality benchmark. Its presence without a warning can accidentally turn a regression fixture into a content template.

### Fix

Document `examples/` as schema fixtures only and create a separate `benchmarks/` location for future human-approved gold items.

## 11. Validator limits that remain

The validator can catch structural defects, but it cannot reliably determine:

- native-level Chinese naturalness;
- whether a distractor is psychologically plausible;
- real student difficulty;
- structural reskinning of an official scenario at a semantic level;
- whether an information journey feels genuinely natural.

These stay in blind LLM review + human QA.

## 12. What not to build yet

Still do not prioritize:

- paid LLM API integration;
- multi-agent frameworks;
- RAG/vector DB;
- IRT;
- web UI;
- automated psychometric difficulty prediction.

The next product question is still: **how much human rework remains after generating five real full Q4 sets?**

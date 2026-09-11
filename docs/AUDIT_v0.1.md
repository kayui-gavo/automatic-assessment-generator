# v0.1 Production Audit

v0.1 succeeded as a workflow proof-of-concept but was not yet an adequate production model for high-fidelity Common Test Chinese Q4 authoring.

## Critical findings

1. **The data model reduced Q4 to ordinary MCQs.** `Question.correct_option` could express only one answer per question. It could not represent two-answer selection, multiple answer boxes sharing one option pool, or case-by-case matching.
2. **The target size was wrong.** The default was six questions. The 2026 main examination Q4 uses answer numbers 21–36: sixteen answer slots across subsections A and B.
3. **Materials were plain strings.** Tables, charts and flowcharts were mentioned in prompts but could not be represented or rendered structurally.
4. **The “independent” review was not independent.** The review prompt exposed `correct_option`, evidence and rationales, causing answer anchoring.
5. **Approval was too permissive.** Any schema-valid item could be moved into the approved bank without a passing independent review.
6. **Originality was only a prompt instruction.** There was no local duplicate/similarity guard against the institution's own item bank.
7. **The renderer looked like a generic worksheet.** Every material was a tcolorbox, task blocks could split badly across pages, and structured information had no authentic rendering path.
8. **Blueprint knowledge was too shallow.** It recorded score and section names but not the functional A/B progression, response-mode diversity, or answer-number structure.
9. **There was no version pinning.** A future Common Test change could silently invalidate assumptions.
10. **The example was too easy to satisfy.** Passing tests mostly proved JSON validity, not that the system encoded the intended exam architecture.

## v0.2 response

v0.2 therefore prioritizes representation and quality gates over UI:

- schema supports `single_choice`, `multi_select`, and `multi_slot_choice`;
- full Q4 requires answer numbers 21–36 exactly once;
- materials are typed (`dialogue`, `table`, `chart`, `flowchart`, etc.);
- A/B order is explicit and materials/tasks can be interleaved through `order`;
- evidence requires a human-checkable locator;
- review requests are blind: answer keys, evidence and rationales are stripped;
- review answers are programmatically compared with the author key;
- approval requires a passing blind review unless explicitly overridden;
- a lightweight 5-gram similarity guard checks the approved bank;
- multi-slot distractor explanations are stored per answer slot;
- LaTeX rendering supports tables, charts and flowcharts and uses a print-oriented exam layout.

The remaining bottleneck is no longer “can the repository express Q4?” but “can the generation prompt consistently produce high-quality content inside this schema?” That should be evaluated by generating real candidate sets and measuring human revision time.

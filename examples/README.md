# Examples

Files in this directory are **schema/regression fixtures**.

They exist to exercise:

- answer-slot structure;
- material/task interleaving;
- response modes;
- validator behavior;
- renderer behavior.

They are **not** approved TABITO item-writing exemplars and must not be used as few-shot gold examples for generation.

In particular, `q4_example_response.json` predates the 2026 dual-baseline v2 audit. It remains useful for backward-compatible regression tests, but its content quality and information journey are not the standard we want future generated sets to imitate.

Human-approved content exemplars belong in `benchmarks/`, not here.

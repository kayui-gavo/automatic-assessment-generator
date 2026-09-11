# Content-QA pilots

This directory contains **intentional, versioned pilot candidates** used to test whether the TABITO Q4 workflow actually reduces human editing work.

Files here are neither schema fixtures (`examples/`) nor approved gold benchmarks (`benchmarks/`).

A pilot may be rough, revised, or rejected. Keep its QA log beside it so prompt/schema/validator improvements are grounded in observed rework rather than intuition.

## Current status

| Pilot | Family | Status | Purpose |
| --- | --- | --- | --- |
| Pilot 001 — reuse station | legacy generic | **REJECTED** | Failure sample showing that abstract “multi-source reading” is not enough to resemble 2026 Q4 |
| Pilot 002 — library study spaces | `main_2026` | **ACTIVE CANDIDATE** | Reproduce the 2026 main-paper 21–36 surface grammar with original content |
| Pilot 003 — urban lighting / stargazing | `makeup_2026` | **ACTIVE CANDIDATE** | Reproduce the 2026 makeup-paper surface family with original content |

The UI should default to Pilot 002, not Pilot 001. Pilot 001 remains only as a calibration failure sample.

Promotion path:

```text
pilot candidate
→ deterministic 2026 surface-family validation
→ blind review
→ human Chinese review
→ human Common Test item-writing review
→ rendering / booklet-likeness check
→ revision
→ only then, if genuinely exemplary, copy to benchmarks/
```

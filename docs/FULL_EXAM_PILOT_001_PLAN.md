# Pilot Exam 001 — production validation plan

## Purpose

Pilot Exam 001 is the first content-quality stress test of v0.5. It is not a schema fixture and must not be treated as a gold benchmark until human QA is complete.

The goal is to learn where a real 80-minute / 200-point / 50-answer mock exam still creates teacher rework.

## Frozen production contract

- Exam family: `main_2026`
- Duration: 80 minutes
- Total score: 200
- Answer numbers: 1–50 exactly once
- Sections: Q1–Q5
- Q4: 21–36, A/B progression, original scenario, no official reskin
- Q5: 37–50, coherent original long-form passage with visible anchors
- Manual ChatGPT generation remains the LLM backend
- Human QA is mandatory
- Do not auto-approve any section because deterministic validation or blind review passes

## Pilot topic separation

Use deliberately different semantic domains so the whole booklet does not feel AI-repetitive.

- Q1: everyday pronunciation/dialogue micro-contexts; no single shared story
- Q2: school / daily-life lexical and ordering contexts
- Q3: translation situations spread across study, travel, communication and daily decisions
- Q4: **地域防災イベント** — participants read schedule, role allocation, facility map/rules and later adapt a plan under new constraints
- Q5: **古い商店街の共同配送と店主の変化** — narrative/expository long passage about how a small shopping street experiments with shared delivery and how one shop owner changes her view

Q4 and Q5 must not share the same scenario architecture, characters, visual logic or decision pattern.

## Human QA data to collect

For every section record:

- first-read minutes
- language-edit minutes
- item-edit minutes
- layout-edit minutes
- disposition: approve / revise / reject
- defect categories
- largest source of rework
- whether answer key changed
- whether blind reviewer disagreed

For the whole exam record:

- full-exam first-read minutes
- layout-fix minutes
- cross-section-fix minutes
- perceived 80-minute feasibility
- difficulty rhythm
- repeated wording / repeated scenario-pattern defects
- pagination defects

## Stop conditions

Do not polish endlessly. Stop Pilot 001 and log a defect if any section requires near-total rewrite because the current generation contract is wrong. That is a product signal, not a reason to hide the failure.

## v0.5 → v0.5.1 decision rule

After Pilot 001, only fix issues that are either:

1. release-blocking correctness bugs,
2. repeated across multiple sections,
3. likely to recur in Pilot 002,
4. responsible for substantial human rework.

Do not add RAG, agents, IRT, a paid API, or new framework layers because of a single awkward item.

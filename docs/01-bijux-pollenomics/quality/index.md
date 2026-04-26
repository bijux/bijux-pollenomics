---
title: Quality
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Quality

This section documents the proof surface for `bijux-pollenomics`: tests,
review rules, invariants, risk tracking, and documentation expectations.

Use it when the question is not only what the package does, but how the
repository proves that it still does it correctly.

```mermaid
flowchart LR
    tests["test strategy"]
    validation["change validation"]
    invariants["invariants"]
    docs["documentation standards"]
    risks["known limitations and risk register"]
    reader["reader question<br/>what evidence supports this change?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class tests,page reader;
    class validation,invariants,docs,risks positive;
    tests --> reader
    validation --> reader
    invariants --> reader
    docs --> reader
    risks --> reader
```

## Start Here

- open [Test Strategy](test-strategy.md) for the proof structure across unit,
  regression, and end-to-end work
- open [Change Validation](change-validation.md) when deciding what to run for a
  concrete change
- open [Known Limitations](known-limitations.md) and [Risk Register](risk-register.md)
  before promising more than the package currently proves

## Pages In This Section

- [Test Strategy](test-strategy.md)
- [Invariants](invariants.md)
- [Review Checklist](review-checklist.md)
- [Documentation Standards](documentation-standards.md)
- [Definition of Done](definition-of-done.md)
- [Dependency Governance](dependency-governance.md)
- [Change Validation](change-validation.md)
- [Known Limitations](known-limitations.md)
- [Risk Register](risk-register.md)

## What This Section Should Answer

- which checks prove which kinds of changes
- which truths should remain stable even as the code evolves
- where the package still has deliberate limitations or ongoing review risk

## Purpose

This page organizes the evidence, review, and risk material that protects the
runtime package.

---
title: Quality
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Quality

Use this section when the question is how the repository proves a runtime
change is safe: which tests matter, which invariants must still hold, what
documentation needs to move with the code, and where the package still carries
known evidence limits.

This package does not prove correctness only through unit tests. It also has to
prove that tracked data layouts, published reports, and map-facing outputs still
match the contracts readers and reviewers rely on.

```mermaid
flowchart LR
    tests["pick the narrowest meaningful test layer"]
    validation["run change-shaped validation"]
    invariants["defend stable truths about outputs"]
    docs["update docs when public behavior moves"]
    risks["name limits and remaining uncertainty"]
    reader["reader question<br/>what evidence makes this runtime change believable?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class validation,page reader;
    class tests,invariants,docs positive;
    class risks caution;
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
- open [Invariants](invariants.md) when a change could disturb tracked data or
  publication truths that must remain stable
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

## Use This Section When

- you need to choose validation that matches a concrete runtime change
- reviewers need to know what evidence should accompany a data or report diff
- the package may still work locally, but the repository needs stronger proof

## Do Not Use This Section When

- the question is mainly how to run the package rather than how to prove it
- you need package purpose or ownership boundaries before choosing evidence
- the primary issue is interface wording rather than validation or risk

## Read Across The Package

- open [Foundation](../foundation/index.md) when quality debate is really about
  what the runtime is supposed to own
- open [Architecture](../architecture/index.md) when the right proof depends on
  where behavior sits in dispatch, collection, or reporting
- open [Interfaces](../interfaces/index.md) when the evidence needs to defend a
  CLI, file layout, or publication artifact contract
- open [Operations](../operations/index.md) when validation requires a specific
  rebuild, recovery, or release procedure

## Reader Takeaway

Use `Quality` to make changes believable, not merely plausible. If a runtime
claim cannot be backed by named tests, explicit invariants, updated docs, and a
clear statement of remaining limits, it is not yet ready for repository review.

## Purpose

This page introduces the proof, review, and risk handbook for
`bijux-pollenomics`.

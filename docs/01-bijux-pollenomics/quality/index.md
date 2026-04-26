---
title: Quality
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Quality

This section is for readers whose question is how the repository proves a
runtime change is safe: which tests matter, which invariants must still hold,
what documentation needs to move with the code, and where the package still
carries known evidence limits.

This package does not prove correctness only through unit tests. It also has to
prove that tracked data layouts, published reports, and map-facing outputs still
match the contracts readers and reviewers rely on.

For this repository, quality is not only about whether the Python code still
works. It is also about whether a visible atlas change, a country-report diff,
or a shifted data layout can still be explained with enough named evidence that
reviewers do not have to guess what changed or why it is acceptable.

```mermaid
flowchart LR
    reader["reader question<br/>what makes this runtime change believable?"]
    tests["pick the narrowest<br/>meaningful test layer"]
    invariants["defend stable truths<br/>about data and reports"]
    outputs["check data/ and atlas-facing<br/>output consequences"]
    docs["update docs when public<br/>behavior moves"]
    risks["name limits and remaining<br/>uncertainty"]
    validation["run change-shaped validation"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class reader page;
    class tests,validation,invariants,docs,outputs positive;
    class risks caution;
    tests --> reader
    invariants --> reader
    outputs --> reader
    docs --> reader
    risks --> reader
    validation --> reader
```

## Start Here

- use [Test Strategy](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/test-strategy/) for the proof structure across unit,
  regression, and end-to-end work
- use [Change Validation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/change-validation/) when deciding what to run for a
  concrete change
- use [Invariants](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/invariants/) when a change could disturb tracked data or
  publication truths that must remain stable
- use [Known Limitations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/known-limitations/) and [Risk Register](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/risk-register/)
  before promising more than the package currently proves
- use [Definition of Done](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/definition-of-done/) when a change touches
  checked-in publication outputs and needs a clear merge bar

## Published Quality Pages

- [Test Strategy](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/test-strategy/)
- [Invariants](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/invariants/)
- [Review Checklist](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/review-checklist/)
- [Documentation Standards](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/documentation-standards/)
- [Definition of Done](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/definition-of-done/)
- [Dependency Governance](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/dependency-governance/)
- [Change Validation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/change-validation/)
- [Known Limitations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/known-limitations/)
- [Risk Register](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/risk-register/)

## Use This Section When

- you need to choose validation that matches a concrete runtime change
- reviewers need to know what evidence should accompany a data or report diff
- the package may still work locally, but the repository needs stronger proof

## Move On When

- the question is mainly how to run the package rather than how to prove it
- you need package purpose or ownership boundaries before choosing evidence
- the primary issue is interface wording rather than validation or risk

## What This Section Clarifies

- which test layers defend code behavior versus tracked repository outputs
- which visible atlas or report consequences should be reviewed even after the
  tests pass
- which remaining limits must still be stated honestly so a green run is not
  mistaken for scientific completeness

## Concrete Anchors

- `tests/unit/` for narrow behavior checks on layout, source normalization, and
  configuration
- `tests/regression/test_data_collector.py`,
  `tests/regression/test_country_report.py`, and
  `tests/regression/test_repository_contracts.py` for tracked output and
  repository-surface proof
- `tests/e2e/test_cli.py` for the end-to-end command contract
- `docs/report/nordic-atlas/` for the public publication surface whose
  consequences quality review must keep visible

## Read Across The Package

- open [Foundation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/) when quality debate is really about
  what the runtime is supposed to own
- open [Architecture](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/) when the right proof depends on
  where behavior sits in dispatch, collection, or reporting
- open [Interfaces](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/) when the evidence needs to defend a
  CLI, file layout, or publication artifact contract
- open [Operations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/) when validation requires a specific
  rebuild, recovery, or release procedure

## Reader Takeaway

Use `Quality` to make changes believable, not merely plausible. If a runtime
claim cannot be backed by named tests, explicit invariants, updated docs, and a
clear statement of remaining limits, it is not yet ready for repository review.

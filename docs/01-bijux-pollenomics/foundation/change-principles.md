---
title: Change Principles
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Change Principles

Changes to `bijux-pollenomics` should make the runtime easier to trust, not
just easier to modify. The hardest tradeoff here is convenience versus review:
shortcuts that save a little implementation effort often make visible output
changes harder to defend later.

## Principles

- prefer explicit filenames, slugs, and command defaults over hidden convention
- keep source collection, normalization, and reporting as distinguishable steps
- treat tracked `data/` and `docs/report/` rewrites as review-significant
  events
- document boundary changes when the package starts owning a new responsibility
- preserve deterministic local rebuild paths before adding convenience layers

## Anti-Patterns

- mixing maintenance policy into runtime modules
- adding one-off output names that do not fit the existing file contracts
- expanding package scope because a nearby repository surface looks convenient

## First Proof Check

- `tests/regression/test_repository_contracts.py`
- `tests/regression/test_data_collector.py`
- `tests/regression/test_country_report.py`

## Boundary Test

If a change cannot preserve explicit commands, stable file contracts, and
reviewable output diffs at the same time, the design is not finished yet.

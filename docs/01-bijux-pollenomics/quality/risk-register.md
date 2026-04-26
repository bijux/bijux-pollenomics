---
title: Risk Register
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Risk Register

The highest current risks are not equal. The most serious ones are the ones
that make visible evidence changes harder to explain.

## Active Risks

- source refreshes can produce large tracked diffs that hide the meaningful
  logic change
- mutable upstream services can introduce surprising data churn
- report artifact contract changes can ripple into docs and review tooling
- incomplete doc migration can leave stale internal links

## First Proof Check

- workflow boundaries
- output naming rules
- docs and tests moving with public contract changes
- strict docs build and regression tests

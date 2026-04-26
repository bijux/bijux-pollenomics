---
title: Repository Fit
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Repository Fit

This package fits the repository because the repository publishes checked-in
evidence outputs and needs one accountable runtime that can regenerate them.
Without that runtime, collection rules, normalization rules, and publication
logic would drift into ad hoc scripts and hand-edited trees.

## Why The Split Exists

- command entrypoints stay explicit instead of living in shell-only flow
- collection and reporting behavior can be tested as package behavior
- visible atlas and report changes can be traced back to one owning runtime

## First Proof Check

- `packages/bijux-pollenomics/src/bijux_pollenomics/`
- `packages/bijux-pollenomics/tests/`
- `data/`
- `docs/report/`

## Boundary Test

If the package cannot make visible output changes easier to trace and review,
the split is no longer earning its place in the repository.

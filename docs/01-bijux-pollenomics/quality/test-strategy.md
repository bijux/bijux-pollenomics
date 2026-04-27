---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Test Strategy

`bijux-pollenomics` uses layered tests so command behavior, file contracts, and
source-specific transformations can fail close to the defect.

## Current Layers

- `tests/unit/` for focused module and helper behavior such as command parsing,
  data layout rules, source normalization, geometry helpers, and reporting
  artifact routines
- `tests/regression/` for stable output and repository contract behavior such
  as docs conventions, workflow assumptions, and bundle-level expectations
- `tests/e2e/` for CLI-level flows that prove the installed command surface

## Choose The Narrowest Honest Layer

- start with `tests/unit/` when the change is local to a helper, parser,
  normalization rule, or renderer
- widen to `tests/regression/` when the contract lives in tracked outputs,
  repository conventions, or docs-facing publication behavior
- use `tests/e2e/` when the risk is the command flow itself rather than one
  internal implementation seam

## Important Local Anchors

- `tests/unit/test_command_line.py` and `tests/e2e/test_cli.py` cover the
  operator-facing command surface at different depths
- `tests/unit/test_data_layout.py` and source-specific unit tests protect the
  tracked data shape and source normalization logic
- `tests/unit/test_reporting_artifacts.py` checks publication asset behavior
- `tests/regression/test_repository_contracts.py` protects repository and docs
  assumptions that should not drift unnoticed

## First Proof Check

- `tests/unit/`
- `tests/regression/`
- `tests/e2e/test_cli.py`

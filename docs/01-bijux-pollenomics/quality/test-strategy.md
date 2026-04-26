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
source-specific transformations can fail close to the defect. The goal is not
to accumulate test volume. The goal is to prove the exact runtime surface that a
change risks disturbing.

```mermaid
flowchart LR
    unit["unit tests for helpers, parsers, and focused transforms"]
    regression["regression tests for repository and output contracts"]
    e2e["end-to-end tests for CLI flows"]
    change["reader question<br/>which proof layer matches this change?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class unit,page change;
    class regression,e2e positive;
    unit --> change
    regression --> change
    e2e --> change
```

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

## Strategy Rule

Add the narrowest test that proves the contract you are changing, then widen to
regression or end-to-end coverage only when the package boundary itself is what
changed.

## Open This Page When

- you need to decide which test suite should move with a runtime change
- a review asks for stronger proof and you need to justify the next layer
- a diff touches `data/`, `docs/report/`, or command behavior and the right
  validation is not obvious

## Common Mistakes

- jumping straight to end-to-end tests when a precise unit or regression check
  would prove the same contract more cleanly
- adding unit tests for behavior that is only meaningful as a tracked output or
  repository-level contract
- treating generated evidence diffs as self-validating instead of pairing them
  with explicit tests

## Reader Takeaway

More test layers are not automatically better. The honest goal is the smallest
proof surface that still matches the real contract risk and leaves reviewers
with a believable explanation for the change.


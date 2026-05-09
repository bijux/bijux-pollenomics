---
title: Test Strategy
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Test Strategy

`bijux-pollenomics` uses layered tests so command behavior, file contracts, and
source-specific transformations fail close to the defect.

The purpose of the test strategy is not to make every change expensive. It is
to make the right failure appear at the right layer, early enough that the
reader can understand what broke.

Use this page when your question is:

- what kind of checking stands behind the repository
- why one change needs a narrow test while another needs a broader gate
- what a passing suite does and does not prove

## Current Layers

- `tests/unit/` for focused module and helper behavior such as command parsing,
  data layout rules, source normalization, geometry helpers, and reporting
  artifact routines
- `tests/regression/` for stable output and repository contract behavior such
  as docs conventions, workflow assumptions, and bundle-level expectations
- `tests/e2e/` for CLI-level flows that prove the installed command surface

Those layers are different on purpose:

- unit tests answer "did this narrow rule still hold"
- regression tests answer "did the repository-owned surface drift"
- end-to-end tests answer "does the installed command path still behave"

## Choose The Narrowest Honest Layer

- start with `tests/unit/` when the change is local to a helper, parser,
  normalization rule, or renderer
- widen to `tests/regression/` when the contract lives in tracked outputs,
  repository conventions, or docs-facing publication behavior
- use `tests/e2e/` when the risk is the command flow itself rather than one
  internal implementation seam

That "narrowest honest layer" rule matters for speed as well as rigor. A slow
test suite is only useful when it is aimed at the right question.

## What Passing Tests Mean Here

- the checked boundary behaved as expected
- the repository caught a specific class of drift
- one surface remains reviewable

They do not automatically mean:

- that the public wording is proportionate
- that the evidence is complete
- that a polished output is stronger than before

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

## Reader-Facing Implication

The testing model is designed to keep failures close to the real question.
That is good for maintainers, but it also matters for readers: when a surface
is published, the repository should be able to say what kind of proof actually
stands behind it.

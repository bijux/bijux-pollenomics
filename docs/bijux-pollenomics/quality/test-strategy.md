---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Test Strategy

`bijux-pollenomics` uses layered tests so command behavior, file contracts, and
source-specific transformations can fail close to the defect.

## Current Layers

- `tests/unit/` for focused module and helper behavior
- `tests/regression/` for stable output and repository contract behavior
- `tests/e2e/` for CLI-level flows

## Strategy Rule

Add the narrowest test that proves the contract you are changing, then widen to
regression or end-to-end coverage only when the package boundary itself is what
changed.

## Purpose

This page records how the package proves correctness across different scopes.

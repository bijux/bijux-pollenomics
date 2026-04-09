---
title: Risk Register
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Risk Register

## Active Risks

- source refreshes can produce large tracked diffs that hide the meaningful
  logic change
- mutable upstream services can introduce surprising data churn
- report artifact contract changes can ripple into docs and review tooling
- incomplete doc migration can leave stale internal links

## Current Mitigations

- keep workflow boundaries explicit
- build docs strictly
- preserve output naming rules in one place
- require docs and tests to move with public contract changes

## Purpose

This page gives maintainers one place to record the current runtime risks.

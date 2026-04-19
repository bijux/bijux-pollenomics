---
title: Change Principles
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Change Principles

Changes to `bijux-pollenomics` should make the runtime easier to trust, not
just easier to modify.

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

## Purpose

This page records the package-level rules that should shape future changes.

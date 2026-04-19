---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Invariants

Certain truths should remain stable across ordinary package changes.

## Package Invariants

- commands either validate or rewrite tracked outputs deliberately
- source outputs stay grouped by source under `data/<source>/`
- report outputs stay grouped under `docs/report/`
- defaults in `config.py` remain the single obvious source for package-wide
  paths and publication identity
- public imports from `bijux_pollenomics` continue to describe real workflow
  entrypoints

## Purpose

This page records the runtime truths that reviewers should defend first.

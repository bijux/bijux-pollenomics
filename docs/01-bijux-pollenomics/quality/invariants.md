---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
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

## First Proof Check

- `tests/unit/test_config.py`
- `tests/unit/test_data_layout.py`
- `tests/regression/test_repository_contracts.py`

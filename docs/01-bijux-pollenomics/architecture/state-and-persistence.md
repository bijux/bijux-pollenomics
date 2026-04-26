---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# State and Persistence

Persistent state in `bijux-pollenomics` is primarily file state. That matters
because review depends on knowing which writes are durable, which files are
authoritative, and which run products are disposable.

## Durable State

- tracked source files under `data/<source>/raw/`
- normalized outputs under `data/<source>/normalized/`
- published report bundles under `docs/report/`
- frozen API contracts under `apis/bijux-pollenomics/v1/`

## Non-Durable State

- virtual environments and build artifacts under `artifacts/`
- command-local in-memory objects used during collection and reporting

## First Proof Check

- `data/`
- `docs/report/`
- `apis/bijux-pollenomics/v1/`
- `tests/regression/test_repository_contracts.py`

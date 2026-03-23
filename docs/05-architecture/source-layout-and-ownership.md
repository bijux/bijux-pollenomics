---
title: Source Layout and Ownership
audience: mixed
type: explanation
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Source Layout and Ownership

The source tree is intentionally split between three concerns:

- command surface
- data acquisition
- report generation

## Current Layout

```text
src/bijux_pollen
├── __init__.py
├── cli.py
├── reporting.py
└── data_downloader
    ├── aadr.py
    ├── boundaries.py
    ├── collector.py
    ├── common.py
    ├── context.py
    ├── geometry.py
    ├── models.py
    ├── neotoma.py
    ├── raa.py
    ├── sead.py
    └── writers.py
```

## Ownership Model

- `cli.py` owns command parsing and user-facing entry points
- `data_downloader/` owns source acquisition and normalization
- `reporting.py` owns report and map generation

## Why `reporting.py` Is Still Separate

Report generation is downstream of the data collectors, but it is not itself a data source. Keeping it separate prevents the downloader package from becoming a general “everything” namespace again.

## Purpose

This page records the intended source boundary so later refactors can preserve the same structure.

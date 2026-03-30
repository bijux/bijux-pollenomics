---
title: Source Layout and Ownership
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Source Layout and Ownership

The source tree is intentionally split between three concerns:

- command surface
- data acquisition
- report generation

## Current Layout

```text
src/bijux_pollenomics
├── __init__.py
├── cli.py
├── settings.py
├── reporting
│   ├── __init__.py
│   ├── aadr.py
│   ├── artifacts.py
│   ├── context_layers.py
│   ├── html.py
│   ├── markdown.py
│   ├── models.py
│   ├── paths.py
│   ├── service.py
│   └── utils.py
└── data_downloader
    ├── aadr.py
    ├── boundaries.py
    ├── collector.py
    ├── common.py
    ├── contracts.py
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
- `settings.py` owns shared defaults for the current checked-in publication scope
- `data_downloader/` owns source acquisition and normalization
- `reporting/` owns report and map generation
- `reporting/service.py` orchestrates report and map builds
- `reporting/html.py` owns the standalone map document
- `reporting/aadr.py` owns AADR sample loading and locality aggregation
- `data_downloader/contracts.py` owns normalized data artifact names
- `reporting/paths.py` owns generated report-bundle artifact names

## Collector Shape

`data_downloader/collector.py` now uses an explicit context-source registry instead of one hardcoded branch per source. That keeps adding or reordering context collectors localized to one place instead of spreading dispatch rules across the module.

## Why `reporting/` Is Separate

Report generation is downstream of the data collectors, but it is not itself a data source. Keeping it in a separate package prevents the downloader package from becoming a general “everything” namespace again, while still letting the reporting code be split into focused modules instead of one long file.

## Purpose

This page records the intended source boundary so later refactors can preserve the same structure.

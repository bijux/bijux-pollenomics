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
├── __main__.py
├── cli.py
├── command_line
│   ├── __init__.py
│   ├── arguments.py
│   ├── dispatch.py
│   └── handlers.py
├── project.py
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
    ├── data_layout.py
    ├── geometry.py
    ├── models.py
    ├── neotoma.py
    ├── raa.py
    ├── sead.py
    ├── source_registry.py
    ├── staging.py
    └── writers.py
```

## Ownership Model

- `cli.py` owns the stable top-level entry point only
- `command_line/arguments.py` owns argument composition
- `command_line/dispatch.py` owns command routing
- `command_line/handlers.py` owns user-facing command behavior
- `project.py` owns canonical project defaults and path roots
- `settings.py` owns shared defaults for the current checked-in publication scope
- `data_downloader/` owns source acquisition and normalization
- `data_downloader/collector.py` owns high-level data-collection orchestration only
- `data_downloader/source_registry.py` owns the tracked context-source registry
- `data_downloader/staging.py` owns safe swap-in staging behavior
- `data_downloader/data_layout.py` owns generated data-root layout contracts
- `reporting/` owns report and map generation
- `reporting/service.py` orchestrates report and map builds
- `reporting/html.py` owns the standalone map document
- `reporting/aadr.py` owns AADR sample loading and locality aggregation
- `data_downloader/contracts.py` owns normalized data artifact names
- `reporting/paths.py` owns generated report-bundle artifact names

## Collector Shape

The collector path is intentionally split into three seams:

- orchestration in `data_downloader/collector.py`
- source registration in `data_downloader/source_registry.py`
- staging and generated layout contracts in `data_downloader/staging.py` and `data_downloader/data_layout.py`

That keeps adding or reordering context collectors localized to one place instead of spreading dispatch rules, README rendering, and staging behavior across the same module.

## Why `reporting/` Is Separate

Report generation is downstream of the data collectors, but it is not itself a data source. Keeping it in a separate package prevents the downloader package from becoming a general “everything” namespace again, while still letting the reporting code be split into focused modules instead of one long file.

## Purpose

This page records the intended source boundary so later refactors can preserve the same structure.

---
title: Codebase Layout and Ownership
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Codebase Layout and Ownership

The source tree is intentionally split between three concerns:

- command surface
- data acquisition
- report generation

## Codebase Layout

```text
src/bijux_pollenomics
├── __init__.py
├── __main__.py
├── cli.py
├── config.py
├── command_line
│   ├── __init__.py
│   ├── arguments.py
│   ├── dispatch.py
│   ├── handlers.py
│   ├── options.py
│   ├── parser.py
│   ├── registry.py
│   └── subcommands.py
├── project.py
├── settings.py
├── reporting
│   ├── __init__.py
│   ├── aadr_localities.py
│   ├── aadr_samples.py
│   ├── aadr_schema.py
│   ├── aadr.py
│   ├── api.py
│   ├── artifacts.py
│   ├── context_point_layers.py
│   ├── context_polygon_layers.py
│   ├── context_time.py
│   ├── context_layers.py
│   ├── countries.py
│   ├── html.py
│   ├── map_document/
│   ├── markdown.py
│   ├── models.py
│   ├── paths.py
│   ├── service.py
│   ├── staging.py
│   ├── summaries.py
│   └── utils.py
└── data_downloader
    ├── api.py
    ├── aadr.py
    ├── boundary_sources.py
    ├── boundaries.py
    ├── collector.py
    ├── common.py
    ├── context_collectors.py
    ├── context_collection.py
    ├── contracts.py
    ├── context.py
    ├── data_layout.py
    ├── geometry.py
    ├── landclim.py
    ├── models.py
    ├── neotoma.py
    ├── requested_sources.py
    ├── raa.py
    ├── sead_fetch.py
    ├── sead_normalization.py
    ├── sead.py
    ├── source_registry.py
    ├── staging.py
    ├── summary_writer.py
    ├── xlsx.py
    └── writers.py
```

## Ownership Model

- `cli.py` owns the stable top-level entry point only
- `config.py` owns the canonical defaults model and flattened constants
- `command_line/parser.py` owns root parser composition
- `command_line/options.py` owns reusable option groups
- `command_line/subcommands.py` owns subcommand-specific parser assembly
- `command_line/runtime/dispatch.py` owns command routing
- `command_line/registry.py` owns the direct-command handler registry
- `command_line/handlers.py` owns user-facing command behavior
- `project.py` and `settings.py` remain compatibility views over `config.py`
- `data_downloader/` owns source acquisition and normalization
- `data_downloader/api.py` owns the public downloader package surface
- `data_downloader/collector.py` owns high-level data-collection orchestration only
- `data_downloader/pipeline/requested_sources.py` owns source-selection normalization
- `data_downloader/sources/boundaries/sources.py` owns boundary reuse and fallback policy
- `data_downloader/pipeline/context_collection.py` owns context-source execution into staged directories
- `data_downloader/pipeline/context_collectors.py` owns the executable collector registry
- `data_downloader/pipeline/source_registry.py` owns tracked source metadata only
- `data_downloader/pipeline/staging.py` owns safe swap-in staging behavior
- `data_downloader/data_layout.py` owns generated data-root layout contracts
- `data_downloader/pipeline/summary_writer.py` owns collection-summary serialization
- `reporting/` owns report and map generation
- `reporting/api.py` owns the public reporting package surface
- `reporting/service.py` orchestrates report and map builds
- `reporting/map_document/` owns the standalone map template and derived render state
- `reporting/context/layers.py` owns top-level context-layer orchestration only
- `reporting/context/points/`, `reporting/context/polygons/`, and `reporting/context/time.py` own map-layer shaping details
- `reporting/aadr/` owns AADR report loading seams
- `reporting/bundles/summary_builders/` owns machine-readable report summary payloads
- `reporting/countries.py` owns country-list normalization for report workflows
- `reporting/bundles/staging.py` owns safe swap-in staging for generated publication trees
- `data_downloader/contracts.py` owns normalized data artifact names
- `reporting/bundles/paths.py` owns generated report-bundle artifact names

## Collector Shape

The collector path is intentionally split into three seams:

- orchestration in `data_downloader/collector.py`
- source metadata in `data_downloader/pipeline/source_registry.py` plus executable registry in `data_downloader/pipeline/context_collectors.py`
- staging and generated layout contracts in `data_downloader/pipeline/staging.py` and `data_downloader/data_layout.py`

That keeps adding or reordering context collectors localized to the registry modules instead of spreading dispatch rules, boundary reuse policy, README rendering, and staging behavior across the same module.

## Why `reporting/` Is Separate

Report generation is downstream of the data collectors, but it is not itself a data source. Keeping it in a separate package prevents the downloader package from becoming a general “everything” namespace again, while still letting the reporting code be split into focused modules instead of one long file.

## Purpose

This page records the intended source boundary so later refactors can preserve the same structure.

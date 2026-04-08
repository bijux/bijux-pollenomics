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
packages/bijux-pollenomics/src/bijux_pollenomics
├── __init__.py
├── __main__.py
├── cli.py
├── config.py
├── command_line
│   ├── parsing
│   │   ├── options.py
│   │   ├── parser.py
│   │   └── subcommands.py
│   └── runtime
│       ├── dispatch.py
│       ├── handlers.py
│       └── registry.py
├── core
│   ├── bp_time.py
│   ├── files.py
│   ├── http.py
│   └── text.py
├── reporting
│   ├── api.py
│   ├── models.py
│   ├── service.py
│   ├── aadr
│   │   ├── api.py
│   │   ├── localities.py
│   │   ├── samples.py
│   │   └── schema.py
│   ├── bundles
│   │   ├── atlas_bundle.py
│   │   ├── country_bundle.py
│   │   ├── country_selection.py
│   │   ├── map_inputs.py
│   │   ├── paths.py
│   │   ├── published_reports.py
│   │   ├── staging.py
│   │   └── summary_builders
│   ├── context
│   │   ├── artifacts.py
│   │   ├── layers.py
│   │   ├── points
│   │   ├── polygons
│   │   └── time.py
│   ├── map_document/
│   ├── rendering
│   │   ├── artifacts.py
│   │   ├── html.py
│   │   ├── markdown.py
│   │   └── record_exports.py
│   └── shared
│       ├── merge.py
│       └── text.py
└── data_downloader
    ├── api.py
    ├── boundaries.py
    ├── collector.py
    ├── contracts.py
    ├── data_layout.py
    ├── landclim.py
    ├── models.py
    ├── neotoma.py
    ├── raa.py
    ├── sead.py
    ├── pipeline
    │   ├── collection_reports.py
    │   ├── context_collection.py
    │   ├── context_collectors.py
    │   ├── requested_sources.py
    │   ├── source_registry.py
    │   ├── staging.py
    │   └── summary_writer.py
    ├── shared
    │   ├── context_exports.py
    │   └── workbooks.py
    ├── sources
    │   ├── aadr
    │   ├── boundaries
    │   ├── landclim
    │   ├── neotoma
    │   ├── raa
    │   └── sead
    └── spatial
        ├── bboxes.py
        ├── country_classification.py
        ├── grid_cells.py
        └── representative_points.py
```

## Ownership Model

- `cli.py` owns the stable top-level entry point only
- `config.py` owns the canonical defaults model and flattened constants
- `command_line/parsing/parser.py` owns root parser composition
- `command_line/parsing/options.py` owns reusable option groups
- `command_line/parsing/subcommands.py` owns subcommand-specific parser assembly
- `command_line/runtime/dispatch.py` owns command routing
- `command_line/runtime/registry.py` owns the direct-command handler registry
- `command_line/runtime/handlers.py` owns user-facing command behavior
- `core/http.py`, `core/files.py`, `core/text.py`, and `core/bp_time.py` own reusable cross-domain helpers rather than downloader-specific shims
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
- `data_downloader/shared/context_exports.py` and `data_downloader/shared/workbooks.py` own shared export and workbook helpers
- `data_downloader/spatial/` owns collector-facing bounding-box, country-classification, grid, and representative-point helpers
- `data_downloader/sources/` owns source-specific fetch, archive, and normalization details
- `reporting/` owns report and map generation
- `reporting/api.py` owns the public reporting package surface
- `reporting/service.py` orchestrates report and map builds
- `reporting/map_document/` owns the standalone map template and derived render state
- `reporting/context/artifacts.py` owns copied context-artifact staging
- `reporting/context/layers.py` owns top-level context-layer orchestration only
- `reporting/context/points/`, `reporting/context/polygons/`, and `reporting/context/time.py` own map-layer shaping details
- `reporting/aadr/` owns AADR report loading seams
- `reporting/bundles/summary_builders/` owns machine-readable report summary payloads
- `reporting/bundles/country_selection.py` owns country-list normalization for report workflows
- `reporting/bundles/staging.py` owns safe swap-in staging for generated publication trees
- `reporting/rendering/` owns generated README, HTML, and record-export helpers
- `reporting/shared/` owns merge and text helpers reused across reporting workflows
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

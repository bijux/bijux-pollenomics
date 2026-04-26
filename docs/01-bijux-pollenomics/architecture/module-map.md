---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Module Map

`bijux-pollenomics` is organized by workflow responsibility rather than by
framework layer. The structural question is simple: which module family owns
command entry, which owns tracked data shaping, and which owns published output
assembly.

## Module Model

```mermaid
flowchart TB
    entry["cli and command_line/"]
    core["core/ and config.py"]
    collect["data_downloader/"]
    report["reporting/"]
    outputs["tracked data and report outputs"]

    entry --> collect
    entry --> report
    core --> collect
    core --> report
    collect --> outputs
    report --> outputs
```

This page should show module families by the work they own, not by directory
labels alone. Readers need to see which family shapes tracked data, which one
assembles publication, and where shared helpers stop.

## Owned Module Families

- `cli.py` and `__main__.py` provide the public command entrypoint
- `command_line/parsing/` defines parser structure and option wiring
- `command_line/runtime/` resolves handlers and command dispatch
- `core/` carries low-level helpers for files, time labels, text, HTTP, and
  GeoJSON handling
- `data_downloader/` owns source collection, staging, contracts, and spatial
  helpers
- `reporting/` owns AADR reporting, context layers, bundle assembly, and map
  rendering

## First Proof Check

- `src/bijux_pollenomics/command_line/parsing/` and
  `src/bijux_pollenomics/command_line/runtime/`
- `src/bijux_pollenomics/data_downloader/pipeline/`,
  `data_downloader/sources/`, and `data_downloader/spatial/`
- `src/bijux_pollenomics/reporting/bundles/`,
  `reporting/rendering/`, `reporting/context/`, and
  `reporting/map_document/`
- `tests/unit/`, `tests/regression/`, and `tests/e2e/`

## Design Pressure

The common failure is to read the package as one big utility tree, which hides
the distinct responsibilities the handbook keeps trying to separate.

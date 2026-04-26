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
framework layer.

```mermaid
flowchart LR
    cli["cli and __main__"]
    parsing["command_line/parsing"]
    dispatch["command_line/runtime"]
    core["core helpers"]
    data["data_downloader"]
    reporting["reporting"]
    tests["tests"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class cli,page parsing;
    class dispatch,core,data,reporting,tests positive;
    cli --> parsing --> dispatch
    dispatch --> data
    dispatch --> reporting
    data --> core
    reporting --> core
    tests --> cli
    tests --> data
    tests --> reporting
```

## Main Runtime Areas

- `cli.py` and `__main__.py` provide the public command entrypoint
- `command_line/parsing/` defines parser structure and option wiring
- `command_line/runtime/` resolves handlers and command dispatch
- `core/` carries low-level helpers for files, time labels, text, HTTP, and
  GeoJSON handling
- `data_downloader/` owns source collection, staging, contracts, and spatial
  helpers
- `reporting/` owns AADR reporting, context layers, bundle assembly, and map
  rendering

## Cross-Cutting Anchors

- `config.py` centralizes stable defaults
- `tests/unit`, `tests/regression`, and `tests/e2e` mirror the runtime from
  fine-grained checks up to command behavior

## Reader Takeaway

The package is not split by web framework concerns or service tiers. It is
split by the work needed to parse commands, collect data, and publish checked-in
artifacts.

## Purpose

This page gives the shortest structural map of the runtime package.

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
framework layer. The main split is between command dispatch, data collection,
report publishing, and the shared helpers that keep file and text handling
consistent across both sides of the runtime.

```mermaid
flowchart LR
    cli["cli.py and __main__.py"]
    parsing["command_line/parsing"]
    dispatch["command_line/runtime"]
    data["data_downloader and pipeline"]
    reporting["reporting bundles and renderers"]
    core["core helpers and config defaults"]
    tests["unit, regression, and e2e tests"]
    reader["reader question<br/>where does this runtime behavior live?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class cli,page reader;
    class parsing,dispatch,data,reporting,core,tests positive;
    cli --> parsing --> dispatch
    dispatch --> data
    dispatch --> reporting
    data --> core
    reporting --> core
    tests --> cli
    tests --> data
    tests --> reporting
    parsing --> reader
    dispatch --> reader
    data --> reader
    reporting --> reader
    core --> reader
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

## How To Read The Package

- start at `cli.py` when the issue begins with a command invocation
- follow `command_line/runtime/dispatch.py` and `registry.py` when the question
  is which handler executes a parsed command
- move into `data_downloader/pipeline/` when the runtime is shaping tracked
  source outputs
- move into `reporting/bundles/`, `reporting/rendering/`, and
  `reporting/map_document/` when the runtime is shaping the published atlas or
  country bundles

## Stable Structural Anchors

- `config.py` keeps stable defaults such as `data/`, `docs/report/`, and the
  atlas defaults in one tracked place
- `data_downloader/data_layout.py` and `contracts.py` define the layout rules
  that collection code is expected to honor
- `reporting/bundles/paths.py` defines the stable path families for bundle
  outputs
- `tests/regression/test_repository_contracts.py` guards several repository and
  docs-level contracts that should not drift silently

## Cross-Cutting Anchors

- `config.py` centralizes stable defaults
- `tests/unit`, `tests/regression`, and `tests/e2e` mirror the runtime from
  fine-grained checks up to command behavior

## Open This Page When

- you know the behavior but not the module family that owns it
- a review comment names a path and you need the surrounding structure
- you need to explain why a change touches collection code, reporting code, or
  both

## Core Point

The package is not split by web framework concerns or service tiers. It is
split by the work needed to parse commands, collect source-backed data, and
publish checked-in artifacts. That workflow split is the shortest reliable way
to navigate the codebase.


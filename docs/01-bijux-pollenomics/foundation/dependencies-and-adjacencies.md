---
title: Dependencies and Adjacencies
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Dependencies and Adjacencies

`bijux-pollenomics` intentionally has a small code dependency surface and a
larger repository adjacency surface. The distinction matters because nearby
surfaces can look available for reuse even when they are not legitimate new
dependencies.

## Direct Dependencies

- the Python standard library across CLI, collection, and rendering paths
- `defusedxml` for safe XML handling in source-processing workflows

## Close Repository Adjacencies

- `apis/bijux-pollenomics/v1/` for frozen public API contracts
- `packages/bijux-pollenomics-dev/` for repository-owned checks around the
  runtime surface
- `makes/` for reproducible local and CI command entrypoints
- `docs/report/` and `data/` as the tracked file surfaces the package rewrites

## Adjacency Risk

The most tempting wrong move here is to treat `data/`, `docs/report/`, or
maintainer tooling as if they were just implementation detail. They are not.
They are adjacent repository-owned surfaces that the runtime coordinates with or
rewrites under visible contracts.

## First Proof Check

- `src/bijux_pollenomics/data_downloader/contracts.py`
- `src/bijux_pollenomics/reporting/bundles/paths.py`
- `apis/bijux-pollenomics/v1/`
- `packages/bijux-pollenomics-dev/`

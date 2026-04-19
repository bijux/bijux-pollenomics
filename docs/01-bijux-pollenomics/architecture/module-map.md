---
title: Module Map
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Module Map

`bijux-pollenomics` is organized by workflow responsibility rather than by
framework layer.

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

## Purpose

This page gives the shortest structural map of the runtime package.

---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Code Navigation

Use the following path when you need to trace behavior quickly.

## Start Points By Question

- command syntax or default flags: start in `cli.py` and
  `command_line/parsing/`
- command dispatch behavior: read `command_line/runtime/dispatch.py` and
  `handlers.py`
- source collection behavior: read `data_downloader/api.py`, `collector.py`,
  and `pipeline/`
- source-specific quirks: move into `data_downloader/sources/<source>/`
- report publishing behavior: read `reporting/service.py`, `reporting/api.py`,
  and `reporting/bundles/`
- rendered output shape: inspect `reporting/rendering/` and
  `reporting/map_document/`

## Test Navigation

- unit behavior: `tests/unit/`
- output regression checks: `tests/regression/`
- CLI behavior: `tests/e2e/test_cli.py`

## Purpose

This page gives maintainers a fast route into the runtime codebase.

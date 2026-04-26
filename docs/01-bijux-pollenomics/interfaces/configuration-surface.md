---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Configuration Surface

Configuration is centered on explicit defaults rather than on hidden discovery.
That makes default changes public interface changes, not quiet implementation
detail.

## Primary Defaults

- `DEFAULT_AADR_VERSION = "v66"`
- `DEFAULT_ATLAS_SLUG = "nordic-atlas"`
- `DEFAULT_ATLAS_TITLE = "Nordic Evidence Atlas"`
- `DEFAULT_PUBLISHED_COUNTRIES = ("Sweden", "Norway", "Finland", "Denmark")`
- default roots for `data/`, `data/aadr/`, and `docs/report/`

## Location

These defaults live in `packages/bijux-pollenomics/src/bijux_pollenomics/config.py`
and are reused by parser helpers under `command_line/parsing/options.py`.

## First Proof Check

- `packages/bijux-pollenomics/src/bijux_pollenomics/config.py`
- `src/bijux_pollenomics/command_line/parsing/options.py`
- `tests/unit/test_config.py`

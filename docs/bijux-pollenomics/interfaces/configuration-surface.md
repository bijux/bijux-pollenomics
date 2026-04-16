---
title: Configuration Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Configuration Surface

Configuration is centered on explicit defaults rather than on hidden discovery.

## Primary Defaults

- `DEFAULT_AADR_VERSION = "v66"`
- `DEFAULT_ATLAS_SLUG = "nordic-atlas"`
- `DEFAULT_ATLAS_TITLE = "Nordic Evidence Atlas"`
- `DEFAULT_PUBLISHED_COUNTRIES = ("Sweden", "Norway", "Finland", "Denmark")`
- default roots for `data/`, `data/aadr/`, and `docs/report/`

## Location

These defaults live in `packages/bijux-pollenomics/src/bijux_pollenomics/config.py`
and are reused by parser helpers under `command_line/parsing/options.py`.

## Review Rule

Changing a default is a public contract change because it can alter tracked
paths, published artifact names, and operator expectations.

## Purpose

This page records the stable default values that shape the runtime surface.

---
title: Configuration Defaults
audience: mixed
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Configuration Defaults

The repository keeps its shared publication defaults and path defaults in Python modules rather than in scattered string literals.

`packages/bijux-pollenomics/src/bijux_pollenomics/config.py` is the canonical source of truth for shared defaults. The CLI surface and `Makefile` derive their default AADR version from that module instead of carrying separate copies.

## Core Defaults

| Setting | Value | Source |
| --- | --- | --- |
| AADR version | `v62.0` | `packages/bijux-pollenomics/src/bijux_pollenomics/config.py` |
| Atlas slug | `nordic-atlas` | `packages/bijux-pollenomics/src/bijux_pollenomics/config.py` |
| Atlas title | `Nordic Evidence Atlas` | `packages/bijux-pollenomics/src/bijux_pollenomics/config.py` |
| Published countries | `Sweden`, `Norway`, `Finland`, `Denmark` | `packages/bijux-pollenomics/src/bijux_pollenomics/config.py` |
| Nordic bbox | `4.0, 54.0, 35.0, 72.0` | `packages/bijux-pollenomics/src/bijux_pollenomics/config.py` |

## Default Paths

| Path role | Value |
| --- | --- |
| data root | `data/` |
| AADR root | `data/aadr/` |
| report root | `docs/report/` |
| context root | `data/` |

## Why This Page Exists

These defaults influence collectors, reporting commands, and the published atlas. Recording them in one reference page makes it easier to review changes when one of those defaults moves.

The CLI parser and `Makefile` default surface both derive from these Python defaults rather than carrying separate hard-coded copies.

## Purpose

This page records the shared repository defaults that shape data collection and publication behavior.

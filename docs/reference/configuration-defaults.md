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

## Core Defaults

| Setting | Value | Source |
| --- | --- | --- |
| AADR version | `v62.0` | `src/bijux_pollenomics/project.py` |
| Atlas slug | `nordic-atlas` | `src/bijux_pollenomics/project.py` |
| Atlas title | `Nordic Evidence Atlas` | `src/bijux_pollenomics/project.py` |
| Published countries | `Sweden`, `Norway`, `Finland`, `Denmark` | `src/bijux_pollenomics/project.py` |
| Nordic bbox | `4.0, 54.0, 35.0, 72.0` | `src/bijux_pollenomics/project.py` |

## Default Paths

| Path role | Value |
| --- | --- |
| data root | `data/` |
| AADR root | `data/aadr/` |
| report root | `docs/report/` |
| context root | `data/` |

## Why This Page Exists

These defaults influence collectors, reporting commands, and the published atlas. Recording them in one reference page makes it easier to review changes when one of those defaults moves.

## Purpose

This page records the shared repository defaults that shape data collection and publication behavior.

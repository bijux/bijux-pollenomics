---
title: Data Categories
audience: mixed
type: explanation
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Data Categories

The project tracks five first-class source categories:

```text
data
├── aadr
├── boundaries
├── neotoma
├── raa
└── sead
```

## Why These Five

- `aadr` provides ancient DNA sample locations and metadata
- `boundaries` provides country polygons used to classify and filter records
- `neotoma` provides pollen and paleoecology site coverage
- `raa` provides Swedish archaeology context
- `sead` provides environmental archaeology context

## Collection Commands

The current command surface treats every tracked source the same way:

```bash
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data aadr --version v62.0 --output-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data boundaries --output-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data neotoma --output-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data sead --output-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data raa --output-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data all --version v62.0 --output-root data
```

## Shared Internal Shape

Every source directory uses one of two stable patterns:

- raw upstream payloads under `raw/`
- normalized map-ready or table-ready outputs under `normalized/`

`aadr` is the exception only in the sense that the tracked `.anno` files are already the durable input format needed by this repository.

## What Is Tracked Today

The current `data/` tree contains:

- tracked AADR `.anno` files under `data/aadr/v62.0/`
- raw and normalized country boundaries
- raw and normalized Neotoma pollen-site outputs
- raw and normalized SEAD site outputs
- raw RAÄ metadata plus normalized Swedish archaeology density outputs

## Why The Data Is Tracked In Git

The current repository keeps these source snapshots and normalized outputs in git so that:

- report and map changes can be reviewed against the exact inputs that produced them
- a clean checkout can be rebuilt into the same data layout with the current command surface
- documentation claims about file layout can be verified against the checked-in tree

## Why Not One Mixed Bucket

A single mixed data bucket would make it harder to:

- reason about source provenance
- update one source without touching unrelated data
- align the Python downloader package with the filesystem
- review changes by source in git history

## Purpose

This page explains the top-level organization rule that the rest of the repository now follows.

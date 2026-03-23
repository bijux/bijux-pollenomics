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

## Shared Internal Shape

Every source directory uses one of two stable patterns:

- raw upstream payloads under `raw/`
- normalized map-ready or table-ready outputs under `normalized/`

`aadr` is the exception only in the sense that the tracked `.anno` files are already the durable input format needed by this repository.

## Why Not One Mixed Bucket

A single mixed data bucket would make it harder to:

- reason about source provenance
- update one source without touching unrelated data
- align the Python downloader package with the filesystem
- review changes by source in git history

## Purpose

This page explains the top-level organization rule that the rest of the repository now follows.

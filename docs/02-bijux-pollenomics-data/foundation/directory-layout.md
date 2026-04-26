---
title: Directory Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Directory Layout

The tracked data layout is intentionally source-first.

## Top-Level Data Directories

- `data/aadr/`
- `data/boundaries/`
- `data/landclim/`
- `data/neotoma/`
- `data/raa/`
- `data/sead/`

## Layout Rule

Each source subtree is understandable without reading every neighboring
source. Raw and normalized outputs belong with the source that produced them,
while shared publication artifacts belong under `docs/report/`.

## Purpose

This page shows the directory shape readers should expect in the tracked data
tree.

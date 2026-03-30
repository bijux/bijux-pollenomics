---
title: Neotoma
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Neotoma

`data/neotoma/` contains Nordic pollen and paleoecology site data normalized from the Neotoma API.

## What It Produces

- a raw API snapshot under `data/neotoma/raw/neotoma_pollen_sites.json`
- normalized CSV and GeoJSON outputs under `data/neotoma/normalized/`

## What The Current Collector Does

The current collector:

- requests Neotoma `datasettype=pollen` rows from both the public `datasets` and `sites` endpoints
- merges those responses by site and collection unit so newer pollen records from `datasets` are not lost and site-only rows from `sites` are still retained
- keeps only rows whose representative point falls inside the Nordic bounding box
- assigns each retained record to a Nordic country using the tracked boundary layer, including a narrow boundary-proximity recovery so coastal and inland-water sites are not dropped by coarse land polygons
- writes one raw JSON snapshot plus normalized CSV and GeoJSON outputs

## Why It Matters

Neotoma is the pollen-oriented source currently integrated into this repository. It adds point-based pollen and paleoecology context to the same country-aware map used for AADR and SEAD.

## Acquisition Command

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollenomics.cli collect-data neotoma --output-root data
```

## Normalization Rule

The repository reduces Neotoma geometries to representative points for map use, then assigns those points to Nordic countries using the tracked boundary layer.

## What This Repository Intentionally Does Not Preserve

- richer upstream geometry distinctions beyond the representative point used for map placement
- every field that may exist in the upstream payload but is not needed by the current map and normalized exports
- non-Nordic records returned by the upstream API queries

That simplification is intentional. It makes the shared map tractable, but it also means the normalized Neotoma outputs are not a full mirror of the source system.

## Purpose

This page explains how Neotoma enters the repository and why it is part of the shared Nordic evidence surface.

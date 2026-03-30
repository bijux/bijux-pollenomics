---
title: Neotoma
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-30
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
- assigns each retained record to a Nordic country using the tracked boundary layer
- writes one raw JSON snapshot plus normalized CSV and GeoJSON outputs

## Why It Matters

Neotoma is the pollen-oriented source currently integrated into this repository. It adds point-based pollen and paleoecology context to the same country-aware map used for AADR and SEAD.

## Acquisition Command

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollenomics.cli collect-data neotoma --output-root data
```

## Normalization Rule

The repository reduces Neotoma geometries to representative points for map use, then assigns those points to Nordic countries using the tracked boundary layer.

## Purpose

This page explains how Neotoma enters the repository and why it is part of the shared Nordic evidence surface.

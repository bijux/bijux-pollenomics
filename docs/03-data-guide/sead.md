---
title: SEAD
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# SEAD

`data/sead/` contains normalized Nordic environmental archaeology site data from SEAD.

## What It Produces

- a raw site snapshot under `data/sead/raw/nordic_sites.json`
- normalized CSV and GeoJSON outputs under `data/sead/normalized/`

## What The Current Collector Does

The current collector:

- queries the SEAD PostgREST `tbl_sites` surface inside the Nordic bounding box
- drops rows without coordinates
- follows linked SEAD tables to attach sample-group, physical-sample, analysis-entity, dataset, reference, relative-date, and dating-range counts
- derives filterable BP coverage from linked dating ranges when SEAD exposes BP age types
- assigns each retained point to a Nordic country using the tracked boundary layer
- writes one raw JSON snapshot plus normalized CSV and GeoJSON outputs

## Why It Matters

SEAD adds environmental archaeology context to the same spatial frame used for pollen and AADR points, which makes it useful for later overlap and interpretation work.

## Acquisition Command

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollenomics.cli collect-data sead --output-root data
```

## Product Role

SEAD is especially useful for:

- checking where environmental archaeology evidence clusters
- comparing those clusters to aDNA and pollen locations
- expanding context beyond purely genetic or pollen-specific layers

## Purpose

This page explains why SEAD is a distinct tracked category and how it contributes to the evidence surface.

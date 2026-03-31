---
title: LandClim
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# LandClim

`data/landclim/` contains Nordic pollen-sequence metadata and REVEALS grid coverage normalized from three LandClim-related PANGAEA datasets.

## What It Produces

- raw upstream workbook, CSV, and ZIP snapshots under `data/landclim/raw/`
- normalized pollen-site CSV and GeoJSON outputs under `data/landclim/normalized/`
- a normalized REVEALS grid-cell GeoJSON layer under `data/landclim/normalized/nordic_reveals_grid_cells.geojson`
- a machine-readable source summary under `data/landclim/normalized/landclim_summary.json`

## What The Current Collector Does

The current collector:

- downloads the PANGAEA assets behind `10.1594/PANGAEA.900966`, `10.1594/PANGAEA.897303`, and `10.1594/PANGAEA.937075`
- resolves those assets from the official PANGAEA landing and textfile records instead of fixed direct-download guesses
- parses workbook-based metadata locally so the repository does not depend on external spreadsheet tooling
- reads LandClim I site metadata from both published workbook variants instead of trusting a single sheet name
- keeps pollen-sequence records whose coordinates fall inside the Nordic bounding box
- assigns retained sequences and grid cells to Nordic countries using the tracked boundary layer, then falls back to the workbook country field when the coordinate is valid but the boundary geometry is too coarse
- merges identical 1 degree grid cells across LandClim I and LandClim II outputs while preserving dataset labels, time-window coverage, and LandClim II quality labels
- validates that the LandClim II results archive contains the documented 25 mean and 25 standard-error CSV windows before normalization

## Why It Matters

LandClim adds a source that is broader than point-only pollen catalogs. It contributes both site-level pollen sequences and published REVEALS reconstruction coverage, which makes the shared map more explicit about where processed vegetation reconstruction products already exist.

## Acquisition Command

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollenomics.cli collect-data landclim --output-root data
```

## Normalization Rule

The upstream LandClim records mix raw pollen-sequence inputs with processed REVEALS products and, in some cases, 1 degree aggregated land-cover reconstructions. The repository keeps that distinction visible by publishing separate point and grid layers instead of flattening everything into one generic pollen table.

The normalized LandClim tree is still a Nordic subset. Coordinate-bearing rows outside the Nordic working extent are intentionally excluded even though they remain present in the raw tracked workbooks.

## Interpretation Caution

LandClim is useful precisely because it is mixed. That also means readers have to stay honest about what they are looking at:

- a pollen-sequence point is not the same kind of evidence as a REVEALS grid cell
- a processed regional reconstruction should not be described as if it were a raw site observation
- presence in the normalized LandClim tree does not imply that every source row is comparable to Neotoma or SEAD records on a one-to-one basis

## Purpose

This page explains how LandClim enters the repository and why it is tracked separately from Neotoma and SEAD.

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

- a dataset inventory audit artifact under `data/neotoma/raw/neotoma_pollen_dataset_inventory.json`
- a chunked full-download archive under `data/neotoma/raw/neotoma_pollen_dataset_downloads/`
- an aggregated site summary under `data/neotoma/raw/neotoma_pollen_sites.json`
- normalized CSV and GeoJSON outputs under `data/neotoma/normalized/`

## Collector Contract

The collector:

- requests a short Neotoma `datasettype=pollen` inventory from the public `datasets` endpoint using a Nordic `loc` query
- filters that inventory to tracked Nordic countries using the repository boundary layer
- preserves both the full bbox inventory and the retained Nordic subset so boundary filtering remains auditable
- downloads each surviving dataset through the full `downloads/{datasetid}` endpoint so samples, taxa, and chronologies are preserved
- retries transient Neotoma HTTP failures such as `429` and `5xx` responses during both inventory and dataset-download requests
- validates that every requested dataset ID is present in the collected download payloads before continuing
- merges the full dataset records by site and collection unit
- assigns each retained record to a Nordic country using the tracked boundary layer, including a narrow boundary-proximity recovery so coastal and inland-water sites are not dropped by coarse land polygons
- writes raw inventory, a chunked raw dataset-download archive, and a raw site-summary JSON artifact plus normalized CSV and GeoJSON outputs

## Why It Matters

Neotoma is the pollen-oriented source currently integrated into this repository. It adds point-based pollen and paleoecology context to the same country-aware map used for AADR and SEAD.

## Acquisition Command

```bash
artifacts/.venv/bin/bijux-pollenomics collect-data neotoma --output-root data
```

## Normalization Rule

The repository reduces Neotoma geometries to representative points for map use, then assigns those points to Nordic countries using the tracked boundary layer.

## What This Repository Intentionally Does Not Preserve In The Normalized Layer

- richer upstream geometry distinctions beyond the representative point used for map placement
- one point per individual sample or taxon observation
- non-Nordic records returned by the upstream API queries

The normalized outputs are intentionally compact for map use. The raw Neotoma artifacts now retain the full dataset downloads used to build those point summaries.

## Audit Artifacts

- a bbox inventory snapshot
- a filtered Nordic inventory snapshot
- full dataset download payloads for retained dataset IDs split across numbered part files with one manifest
- an aggregated site summary that explains how the normalized points were derived

## Purpose

This page explains how Neotoma enters the repository and why it is part of the shared Nordic evidence surface.

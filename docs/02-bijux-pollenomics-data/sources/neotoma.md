---
title: Neotoma
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Neotoma

Neotoma supplies paleoecological pollen-site context to the Nordic workspace.

## Neotoma Source Model

```mermaid
flowchart TB
    source["Neotoma source records"]
    sites["pollen-site context"]
    normalized["normalized Neotoma outputs"]
    atlas["atlas pollen context layers"]

    source --> sites
    sites --> normalized
    normalized --> atlas
```

Neotoma is a second major pollen-context family in the repository. Keeping it
visible as its own source helps readers compare pollen coverage without turning
all pollen context into one interchangeable backdrop.

## What This Source Adds

- point-based paleoecological context under `data/neotoma/`
- an independent pollen-family layer that complements LandClim
- source-specific provenance that remains visible even after normalization

## Boundary

Neotoma helps readers compare site distributions and contextual layers. It does
not collapse into one generic pollen source, and it does not answer ancient DNA
questions by itself.

## Downstream Outputs

- `data/neotoma/normalized/nordic_pollen_sites.csv`
- `data/neotoma/normalized/nordic_pollen_sites.geojson`
- shared atlas layers under `docs/report/nordic-atlas/`

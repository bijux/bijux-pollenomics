---
title: Source Comparison
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Source Comparison

The project tracks six first-class source categories:

```text
data
├── aadr
├── boundaries
├── landclim
├── neotoma
├── raa
└── sead
```

## Why These Six

- `aadr` provides ancient DNA sample locations and metadata
- `boundaries` provides country polygons used to classify and filter records
- `landclim` provides curated pollen-sequence inputs plus REVEALS reconstruction grid coverage from PANGAEA
- `neotoma` provides pollen and paleoecology site coverage
- `raa` provides Swedish archaeology context
- `sead` provides environmental archaeology context

## Comparison Matrix

| Source | Primary geometry in this repository | Geographic scope in checked-in outputs | Main use in outputs | Important limit |
| --- | --- | --- | --- | --- |
| `aadr` | points | Sweden, Norway, Finland, Denmark in the checked-in shared outputs | primary evidence layer for sample metadata | uses `.anno` metadata only, not genotype matrices |
| `boundaries` | polygons | Nordic country boundaries | country assignment and filtering | used as a support layer, not a research source on its own |
| `landclim` | points and 1 degree grid cells | Nordic subset of three PANGAEA datasets | pollen-sequence and REVEALS context | mixes raw pollen sequences with processed REVEALS products |
| `neotoma` | points | Nordic subset of Neotoma pollen datasets | pollen and paleoecology point context | normalized to representative points rather than richer source geometries |
| `raa` | density polygons plus metadata JSON | Sweden only | national archaeology context | does not expose every Swedish record as a point layer in the shared map |
| `sead` | points | Nordic subset of SEAD sites | environmental archaeology point context | site coverage depends on upstream SEAD metadata responses |

## Collection Commands

The command surface treats every tracked source the same way:

```bash
artifacts/.venv/bin/bijux-pollenomics collect-data aadr --version v62.0 --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data boundaries --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data landclim --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data neotoma --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data sead --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data raa --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data all --version v62.0 --output-root data
```

## Shared Internal Shape

Every source directory uses one of two stable patterns:

- raw upstream payloads under `raw/`
- normalized map-ready or table-ready outputs under `normalized/`

`aadr` is the exception only in the sense that the tracked `.anno` files are already the durable input format needed by this repository.

## What Is Tracked In Git

The checked-in `data/` tree contains:

- tracked AADR `.anno` files under `data/aadr/v62.0/`
- raw and normalized country boundaries
- raw and normalized LandClim pollen-sequence and REVEALS grid outputs
- raw Neotoma inventory and dataset-download snapshots plus normalized pollen-site outputs
- raw and normalized SEAD site outputs
- raw RAÄ metadata plus normalized Swedish archaeology density outputs

## Comparison Rule

Do not flatten these sources into one mental model.

- some are points and some are polygons
- some are raw observational inputs and some are already summarized products
- some are Nordic-wide in checked-in outputs and some are country-specific
- some support filtering and classification rather than acting as evidence layers themselves

## Why The Data Is Tracked In Git

The repository keeps these source snapshots and normalized outputs in git so that:

- report and map changes can be reviewed against the exact inputs that produced them
- a clean checkout can be rebuilt into the same tracked top-level layout with the checked-in command surface
- documentation claims about file layout can be verified against the checked-in tree

## Why Not One Mixed Bucket

A single mixed data bucket would make it harder to:

- reason about source provenance
- update one source without touching unrelated data
- align the Python downloader package with the filesystem
- review changes by source in git history

## Purpose

This page explains the top-level organization rule that the rest of the repository follows.

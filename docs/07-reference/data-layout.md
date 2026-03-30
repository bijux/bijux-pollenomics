---
title: Data Layout
audience: mixed
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Data Layout

## Top-Level Tree

```text
data
├── collection_summary.json
├── aadr
├── boundaries
├── landclim
├── neotoma
├── raa
└── sead
```

## Current Checked-In Files

```text
data
├── collection_summary.json
├── aadr
│   └── v62.0
│       ├── 1240k
│       │   └── v62.0_1240k_public.anno
│       └── ho
│           └── v62.0_HO_public.anno
├── boundaries
│   ├── normalized
│   │   └── nordic_country_boundaries.geojson
│   └── raw
│       ├── denmark.geojson
│       ├── finland.geojson
│       ├── norway.geojson
│       └── sweden.geojson
├── landclim
│   ├── normalized
│   │   ├── landclim_summary.json
│   │   ├── nordic_pollen_site_sequences.csv
│   │   ├── nordic_pollen_site_sequences.geojson
│   │   └── nordic_reveals_grid_cells.geojson
│   └── raw
│       ├── landclim_i_land_cover_types.xlsx
│       ├── landclim_i_plant_functional_types.xlsx
│       ├── landclim_ii_grid_cell_quality.xlsx
│       ├── landclim_ii_reveals_results.zip
│       ├── landclim_ii_site_metadata.xlsx
│       ├── landclim_ii_taxa_pft_ppe_fsp_values.csv
│       ├── landclim_sources.json
│       └── marquer_2017_reveals_taxa_grid_cells.xlsx
├── neotoma
│   ├── normalized
│   │   ├── nordic_pollen_sites.csv
│   │   └── nordic_pollen_sites.geojson
│   └── raw
│       └── neotoma_pollen_sites.json
├── raa
│   ├── normalized
│   │   ├── sweden_archaeology_density.geojson
│   │   └── sweden_archaeology_layer.json
│   └── raw
│       ├── arkreg_v1_0_wfs_capabilities.xml
│       ├── fornsok_domains.json
│       └── publicerade_lamningar_centrumpunkt_schema.xml
└── sead
    ├── normalized
    │   ├── nordic_environmental_sites.csv
    │   └── nordic_environmental_sites.geojson
    └── raw
        └── nordic_sites.json
```

## Internal Patterns

- `collection_summary.json`
- `aadr/<version>/<dataset>/...`
- `<source>/raw/...`
- `<source>/normalized/...`

## Contract Notes

- `aadr` is versioned because the checked-in `.anno` inputs are tied to a specific public release directory
- the other source directories are not versioned in the path; their current snapshot is represented by the checked-in raw and normalized files in place
- `collection_summary.json` is part of the contract, not an optional side artifact
- source collectors replace their own output directories before writing new files, so this tree should not accumulate stale files from earlier collector behavior

## Purpose

This page records the intended `data/` directory contract.

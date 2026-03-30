---
title: Data Layout
audience: mixed
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-23
---

# Data Layout

## Top-Level Tree

```text
data
├── collection_summary.json
├── aadr
├── boundaries
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

## Purpose

This page records the intended `data/` directory contract.

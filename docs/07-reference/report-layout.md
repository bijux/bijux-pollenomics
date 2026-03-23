---
title: Report Layout
audience: mixed
type: reference
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Report Layout

## Shared Map Bundle

```text
docs/report/nordic
├── _map_assets
├── README.md
├── nordic_aadr_v62.0_map.html
├── nordic_aadr_v62.0_summary.json
├── nordic_aadr_v62.0_samples.geojson
├── nordic_country_boundaries.geojson
├── nordic_environmental_sites.geojson
├── nordic_pollen_sites.geojson
├── sweden_archaeology_density.geojson
└── sweden_archaeology_layer.json
```

The checked-in Nordic bundle is currently the only shared HTML map bundle in the repository.

## Country Bundle Pattern

```text
docs/report/<country>
├── README.md
├── <country>_aadr_<version>_summary.json
├── <country>_aadr_<version>_samples.csv
├── <country>_aadr_<version>_localities.csv
├── <country>_aadr_<version>_samples.geojson
└── <country>_aadr_<version>_samples.md
```

## Current Checked-In Country Bundles

- `docs/report/published_reports_summary.json`
- `docs/report/sweden/`
- `docs/report/norway/`
- `docs/report/finland/`
- `docs/report/denmark/`

## Purpose

This page records the expected output shape for generated report artifacts.

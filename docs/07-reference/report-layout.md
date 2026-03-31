---
title: Report Layout
audience: mixed
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Report Layout

## Shared Map Bundle

```text
docs/report/nordic-evidence-atlas
├── _map_assets
├── README.md
├── nordic-evidence-atlas_v62.0_map.html
├── nordic-evidence-atlas_v62.0_summary.json
├── nordic-evidence-atlas_v62.0_samples.geojson
├── nordic_country_boundaries.geojson
├── nordic_environmental_sites.geojson
├── nordic_pollen_site_sequences.geojson
├── nordic_pollen_sites.geojson
├── nordic_reveals_grid_cells.geojson
├── sweden_archaeology_density.geojson
└── sweden_archaeology_layer.json
```

The checked-in Nordic atlas bundle is currently the only shared HTML map bundle in the repository.

`_map_assets/` is part of the published bundle contract even though its individual vendored files are not expanded in the tree above.

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

## Contract Notes

- the Nordic Evidence Atlas bundle is a generated publication tree, not hand-written documentation
- country bundles intentionally do not contain their own standalone HTML maps
- the shared bundle carries local Leaflet assets but still depends on external basemap tile services at runtime
- country and atlas summary JSON files now include explicit `artifacts` inventories so downstream tooling can rely on bundle contents without reimplementing filename conventions
- generated report-bundle filenames are defined in `src/bijux_pollenomics/reporting/paths.py`
- report publishing rewrites these artifacts in place, so reference expectations should stay aligned with the checked-in tree rather than older bundle shapes

## Purpose

This page records the expected output shape for generated report artifacts.

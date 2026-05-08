---
title: Nordic Atlas Inputs
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Nordic Atlas Inputs

The Nordic atlas is assembled from distinct input families. This page keeps
their source and refresh anchors visible so the map does not collapse into one
opaque surface.

## Reader Anchors

- [`docs/report/repository_atlas_input_audit.json`](../../report/repository_atlas_input_audit.json)
- [`docs/report/repository_atlas_input_audit.md`](../../report/repository_atlas_input_audit.md)
- [`docs/report/repository_cross_domain_evidence_matrix.md`](../../report/repository_cross_domain_evidence_matrix.md)
- [Nordic atlas outputs](nordic-atlas.md)

## Atlas Input Families

| Family | Source anchor | Normalized anchor | Published anchor |
| --- | --- | --- | --- |
| LandClim | `data/landclim/raw/landclim_sources.json` | `data/landclim/normalized/` | `docs/report/nordic-atlas/nordic_pollen_site_sequences.geojson` |
| Neotoma | `data/neotoma/raw/neotoma_pollen_dataset_inventory.json` | `data/neotoma/normalized/` | `docs/report/nordic-atlas/nordic_pollen_sites.geojson` |
| SEAD | `data/sead/raw/nordic_sites.json` | `data/sead/normalized/` | `docs/report/nordic-atlas/nordic_environmental_sites.geojson` |
| RAÄ | `data/raa/raw/` | `data/raa/normalized/` | `docs/report/nordic-atlas/sweden_archaeology_density.geojson` |
| Boundaries | `data/boundaries/raw/` | `data/boundaries/normalized/` | `docs/report/nordic-atlas/nordic_country_boundaries.geojson` |
| Animal aDNA | `data/adna/governance/` | `data/adna/final/atlas/` | `docs/report/nordic-atlas/nordic-atlas_animal_atlas_evidence.json` |

## Boundary

The atlas is strongest when each layer keeps its own source and refresh path
visible. If those paths blur, readers will over-read the map and under-read the
tracked evidence that justifies it.

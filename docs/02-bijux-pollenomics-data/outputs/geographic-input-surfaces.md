---
title: Geographic Input Surfaces
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Geographic Input Surfaces

The geography publication tree is assembled from distinct input families. This
page keeps their source anchors, normalized anchors, and published anchors
visible so the maps do not collapse into one opaque surface.

## Reader Anchors

- [repository atlas input audit](../../report/repository_atlas_input_audit.md)
- [repository cross-domain evidence matrix](../../report/repository_cross_domain_evidence_matrix.md)
- [geographic evidence surfaces](geographic-evidence-surfaces.md)

## Geographic Input Families

| Family | Source anchor | Normalized anchor | Published anchor |
| --- | --- | --- | --- |
| LandClim | `data/landclim/raw/landclim_sources.json` | `data/landclim/normalized/` | `docs/report/regions/nordic/nordic_pollen_site_sequences.geojson` |
| Neotoma | `data/neotoma/raw/neotoma_pollen_dataset_inventory.json` | `data/neotoma/normalized/` | `docs/report/regions/nordic/nordic_pollen_sites.geojson` |
| SEAD | `data/sead/raw/nordic_sites.json` | `data/sead/normalized/` | `docs/report/regions/nordic/nordic_environmental_sites.geojson` |
| RAÄ | `data/raa/raw/` | `data/raa/normalized/` | `docs/report/regions/nordic/sweden_archaeology_density.geojson` |
| Boundaries | `data/boundaries/raw/` | `data/boundaries/normalized/` | `docs/report/regions/nordic/nordic_country_boundaries.geojson` |
| Animal aDNA | `data/adna/governance/` | `data/adna/final/atlas/` | `docs/report/world/world_animal_atlas_evidence.json` |

## Boundary

The geographic publication tree is strongest when each layer keeps its own
source and refresh path visible. If those paths blur, readers will over-read
the map and under-read the tracked evidence that justifies it.

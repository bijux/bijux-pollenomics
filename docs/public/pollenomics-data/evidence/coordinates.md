---
title: Coordinates
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Coordinates

Coordinates are a provenance layer, not a substitute for locality evidence.
This page is where the repository shows whether a mapped point came from direct
coordinates, named-site geocoding, broader projection logic, or a decision not
to map the row at all.

## Direct Files

- `data/adna/species/ovis_aries/normalized/coordinate_provenance.json`
- `data/adna/governance/coordinate_caveat_surface.json`
- `data/adna/governance/cross_species_map_readiness.json`
- [`docs/report/animal_point_evidence_review.md`](../../../report/animal_point_evidence_review.md)
- `data/adna/species/ovis_aries/normalized/site_evidence.json`
- `data/adna/governance/unresolved_site_ledger.json`
- `data/adna/governance/overbroad_site_ledger.json`

## How Place Names Become Map Points

- direct coordinates can publish as direct points when the provenance row is complete
- named-site geocoding stays marked as weaker geography
- region-only or unresolved locality claims stay blocked from exact publication
- the atlas and country bundles should surface those weaker postures honestly

## Reader Rule

Coordinates only count as publishable evidence when the provenance row still
shows the basis, confidence, rationale, and sample linkage that produced the
visible point.

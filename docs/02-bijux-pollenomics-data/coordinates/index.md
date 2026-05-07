---
title: Coordinates
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Coordinates

Coordinates are a provenance layer, not a substitute for locality evidence.
This page is where the repository shows whether a mapped point came from direct
coordinates, named-site geocoding, broader projection logic, or a decision not
to map the row at all.

## Direct Files

- [`data/adna/species/ovis_aries/normalized/coordinate_provenance.json`](../../../data/adna/species/ovis_aries/normalized/coordinate_provenance.json)
- [`data/adna/governance/coordinate_caveat_surface.json`](../../../data/adna/governance/coordinate_caveat_surface.json)
- [`data/adna/governance/cross_species_map_readiness.json`](../../../data/adna/governance/cross_species_map_readiness.json)
- [`docs/report/animal_point_support_packets.md`](../../report/animal_point_support_packets.md)
- [How site names become coordinates](site-coordinate-resolution.md)

## Reader Rule

Coordinates only count as publishable evidence when the provenance row still
shows the basis, confidence, rationale, and sample linkage that produced the
visible point.

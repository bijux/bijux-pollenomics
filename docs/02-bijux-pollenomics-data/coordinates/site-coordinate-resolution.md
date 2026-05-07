---
title: How Site Names Become Coordinates
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# How Site Names Become Coordinates

The repository never treats a site name as a coordinate by magic. It first
checks whether the source already provides coordinates, then whether the sample
owns a defensible named site that can be geocoded, and then whether the result
must stay weaker than an exact point.

## Direct Files

- [`data/adna/species/ovis_aries/normalized/site_evidence.json`](../../../data/adna/species/ovis_aries/normalized/site_evidence.json)
- [`data/adna/species/ovis_aries/normalized/coordinate_provenance.json`](../../../data/adna/species/ovis_aries/normalized/coordinate_provenance.json)
- [`data/adna/governance/coordinate_caveat_surface.md`](../../../data/adna/governance/coordinate_caveat_surface.md)
- [`data/adna/governance/unresolved_site_ledger.json`](../../../data/adna/governance/unresolved_site_ledger.json)
- [`data/adna/governance/overbroad_site_ledger.json`](../../../data/adna/governance/overbroad_site_ledger.json)

## Publication Rule

- direct coordinates can publish as direct points when the provenance row is complete
- named-site geocoding stays marked as weaker geography
- region-only or unresolved locality claims stay blocked from exact publication
- the atlas and country bundles should surface those weaker postures honestly

This is why the database keeps both site evidence and coordinate provenance.
One explains what the place claim was, and the other explains how the map point
was or was not derived from it.

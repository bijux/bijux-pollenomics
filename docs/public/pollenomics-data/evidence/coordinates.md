---
title: Coordinates
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Coordinates

Coordinates are a provenance layer, not a substitute for locality evidence.
This page shows whether a mapped point came from direct coordinates, named-site
geocoding, broader projection logic, or a decision not to map the row at all.

That distinction matters because the map is often the first thing people see.
If the coordinate basis is unclear, the point can look more exact than the
evidence behind it really is.

## How Place Names Become Map Points

- direct coordinates can publish as direct points when the provenance row is
  complete
- named-site geocoding stays marked as weaker geography
- region-only or unresolved locality claims stay blocked from exact publication
- the atlas and country bundles should surface those weaker postures honestly

## What You Should Be Able To Tell

- whether a point is based on direct coordinates or on a narrower geocoding
  step
- whether the visible precision matches the supporting locality evidence
- whether a record stayed blocked because the repository refused to fake exact
  geography
- whether a public map point should be read as exact placement, cautious
  placement, or only broad regional context

## The Key Rule

Coordinates only count as publishable evidence when the provenance row still
shows the basis, confidence, rationale, and sample linkage that produced the
visible point.

## Why This Layer Protects The Public Product

Without coordinate provenance, a map point can silently become the strongest
thing in the repository even when it should not be. This layer prevents that by
keeping the public point tied to:

- the locality decision that made mapping possible
- the rationale for the coordinate itself
- the confidence and caveat posture that still belongs to the point

## Direct Files

- `data/adna/species/ovis_aries/normalized/coordinate_provenance.json`
- `data/adna/governance/coordinate_caveat_surface.json`
- `data/adna/governance/cross_species_map_readiness.json`
- [`docs/report/animal_point_evidence_review.md`](../../../report/animal_point_evidence_review.md)
- `data/adna/species/ovis_aries/normalized/site_evidence.json`
- `data/adna/governance/unresolved_site_ledger.json`
- `data/adna/governance/overbroad_site_ledger.json`

## Where To Go Next

- move to [localities](localities.md) if the coordinate question is really a
  place-claim question
- move to [sample records](sample-records.md) if the point may be attached to
  the wrong sample lineage
- move to [chronology](chronology.md) if the point is placed acceptably but the
  time claim still feels too strong

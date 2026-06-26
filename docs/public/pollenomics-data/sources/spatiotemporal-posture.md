---
title: Spatiotemporal Posture
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-06-22
---

# Spatiotemporal Posture

Not every checked-in source family is comparable in the same way through space
and time.

That is not a documentation problem. It is a real property of the tracked
evidence. Some source families contribute lake anchors, some contribute point
inventories, some contribute density context, and only some contribute numeric
BP windows that can support chronology-aware comparison.

The repository keeps that distinction explicit in the machine-readable
registry:

- `data/source_spatiotemporal_posture_registry.json`

## Why This Registry Exists

Without one shared posture surface, readers have to infer too much from file
names or map symbols alone.

This registry answers a narrower set of questions directly:

- is this family a lake anchor, a context point inventory, a density surface,
  or framing geometry?
- does the checked-in repository state carry numeric BP windows for this
  family?
- should this family affect chronology-aware ranking, broad context scoring,
  or only candidate-lake identity?

## What It Says Right Now

- LandClim carries numeric BP windows in the normalized site-sequence layer and
  acts as supporting pollen context.
- Neotoma carries uneven BP site-span support and must not be treated as if the
  checked-in raw capture already includes chronology rows for every site.
- SEAD remains contextual archaeology inventory in the checked-in state and
  should not be promoted into same-period support unless explicit numeric
  intervals are present.
- RAÄ is rich Swedish archaeology context, but the repository-owned normalized
  surface is density-oriented rather than one exact local-distance site
  inventory.
- SVAR governs candidate-lake identity and location, not chronology.
- Boundary geometry constrains scope and framing only.

## How To Use It

Use the registry before making or reading lake-ranking claims.

If a source family is marked as context only, do not inflate it into direct
same-period support. If a family is marked as a lake anchor only, do not count
it as environmental or archaeological evidence. If a family carries numeric
intervals unevenly, keep the unevenness visible instead of smoothing it away in
the report.

## Best Companion Pages

- [LandClim](landclim.md)
- [Neotoma](neotoma.md)
- [SEAD](sead.md)
- [Source family matrix](source-family-matrix.md)

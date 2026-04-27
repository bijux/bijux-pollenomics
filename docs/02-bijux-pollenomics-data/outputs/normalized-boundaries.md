---
title: Normalized Boundary Outputs
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Normalized Boundary Outputs

Boundary outputs live under `data/boundaries/normalized/`.

## Boundary Output Model

```mermaid
flowchart TB
    upstream["boundary source geometry"]
    normalized["normalized Nordic boundaries"]
    framing["country filtering and framing"]
    publication["reports and atlas views"]

    upstream --> normalized
    normalized --> framing
    framing --> publication
```

This page should show why boundary files matter even though they are not the
main scientific evidence. They define the spatial frame that keeps report and
atlas publication readable and reviewable.

## What This Output Family Carries

- stable country geometry used by reports and the atlas
- a shared spatial frame that stays separate from scientific source outputs
- one reusable filter surface for Nordic publication views

## Boundary

These files make map framing and country filtering reviewable. They do not add
scientific evidence by themselves, and they should not be read as equivalent to
ancient DNA, pollen, or archaeology layers.

## First Proof Check

- inspect `data/boundaries/normalized/nordic_country_boundaries.geojson`
- compare with [Boundaries](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/boundaries/)
  when the question is about upstream framing logic

## Design Pressure

The easy failure is to treat boundaries as neutral backdrop only, even though a
changed framing layer can silently alter how readers interpret every other
mapped surface.

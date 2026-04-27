---
title: Pollenomics Engine Roadmap
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-27
---

# Pollenomics Engine Roadmap

The current repository is an atlas-builder with reproducible evidence routing.
That is the right starting point, but it is not the end state. The end state is
a pollenomics runtime that can compare pollen, archaeological context, and
ancient DNA evidence without losing provenance or contract clarity.

## Current Stage

Today the repository can:

- collect tracked evidence from AADR metadata, LandClim, Neotoma, SEAD, RAÄ,
  and fieldwork records
- normalize those sources into reviewed files under `data/`
- publish country bundles and one shared Nordic atlas under `docs/report/`
- emit heuristic candidate-site ranking sidecars from the tracked atlas context
  layers

## Next Stage

The next stage is to turn heuristic publication outputs into explicit workflow
stages:

- candidate ranking should remain traceable to exact tracked context layers
- multi-evidence joins should state where provenance differs rather than
  flattening those differences into one score
- workflow outputs should be publishable and reviewable from the repository
  alone

## Paper Direction

The planned paper direction is:

`POLLENOMIC's: Decoding the farming history of Scandinavia using advanced statistics to combine ancient DNA with paleo-pollen data.`

That future work needs more than a map. It needs reproducible statistical
workflows, explicit evidence contracts, and a runtime that can relate pollen
signals to ancient-DNA context without pretending that proximity alone is
enough.

## Boundary

This roadmap should keep ambition honest. A page like this is useful only if it
prevents the repository from claiming that future engine work already exists in
the current atlas-builder surface.

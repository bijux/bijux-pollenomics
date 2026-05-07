---
title: Pollenomics Engine Roadmap
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Pollenomics Engine Roadmap

The current repository is a tracked evidence system with one shared atlas and
country bundles. That is a legitimate starting point, but it is not the end
state. The end state is a pollenomics runtime that can compare pollen,
archaeological context, and ancient DNA evidence without losing provenance or
claim discipline.

## Current Stage

Today the repository can:

- collect tracked evidence from AADR metadata, LandClim, Neotoma, SEAD, RAÄ,
  boundaries, and fieldwork records
- normalize those sources into reviewed files under `data/`
- publish country bundles and one shared Nordic atlas under `docs/report/`
- expose the current weakness of the animal aDNA recovery state instead of
  pretending that thin atlas output already proves broad coverage

## Next Stage

The next stage is to turn thin or uneven surfaces into explicit recovery work:

- source acquisition must widen, especially for missing supplementary material
- sample, site, chronology, and coordinate extraction must become defensible
- multi-evidence joins must state where provenance differs rather than
  flattening those differences into one score
- pollenomics-first explanation must stay broader than the current aDNA
  recovery slice

## Boundary

This roadmap is useful only while it prevents the repository from claiming that
future engine work already exists in the current publication surface.

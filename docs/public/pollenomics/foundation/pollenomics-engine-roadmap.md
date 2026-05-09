---
title: Pollenomics Engine Roadmap
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Pollenomics Engine Roadmap

The current repository is a real evidence system, but it is not the final
pollenomics engine. Today it can collect, normalize, and publish several
evidence families into one governed output tree. The longer-term ambition is
broader: compare pollen, archaeological context, and ancient-DNA evidence in a
way that keeps provenance visible and refuses overclaiming.

This page is here so readers do not confuse those two things. The current
system is legitimate. The larger engine is still ahead.

## Current Stage

Today the repository can:

- collect tracked evidence from AADR metadata, LandClim, Neotoma, SEAD, RAÄ,
  boundaries, and fieldwork records
- normalize those sources into reviewed files under `data/`
- publish one world-to-country geography tree under `docs/report/`
- expose the current weakness of the animal aDNA recovery state instead of
  pretending that thin atlas output already proves broad coverage

That is enough to produce useful, reviewable outputs. It is not enough to claim
that every evidence family is equally deep or equally mature.

## Next Stage

The next stage is to turn thin or uneven surfaces into explicit recovery work:

- source acquisition must widen, especially for missing supplementary material
- sample, site, chronology, and coordinate extraction must become defensible
- multi-evidence joins must state where provenance differs rather than
  flattening those differences into one score
- pollenomics-first explanation must stay broader than the current aDNA
  recovery slice
- world, Europe-plus, Nordic, and country publication must keep sharing one
  product model so future-country growth does not fragment the code or docs

In other words, the roadmap is not just "collect more files." It is about
making weaker parts of the system more defensible without breaking the parts
that are already reviewable.

## Current Refusal Boundary

The roadmap is ambitious, but the repository still refuses final release
language. Animal recovery depth and SEAD comparability remain materially weaker
than the stronger architecture, geography, and docs surfaces. The roadmap is
useful only if that refusal stays explicit while the weaker dimensions catch up.

## Boundary

This roadmap is useful only while it prevents the repository from claiming that
future engine work already exists in the current publication surface.

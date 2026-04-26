---
title: Shared Normalization
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Shared Normalization

The repository normalizes different source families into reviewable,
publication-ready shapes without pretending that the sources are the same.

## Shared Expectations

- each source keeps its own raw and normalized identity
- normalized files are shaped for atlas and report consumption
- country filtering and spatial interpretation stay consistent across layers
- provenance stays inspectable after normalization rather than being hidden
  behind one merged export

## Boundary

Shared normalization narrows format and review cost. It does not erase
source-specific caveats, and it does not make a contextual layer interchangeable
with ancient DNA metadata or direct fieldwork.

## First Proof Check

- compare one raw tree and one normalized tree under `data/*/`
- inspect the atlas bundle under `docs/report/nordic-atlas/` to see how those
  normalized files become a visible publication surface

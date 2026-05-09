---
title: SEAD
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# SEAD

SEAD supplies environmental archaeology context to the tracked data tree.
It is useful, but it is easy to over-read. A SEAD site row is not a pollen
sequence, not a sample-owned animal date, and not a clean uniform archaeology
fact just because it made it into a GeoJSON file.

## SEAD Source Model

```mermaid
flowchart TB
    source["SEAD source data"]
    context["environmental archaeology context"]
    normalized["normalized SEAD outputs"]
    atlas["atlas archaeology layers"]

    source --> context
    context --> normalized
    normalized --> atlas
```

SEAD belongs beside RAÄ, but it is not the same kind of archaeology source.
It provides broader environmental archaeology context with its own coverage and
limits.

The important correction is legibility, not cosmetic completeness. SEAD rows
are site-level archaeology context. Some rows carry numeric spans, some carry
relative period labels, some remain thin site inventory captures, and some
only expose stable access through the upstream SEAD site page. The repository
now keeps those distinctions visible through:

- `data/sead/review/temporal_review.json`
- `data/sead/review/access_model.json`
- `data/sead/review/evidence_legibility_review.json`
- `data/sead/review/recovery_roadmap.json`
- [SEAD Handbook](sead-handbook.md)

## What This Source Adds

- archaeological site context that complements pollen and ancient DNA layers
- point-based evidence that helps the atlas show wider environmental
  archaeology distribution
- a second archaeology family whose scope and interpretation differ from RAÄ
- governed period labels, duration ranges, and temporal uncertainty that remain
  visible through normalization

## Boundary

SEAD is contextual archaeology evidence, not a replacement for pollen layers,
not a direct field log, and not equivalent to the Sweden-only RAÄ surface. Its
meaning depends on being read beside the other normalized layers.

When SEAD publishes a numeric span, that span still belongs to a site-level
context surface. It is not automatically comparable to one sample-owned animal
date. See [Temporal Semantics](../evidence/temporal-semantics.md) for the
shared comparison rules.

## Downstream Outputs

- `data/sead/normalized/nordic_environmental_sites.csv`
- `data/sead/normalized/nordic_environmental_sites.geojson`
- `data/sead/review/temporal_review.json`
- atlas context layers under `docs/report/world/`
- one report-root legibility packet at
  [`docs/report/repository_sead_legibility_review.md`](../../report/repository_sead_legibility_review.md)

---
title: Normalized RAÄ Outputs
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Normalized RAÄ Outputs

RAÄ normalized outputs live under `data/raa/normalized/`.

## RAÄ Output Model

```mermaid
flowchart TB
    upstream["RAA archaeology source"]
    normalized["Sweden-scoped normalized outputs"]
    atlas["Swedish archaeology atlas layer"]
    reader["archaeology context question"]

    upstream --> normalized
    normalized --> atlas
    atlas --> reader
```

This page should make the geographic limit part of the page’s headline logic.
RAA is useful because it stays explicitly Sweden-scoped even when rendered next
to Nordic-wide layers.

## What This Output Family Carries

- Swedish archaeology density geometry
- Sweden-scoped contextual files that enrich the atlas without pretending to
  cover the full Nordic region
- one output family whose geographic limit is part of its meaning

## Boundary

These files are useful because they keep the Swedish scope explicit. They
should not be generalized into Nordic-wide archaeology coverage just because
they are rendered beside Nordic-wide layers.

## First Proof Check

- inspect `data/raa/normalized/`
- compare with [RAÄ](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/sources/raa/)
  when the question is about source scope rather than normalized outputs

## Design Pressure

The common failure is to let a visually strong Swedish layer imply Nordic-wide
coverage, which turns an honest scoped context surface into a misleading
regional claim.

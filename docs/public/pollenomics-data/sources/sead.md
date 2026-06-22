---
title: SEAD
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-06-22
---

# SEAD

SEAD is one of the repository's main archaeology-context families. It helps
readers ask a broader question than "where is the sample?" It helps ask, "what
kind of archaeological setting surrounds this evidence?"

That role matters because the public product is not only a collection of
points. It is also an interpretation surface. SEAD gives the repository a way
to place pollen and ancient DNA inside a wider environmental archaeology
context.

## What SEAD Adds

SEAD is strongest when readers need broader archaeological context that is not
limited to one national registry.

It is especially useful for:

- environmental archaeology context around sites and regions
- broader cross-regional comparison than a Sweden-only source can provide
- public interpretation that needs cultural setting as well as biological or
  environmental evidence

For Sweden-specific lake work, SEAD is one of the fastest ways to see whether a
promising pollen basin also sits inside a richer environmental-archaeology
landscape. That matters when the repository is comparing many possible lakes
and needs to distinguish "good pollen signal" from "good pollen signal plus
surrounding archaeological context."

## Temporal Posture In This Repository

The checked-in SEAD surfaces should be read as archaeology context with uneven
chronology capture, not as a uniformly time-expanded archaeological layer.

In the current repository state:

- the tracked Sweden-facing SEAD surface is primarily a site inventory
- the checked-in raw capture does not yet supply numeric BP intervals across
  the same inventory in a way that can be promoted wholesale into chronology
  support
- the lake-ranking workflow therefore uses SEAD chiefly for contextual density
  and only gives stronger chronology credit where numeric intervals are
  actually present

This is an honesty rule, not a downgrade. SEAD remains valuable, but the
repository does not collapse "archaeology nearby" into "archaeology from the
same period" unless the checked-in record state supports that claim.

The shared machine-readable posture for this family lives in:

- `data/source_spatiotemporal_posture_registry.json`

## What SEAD Does Not Do

SEAD is contextual support. It should not be read as direct proof of a single
sample's identity, locality, chronology, or coordinates.

It does not replace:

- aDNA recovery and review
- pollen-derived environmental context
- country and regional framing layers
- local Swedish detail from RAÄ where that source is richer

It also does not mean that every SEAD-linked context point is temporally
comparable with nearby pollen or ancient DNA. The repository keeps that limit
explicit instead of smoothing it away.

Its job is to deepen interpretation, not to erase the difference between
context and direct evidence.

## How It Differs From RAÄ

SEAD and RAÄ are both archaeology families, but they do not have the same
scope.

SEAD is the broader archaeology-context family. RAÄ is intentionally
Sweden-specific and often denser inside Swedish and Nordic reading.

That means SEAD is usually the better first source when the question is broad
archaeology context across places, while RAÄ is often the better first source
when the question is specifically about Swedish detail.

## Why SEAD Is A Real Collaboration Fit

SEAD is not only a dataset. It is also a Swedish environmental-archaeology
infrastructure with broader Nordic and European reach. That makes it a strong
fit when the repository needs to:

- improve archaeology context around Sweden lake candidates
- compare Swedish basins against wider Scandinavian and European context
- strengthen metadata, reference links, and temporal legibility around tracked
  archaeology records

That fit is why the repository treats SEAD as a durable source family rather
than as one more map decoration.

## How It Appears In Public Outputs

SEAD helps the atlas and country outputs avoid reading as if ancient DNA and
pollen were being interpreted in a cultural vacuum. It adds archaeology context
that can travel beyond one local system, while still remaining honest about its
contextual role.

In the Sweden lake evidence surfaces, SEAD does three narrower jobs:

- it counts surrounding archaeology-context records within explicit distance
  bands
- it helps distinguish lakes with similar pollen or aDNA support by the depth
  of their wider archaeology setting
- it strengthens chronology-aware comparisons only when checked-in numeric BP
  intervals are actually available

## If You Need The Repository-Owned Records

The family-owned normalized outputs live under:

- `data/sead/normalized/`
- `data/sead/review/temporal_review.json`
- `data/source_spatiotemporal_posture_registry.json`

The current public source and infrastructure entry points live at:

- `https://www.sead.se/`
- `https://browser.sead.se/`

If you want the deeper interpretation model behind this family, continue to the
[SEAD handbook](sead-handbook.md).

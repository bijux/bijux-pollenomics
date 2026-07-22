---
title: Fieldwork
audience: reader
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Fieldwork

Fieldwork records direct observation at a declared place and time. Within
Bijux Pollenomics, that is a distinct evidence role: it can establish that a
visit occurred and preserve what was documented, but it cannot replace pollen,
archaeology, hydrography, or ancient-DNA evidence.

## Evidence Role

```mermaid
flowchart LR
    Visit["dated visit"] --> Record["location and visit record"]
    Visit --> Media["repository-owned photo and video"]
    Record --> Point["fieldwork atlas feature"]
    Media --> Point
    Point --> Claim["inspectable visit claim"]
    Context["pollen, archaeology, aDNA, and lake context"] -. interpreted separately .-> Point
```

| Fieldwork can establish | Fieldwork cannot establish alone |
| --- | --- |
| a visit at the recorded date and location | representative coverage of a lake or region |
| repository ownership of the published media | sediment quality, bathymetry, or coring suitability |
| linkage between a visit record and an atlas feature | temporal overlap among nearby evidence families |
| what is visibly documented in the selected media | a general sampling recommendation |

## Current Record

The published fieldwork surface contains one direct visit record:
[Lyngsjön Lake, 26 February 2026](./lyngsjon-lake-fieldwork/index.md). The
record includes coordinates, atlas identity, a checked-in photograph, and a
checked-in video.

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="./lyngsjon-lake-fieldwork/">Inspect the Lyngsjön visit</a>
  <a class="md-button" href="../../report/regions/nordic/nordic_map.html">Open the Nordic atlas</a>
  <a class="md-button" href="../nordic-atlas/sweden-lake-priorities/">Review Sweden lake priorities</a>
  <a class="md-button" href="../pollenomics-data/">Follow the data evidence chain</a>
</div>

## Relationship To Lake Prioritization

A documented visit and a ranked lake answer different questions. Ranking
combines declared evidence and lake attributes to support prioritization. A
visit records direct presence and media at one location. Neither supplies the
missing bathymetry, permits, access analysis, sediment assessment, or complete
field protocol required for sampling readiness.

The fieldwork feature therefore remains its own atlas layer. It can be compared
with nearby context, but proximity does not transfer evidentiary weight between
layers.

## Publication Boundary

The current record does not imply that every atlas point has field media or
that Lyngsjön represents regional conditions. Additional visits require their
own date, location, media lineage, feature identity, and claim boundary before
publication.

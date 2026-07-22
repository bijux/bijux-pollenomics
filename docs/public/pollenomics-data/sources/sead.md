---
title: SEAD
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# SEAD

SEAD supplies environmental-archaeology context. In the current checked-in
state it is a spatial site inventory, not a uniformly time-resolved
archaeology layer. Its value is substantial precisely when that contextual
role and temporal limit remain explicit.

## Checked-In Evidence

The current temporal and legibility reviews cover 2,195 captured site rows:

| Property | Count | Posture |
| --- | ---: | --- |
| site inventory rows | 2,195 | spatial archaeology context |
| numeric temporal intervals | 0 | no numeric same-period comparison |
| linked dating-range rows | 0 | dating foundation not captured here |
| linked relative-period rows | 0 | period foundation not captured here |
| bibliography rows | 0 | bibliography linkage not captured here |

The normalized spatial layer contains 2,172 records. The difference between
captured and normalized counts must remain visible; it is not evidence that
the omitted records never existed.

Every current legibility-review row is classified as inventory-only or
unresolved for time, with high risk from the thin site-inventory capture and a
publication posture of context with an explicit caveat.

```mermaid
flowchart LR
    Capture["captured site inventory"] --> Normalize["normalized site points"]
    Normalize --> Temporal["temporal review"]
    Normalize --> Legibility["evidence legibility review"]
    Temporal --> Context["context-only publication posture"]
    Legibility --> Context
    Context --> Product["archaeology context layer"]
```

## What SEAD Supports

- environmental-archaeology context around samples, pollen records, lakes,
  and regions;
- spatial density and proximity comparisons under declared distance bands;
- cross-regional context beyond one national registry;
- identification of places where deeper source recovery may be valuable;
- landscape interpretation that keeps archaeology visible beside biological
  and environmental evidence.

## What The Current Capture Does Not Support

- same-period claims between SEAD sites and nearby pollen or aDNA;
- exact sample identity, locality, chronology, or species assignment;
- duration or phase comparison across the captured inventory;
- bibliography-backed interpretation for every normalized site;
- treating site density as a direct measure of past activity or preservation.

The absence of numeric intervals is not repaired with inferred dates. SEAD can
affect spatial decision support while receiving no chronology credit.

## Relationship To RAÄ

SEAD provides wider environmental-archaeology context. RAÄ provides denser
Sweden-specific registry context. Their records may overlap spatially, but the
families have different coverage, source systems, and normalization semantics.
They should be compared as complementary context rather than merged into a
single archaeology truth set.

## Governing Surfaces

- `data/sead/raw/nordic_sites.json` records the captured inventory;
- `data/sead/normalized/nordic_environmental_sites.geojson` governs normalized
  points;
- `data/sead/review/access_model.json` records access posture;
- `data/sead/review/evidence_legibility_review.json` records interpretability;
- `data/sead/review/temporal_review.json` records temporal refusal;
- `data/sead/review/recovery_roadmap.json` records recovery direction.

The [SEAD handbook](sead-handbook.md) expands the interpretation and
collaboration context without changing these evidence limits.

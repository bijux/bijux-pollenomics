---
title: Fieldwork
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Fieldwork

Fieldwork is the checked-in evidence layer for real sampling visits.

Use this section when a map point or normalized source record must be grounded
in direct on-site collection context.

This section is intentionally narrow. It does not try to replace the atlas, the
data reference, or a full field-log system. Its job is to preserve the direct
human record behind a documented visit: where the team went, when sampling
happened, and which media artifacts support that record.

```mermaid
flowchart LR
    visit["field visit"]
    record["fieldwork page<br/>date, place, purpose, media"]
    atlas["atlas point<br/>visible publication layer"]
    data["data reference<br/>source-derived context"]
    boundary["interpretation boundary<br/>one visit is not a full evidence system"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class visit,page record;
    class atlas,data positive;
    class boundary caution;
    visit --> record --> atlas
    record --> data
    record --> boundary
```

The [Nordic Evidence Atlas](../report/nordic-atlas/nordic-atlas_map.html)
remains the main decision surface for comparing mapped evidence layers. This
row exists so readers can follow one visible atlas point back to a real visit
instead of treating every layer as equally abstract.

## Pages In This Section

- [Lyngsjön Lake Fieldwork](lyngsjon-lake-fieldwork/index.md)

## Use This Section For

- confirming that a mapped fieldwork point refers to a documented visit
- checking the exact date, location, and media attached to that visit
- distinguishing direct field evidence from source-derived atlas layers

## Do Not Use This Section For

- inferring that every atlas point has matching field documentation
- treating one visit as proof of regional sampling completeness
- replacing the data reference when the real question is provenance or
  normalization

## Purpose

This page gives field documentation a durable root docs row and keeps future
sampling planning visibly connected to the atlas.

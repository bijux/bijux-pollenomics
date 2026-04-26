---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Architecture Risks

The package architecture is intentionally simple, but simplicity only helps if
the main failure modes stay visible.

```mermaid
flowchart TD
    outputs["large tracked file diffs"]
    source["source-specific special cases"]
    boundary["collection and reporting boundary drift"]
    docs["docs lag behind contracts"]
    rename["output path or slug renames"]
    risk["architecture review risk"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class risk,page outputs;
    class source,boundary,docs,rename caution;
    outputs --> risk
    source --> risk
    boundary --> risk
    docs --> risk
    rename --> risk
```

## Current Risks

- tracked file outputs can make small code changes look large in review
- upstream source changes can pressure the package into source-specific special
  cases that leak across the runtime
- report rendering and data collection both touch durable files, so boundary
  drift between them is costly
- docs can lag behind package behavior if output contracts change without a
  matching handbook update

## Migration Risks

- moving existing flat docs into the package handbook can leave stale links if
  navigation and cross-references are updated incompletely
- renaming output paths or slugs would force wide downstream changes across
  tracked artifacts, tests, and published docs

## Open This Page When

- a proposed refactor looks structurally tidy but may widen review cost
- an output rename or boundary shift would affect many tracked surfaces at once

## Purpose

This page shows the structural risks that stay in view during package changes.

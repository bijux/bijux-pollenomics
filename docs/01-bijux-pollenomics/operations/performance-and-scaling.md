---
title: Performance and Scaling
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Performance and Scaling

`bijux-pollenomics` is optimized for reproducibility and inspectability before
throughput.

```mermaid
flowchart LR
    verify["verification work"]
    collect["source collection"]
    publish["report publishing"]
    cost["operational cost"]
    review["keep the expensive step identifiable"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class verify,page cost;
    class collect,publish,review positive;
    verify --> cost
    collect --> cost
    publish --> cost
    cost --> review
```

## Current Performance Truths

- verification targets are much cheaper than full data refreshes
- source collection cost is dominated by upstream download and normalization work
- report publishing cost grows with the size of tracked source outputs and atlas
  assets

## Scaling Rule

Do not hide performance pressure by collapsing workflow boundaries. If a step is
slow, keep the slow step identifiable so reviewers and operators still know
whether the cost came from collection, reporting, or docs publication.

## Use This Page When

- a slow workflow invites bundling steps together in a way that would blur
  causality
- performance tradeoffs need to be explained without pretending throughput is
  the primary optimization goal

## Purpose

This page records the package's performance stance and operational trade-offs.

---
title: Change Principles
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Change Principles

Changes to `bijux-pollenomics` keep the runtime easier to trust, not just
easier to modify.

```mermaid
flowchart LR
    trust["change makes runtime easier to trust"]
    explicit["explicit commands and filenames"]
    separation["collection, normalization, publication stay distinct"]
    review["tracked rewrites stay review-significant"]
    boundary["new ownership is documented"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class trust,page explicit;
    class separation,review,boundary positive;
    trust --> explicit
    trust --> separation
    trust --> review
    trust --> boundary
```

## Principles

- prefer explicit filenames, slugs, and command defaults over hidden convention
- keep source collection, normalization, and reporting as distinguishable steps
- treat tracked `data/` and `docs/report/` rewrites as review-significant
  events
- document boundary changes when the package starts owning a new responsibility
- preserve deterministic local rebuild paths before adding convenience layers

## Anti-Patterns

- mixing maintenance policy into runtime modules
- adding one-off output names that do not fit the existing file contracts
- expanding package scope because a nearby repository surface looks convenient

## Open This Page When

- a change is technically possible but may still be a bad repository tradeoff
- a reviewer needs package-level principles rather than one module-level detail

## Purpose

This page shows the package-level rules that shape future changes.

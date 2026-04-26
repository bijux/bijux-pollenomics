---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Integration Seams

The package integrates across a small set of important seams. Those seams should
stay visible instead of being hidden behind accidental coupling.

```mermaid
flowchart LR
    cli["CLI parsing"]
    handlers["runtime handlers"]
    collection["collection workflows"]
    reports["report bundle assembly"]
    docs["docs/report publication"]
    api["frozen API contracts"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class cli,page handlers;
    class collection,reports,docs,api positive;
    cli --> handlers --> collection --> reports --> docs
    handlers --> api
```

## Main Seams

- CLI parsing to runtime handlers
- runtime handlers to `data_downloader` collection workflows
- normalized data outputs to `reporting` bundle assembly
- runtime outputs to tracked docs publication under `docs/report/`
- package code to frozen contracts under `apis/bijux-pollenomics/v1/`

## Why These Seams Matter

These are the points where subtle scope creep appears first. If reporting starts
depending on raw-source quirks or docs start carrying logic that belongs in the
runtime, the package becomes harder to rebuild and harder to review honestly.

## Bottom Line

The seams are where architecture debt first becomes visible. Protecting them is
less about neatness and more about preserving honest rebuild boundaries.


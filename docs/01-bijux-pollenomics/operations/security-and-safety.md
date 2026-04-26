---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security in `bijux-pollenomics` is mostly about trusted execution and safe
handling of fetched content.

```mermaid
flowchart LR
    upstream["mutable upstream inputs"]
    collect["supported collection paths"]
    xml["defusedxml"]
    diffs["tracked output diffs"]
    review["safe publication review"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class upstream,page review;
    class collect,xml,diffs positive;
    upstream --> collect --> diffs --> review
    upstream --> xml
```

## Current Safety Anchors

- source files are collected through explicit supported-source paths
- XML handling uses `defusedxml`
- repository checks include security and dependency review targets
- tracked outputs make suspicious changes easier to inspect in review

## Operational Caution

Some collection paths interact with mutable external services. Treat upstream
inputs as untrusted and prefer explicit local review of resulting tracked diffs
before assuming a refresh is safe to publish.

## Use This Page When

- a workflow touches fetched content from outside the repository
- a reviewer needs the practical safety stance, not a generic security slogan

## Purpose

This page shows the practical security stance of the runtime package.

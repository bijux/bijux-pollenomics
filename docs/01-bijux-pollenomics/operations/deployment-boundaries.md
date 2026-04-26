---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

The package does not deploy a long-lived application. Its deployable unit is a
set of generated files plus a publishable Python distribution.

```mermaid
flowchart LR
    package["python distribution"]
    docs["mkdocs site and checked-in reports"]
    service["long-lived runtime service"]
    boundary["deployment boundary"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class boundary,page package;
    class docs positive;
    class service caution;
    package --> boundary
    docs --> boundary
    service -.not provided.-> boundary
```

## What Gets Deployed

- Python package artifacts built from `packages/bijux-pollenomics/`
- the MkDocs site that exposes checked-in docs and `docs/report/` outputs

## What Does Not Get Deployed

- a runtime server for interactive data collection
- mutable remote state owned by this package

## Reader Takeaway

Think in terms of distributions and published files, not in terms of an
always-running application that owns mutable server state.


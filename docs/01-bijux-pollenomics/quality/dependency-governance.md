---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency additions should be rare and easy to justify.

```mermaid
flowchart LR
    dependency["new dependency proposal"]
    stdlib["prefer standard library when reasonable"]
    review["treat new library as review event"]
    maintenance["ongoing maintenance cost"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class dependency,page maintenance;
    class stdlib,review positive;
    dependency --> stdlib --> review --> maintenance
```

## Current Stance

- keep runtime dependencies small
- prefer standard-library solutions when they keep the code understandable
- treat new parsing, HTTP, or geospatial libraries as public review events

## Repository Context

Dependency checks are reinforced by repository quality and security targets, but
package docs should still explain why a new dependency is worth its maintenance
cost.

## Core Point

Dependency review is not just a build concern. It changes the long-term trust
and maintenance burden of the runtime surface.


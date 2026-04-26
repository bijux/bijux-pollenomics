---
title: Documentation Standards
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Documentation Standards

Package docs should describe the real runtime, not a hoped-for future runtime.

```mermaid
flowchart LR
    real["real commands, paths, and artifacts"]
    limits["state limitations directly"]
    sync["move docs with public changes"]
    trust["reader trust"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class real,page trust;
    class limits,sync positive;
    real --> trust
    limits --> trust
    sync --> trust
```

## Standards

- use stable, descriptive names for pages and headings
- anchor claims to real commands, paths, modules, or artifacts
- document limitations and migration risks directly instead of hiding them in
  review comments
- update docs in the same change that alters a public command, output path, or
  package boundary

## Core Point

Integrity in docs means being exact about what exists now, including the parts
that are incomplete or inconvenient.


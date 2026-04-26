---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Dependency Direction

Dependency flow moves inward from command surfaces toward stable helpers and
file contracts.

```mermaid
flowchart LR
    cli["CLI surfaces"]
    dispatch["dispatch"]
    services["collector and reporting services"]
    contracts["core helpers and file contracts"]
    forbidden["forbidden reverse pull<br/>low-level code back into CLI or docs policy"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class cli,page dispatch;
    class services,contracts positive;
    class forbidden caution;
    cli --> dispatch --> services --> contracts
    forbidden -.must not happen.-> dispatch
```

## Intended Direction

- CLI entrypoints depend on parsing and runtime dispatch
- dispatch depends on collector and reporting services
- collector and reporting code depend on `core/`, `config.py`, and their own
  local contracts
- low-level helpers do not depend back on command registration or docs
  concerns

## Boundary Rule

Source-specific modules may know how to write their own files, but they do not
reach upward into report rendering policy. Reporting modules may consume
normalized source outputs, but they do not quietly redefine how raw source
collection works.

## Open This Page When

- one module starts importing across too many layers
- a source-specific shortcut risks becoming a package-wide architectural leak

## Purpose

This page shows the dependency flow inside the package.

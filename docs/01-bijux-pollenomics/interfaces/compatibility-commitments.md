---
title: Compatibility Commitments
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Compatibility Commitments

Compatibility in `bijux-pollenomics` is about preserving rebuildability and
review clarity, not only preserving Python import names.

```mermaid
flowchart LR
    compat["compatibility promise"]
    cli["CLI names and scope"]
    defaults["defaults and stable slugs"]
    schemas["frozen API contracts"]
    tracked["tracked data and report layout"]
    non["upstream services and internal modules"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class compat,page cli;
    class defaults,schemas,tracked positive;
    class non caution;
    compat --> cli
    compat --> defaults
    compat --> schemas
    compat --> tracked
    non -.not promised.-> compat
```

## Current Commitments

- documented CLI commands remain named and scoped consistently
- default output roots and stable slugs change only deliberately
- frozen API contracts under `apis/bijux-pollenomics/v1/` stay synchronized with
  implementation
- tracked data and report layout changes are documented when they are
  intentional

## Known Non-Commitments

- upstream source services are not guaranteed stable by this package
- unpublished internal module names may change during refactors

## Bottom Line

The main compatibility promise is that a reader can rebuild and review the same
kind of repository outputs with the same documented surfaces. That is broader
than imports, but narrower than guaranteeing every upstream dependency.


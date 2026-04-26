---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Public Imports

The public import surface is defined by `bijux_pollenomics.__all__`.

```mermaid
flowchart LR
    all["bijux_pollenomics.__all__"]
    reports["report dataclasses"]
    collection["collection dataclasses"]
    workflows["workflow functions"]
    version["__version__"]
    callers["stable caller-facing imports"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class all,page callers;
    class reports,collection,workflows,version positive;
    all --> reports --> callers
    all --> collection --> callers
    all --> workflows --> callers
    all --> version --> callers
```

## Supported Imports

- report dataclasses such as `CountryReport` and `PublishedReportsReport`
- collection dataclasses such as `DataCollectionReport` and `ContextDataReport`
- top-level workflow functions including `collect_data`,
  `collect_context_data`, `generate_country_report`,
  `generate_multi_country_map`, and `generate_published_reports`
- `__version__`

## Import Guidance

Prefer importing through `bijux_pollenomics` for stable caller-facing code.
Reach into internal modules only when changing the package itself.

## Open This Page When

- a consumer needs the top-level import surface only
- a refactor risks moving or renaming symbols that callers treat as stable

## Purpose

This page shows the import surface that external callers should treat as
stable first.

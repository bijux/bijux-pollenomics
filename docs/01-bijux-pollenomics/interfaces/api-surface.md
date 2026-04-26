---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# API Surface

The importable API is intentionally small and mirrors the package's major
workflow families.

```mermaid
flowchart LR
    imports["top-level API imports"]
    collect["collection functions"]
    report["report generation functions"]
    schemas["frozen API schema artifacts"]
    callers["downstream callers and reviewers"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class imports,page callers;
    class collect,report,schemas positive;
    imports --> collect --> callers
    imports --> report --> callers
    schemas --> callers
```

## Runtime Entry Points

- `collect_data` and `collect_context_data` from `data_downloader.api`
- `generate_country_report`, `generate_multi_country_map`, and
  `generate_published_reports` from `reporting.api`

## Report Types

- `DataCollectionReport`
- `ContextDataReport`
- `CountryReport`
- `MultiCountryMapReport`
- `PublishedReportsReport`

## Frozen API Contract

Repository-level API expectations are pinned under `apis/bijux-pollenomics/v1/`
with `schema.yaml`, `pinned_openapi.json`, and `schema.hash`.

## Use This Page When

- someone needs the list of supported importable workflows
- an API-facing change may require schema and caller updates

## Purpose

This page shows the import and schema surfaces that count as public package
API.

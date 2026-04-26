---
title: Extensibility Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Extensibility Model

The package is designed to add new sources and reporting refinements by
extending named registries and stable file contracts rather than by inserting
special cases everywhere.

```mermaid
flowchart LR
    source["new source integration"]
    pipeline["pipeline extension"]
    report["new report artifact"]
    contracts["stable tracked paths and contracts"]
    docs_tests["docs and tests update together"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class source,page pipeline;
    class report,contracts,docs_tests positive;
    source --> contracts
    pipeline --> contracts
    report --> contracts
    contracts --> docs_tests
```

## Expected Extension Paths

- add new source integrations through `data_downloader.sources` and source
  registry wiring
- add new staging or summary behavior through `data_downloader.pipeline`
- add new report artifacts through `reporting.bundles`, `reporting.rendering`,
  and related context helpers

## Guardrails

- new extensions should still land in deterministic tracked paths
- source-specific behavior should stay source-scoped rather than becoming a
  cross-package shortcut
- extension work should update docs and tests at the same time as code

## Reader Takeaway

Good extension work adds one new path of capability while preserving the same
review shape. It should not require readers to relearn where files land or how
commands behave.

## Purpose

This page explains how the package is expected to grow without losing shape.

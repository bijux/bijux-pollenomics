---
title: Capability Map
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Capability Map

The package has three durable capability families.

```mermaid
flowchart LR
    collection["collection"]
    reporting["reporting"]
    coordination["coordination"]
    outputs["tracked files and publications"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class collection,page reporting;
    class coordination,outputs positive;
    collection --> coordination
    coordination --> reporting
    collection --> outputs
    reporting --> outputs
```

## Collection

- register supported sources through `data_downloader.pipeline.source_registry`
- fetch raw source data and stage it into source-specific trees
- normalize records so later reporting code can consume a stable shape

## Reporting

- build country bundles for AADR-driven report slices
- assemble the shared Nordic atlas with country and layer context
- write markdown, HTML, JSON, and auxiliary assets into `docs/report/`

## Coordination

- expose package defaults from `config.py`
- map CLI commands onto handlers and workflows
- centralize file, slug, and output-root conventions

## Why This Split Matters

This breakdown helps reviewers see whether a change is adding a new capability,
changing one existing capability, or leaking one responsibility into the wrong
part of the package.

## Purpose

This page names the core capabilities the package is expected to defend over
time.

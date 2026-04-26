---
title: Artifact Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Artifact Contracts

Published artifacts are part of the package contract because they are checked in
and reviewed like code.

```mermaid
flowchart LR
    package["package reporting logic"]
    country["country bundles"]
    atlas["shared atlas"]
    summaries["summary and payload files"]
    review["publication contract readers inspect"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class package,page review;
    class country,atlas,summaries positive;
    package --> country --> review
    package --> atlas --> review
    package --> summaries --> review
```

## Main Artifact Families

- country bundles under `docs/report/<country-slug>/`
- the shared atlas under `docs/report/nordic-atlas/`
- report summaries and map payloads produced by the reporting package

## Contract Anchors

- `reporting/bundles/paths.py`
- `reporting/rendering/`
- `reporting/map_document/`

## Review Rule

If an output path, slug, or file family changes, treat it as an interface change
and update docs plus tests together with the code.

## Reader Takeaway

Artifact contracts matter because the website and repository review process both
consume these files directly. Breaking them is not an internal refactor.

## Purpose

This page records the stable publication artifact surface owned by the package.

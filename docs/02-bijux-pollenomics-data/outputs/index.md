---
title: Outputs
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Outputs

Use this section to understand the normalized and published file families that
the data system produces.

This section should help a reader move from one checked-in file family to the
reason it exists: which normalized outputs are intermediate evidence surfaces,
which bundles are publication-facing, and how the Nordic atlas relates to both.

```mermaid
flowchart LR
    reader["reader question<br/>what output surface am I actually looking at?"]
    normalize["normalized source outputs"]
    summaries["collection summaries"]
    reports["published country bundles"]
    atlas["Nordic atlas publication"]
    field["fieldwork media can anchor one visible point"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class reader page;
    class normalize,summaries,reports,atlas,field positive;
    normalize --> summaries
    summaries --> reports
    reports --> atlas
    field --> atlas
    atlas --> reader
```

## Start Here

- use [Collection Summary](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/collection-summary/) for the shortest overview of
  what is currently checked in
- use [Published Reports](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/published-reports/) when the question is about the
  country bundles rather than intermediate normalized files
- use [Nordic Atlas Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/nordic-atlas/) when the question starts from the
  map rather than from a source family
- use [Normalized Neotoma Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/normalized-neotoma/) or another source
  family page when the issue is already narrowed to one checked-in file family

## Pages In Outputs

- [Collection Summary](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/collection-summary/)
- [Normalized AADR Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/normalized-aadr/)
- [Normalized Boundary Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/normalized-boundaries/)
- [Normalized LandClim Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/normalized-landclim/)
- [Normalized Neotoma Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/normalized-neotoma/)
- [Normalized RAÄ Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/normalized-raa/)
- [Normalized SEAD Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/normalized-sead/)
- [Published Reports](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/published-reports/)
- [Nordic Atlas Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/nordic-atlas/)

## Use This Section When

- you need to inspect one checked-in output family directly
- you want to know whether a file is a normalized input, a publication bundle,
  or the atlas surface itself
- the question starts from repository-owned outputs rather than from upstream
  sources

## Move On When

- the real question is about source caveats before normalization
- the issue is about the tracked data tree rules rather than one output family
- the concern belongs to runtime commands or maintainer automation instead of
  published files

## Concrete Anchors

- `docs/report/denmark/`, `docs/report/finland/`, `docs/report/norway/`, and
  `docs/report/sweden/` for the public country bundles
- `docs/report/nordic-atlas/` for the atlas publication surface
- `data/*/normalized/` for the intermediate repository-owned outputs that feed
  later bundles
- [Published Reports](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/published-reports/) and [Nordic Atlas Outputs](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/outputs/nordic-atlas/)
  for the bridge between raw normalized outputs and reader-facing publication

## Reader Takeaway

This section is where publication-facing files become concrete. It should help
readers distinguish intermediate normalized evidence from the country bundles
and atlas surfaces that the site exposes publicly.

## What You Get

This page gives you the route from one checked-in output family to the page
that explains whether it is intermediate evidence, a published bundle, or the
atlas surface itself.

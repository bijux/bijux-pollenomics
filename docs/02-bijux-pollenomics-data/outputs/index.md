---
title: Outputs
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Outputs

This section explains the normalized and published file families that the data
system produces.

This section should help a reader move from one checked-in file family to the
reason it exists: which normalized outputs are intermediate evidence surfaces,
which bundles are publication-facing, and how the Nordic atlas relates to both.

```mermaid
flowchart LR
    normalize["normalized source outputs"]
    summaries["collection summaries"]
    reports["published country bundles"]
    atlas["Nordic atlas publication"]
    reader["reader question<br/>what output surface am I actually looking at?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class normalize,page reader;
    class summaries,reports,atlas positive;
    normalize --> summaries --> reports --> atlas --> reader
```

## Start Here

- open [Collection Summary](collection-summary.md) for the shortest overview of
  what is currently checked in
- open [Published Reports](published-reports.md) when the question is about the
  country bundles rather than intermediate normalized files
- open [Nordic Atlas Outputs](nordic-atlas.md) when the question starts from the
  map rather than from a source family

## Pages In This Section

- [Collection Summary](collection-summary.md)
- [Normalized AADR Outputs](normalized-aadr.md)
- [Normalized Boundary Outputs](normalized-boundaries.md)
- [Normalized LandClim Outputs](normalized-landclim.md)
- [Normalized Neotoma Outputs](normalized-neotoma.md)
- [Normalized RAÄ Outputs](normalized-raa.md)
- [Normalized SEAD Outputs](normalized-sead.md)
- [Published Reports](published-reports.md)
- [Nordic Atlas Outputs](nordic-atlas.md)

## Use This Section When

- you need to inspect one checked-in output family directly
- you want to know whether a file is a normalized input, a publication bundle,
  or the atlas surface itself
- the question starts from repository-owned outputs rather than from upstream
  sources

## Do Not Start Here When

- the real question is about source caveats before normalization
- the issue is about the tracked data tree rules rather than one output family
- the concern belongs to runtime commands or maintainer automation instead of
  published files

## Reader Takeaway

This section is where publication-facing files become concrete. It should help
readers distinguish intermediate normalized evidence from the country bundles
and atlas surfaces that the site exposes publicly.

## Purpose

This page organizes the normalized and publication-facing output families of the
data system.

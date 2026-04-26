---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Foundation

These pages explain the architecture of the pollenomics data tree before any
single source or output family is discussed.

This section should answer the questions that stay true even when one source
family or one output bundle changes: how the tracked tree is shaped, how
provenance is preserved, how naming and coordinates stay stable, and where
migration risk starts when the layout moves.

```mermaid
flowchart LR
    shape["data system overview"]
    layout["directory layout"]
    provenance["provenance and publication linkage"]
    policy["naming, coordinates, and source selection rules"]
    lifecycle["update lifecycle and migration issues"]
    reader["reader question<br/>what keeps the tracked data tree coherent?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class shape,page reader;
    class layout,provenance,policy,lifecycle positive;
    shape --> reader
    layout --> reader
    provenance --> reader
    policy --> reader
    lifecycle --> reader
```

## Start Here

- open [Data System Overview](data-system-overview.md) for the shortest
  description of the tracked data model
- open [Directory Layout](directory-layout.md) when the real question is file
  placement and ownership
- open [Provenance Model](provenance-model.md) before changing how upstream
  origin is represented

## Pages In This Section

- [Data System Overview](data-system-overview.md)
- [Directory Layout](directory-layout.md)
- [Source Selection Rules](source-selection-rules.md)
- [Update Lifecycle](update-lifecycle.md)
- [Provenance Model](provenance-model.md)
- [Naming Conventions](naming-conventions.md)
- [Coordinate Policy](coordinate-policy.md)
- [Publication Linkage](publication-linkage.md)
- [Migration Issues](migration-issues.md)

## Use This Section When

- the question is about the shared rules of the tracked data tree rather than
  one source family in isolation
- you need to know how provenance, layout, naming, or publication linkage are
  supposed to stay stable
- you are evaluating whether a data-layout change will create wide review cost

## Do Not Start Here When

- the real question is about one concrete upstream source and its caveats
- you only need one normalized output family rather than the shared tree rules
- the issue belongs to runtime commands or maintainer automation rather than
  tracked data structure

## Reader Takeaway

This section is the stable rulebook for the tracked data tree. It should make
the shape, provenance, and migration constraints visible before a reader drops
into one source page or one published output family.

## Purpose

This page organizes the shared rules that shape the tracked data tree.

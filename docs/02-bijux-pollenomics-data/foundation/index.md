---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Foundation

This section is for readers who need the shared rules of the tracked data tree
before any single source family or output bundle is discussed.

Readers often arrive here after seeing one atlas layer or one checked-in file
and asking what keeps the overall data system coherent. This section is where
that answer lives: directory shape, provenance discipline, naming rules,
coordinate policy, publication linkage, and the migration pressure created when
the tracked tree moves.

```mermaid
flowchart LR
    reader["reader question<br/>what keeps the tracked data tree coherent?"]
    shape["shared directory shape"]
    provenance["provenance and publication linkage"]
    policy["naming, coordinates, and source selection rules"]
    lifecycle["update lifecycle and migration risk"]
    outputs["checked-in outputs depend on these rules"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class reader page;
    class shape,provenance,policy,lifecycle,outputs positive;
    shape --> reader
    provenance --> reader
    policy --> reader
    lifecycle --> reader
    outputs --> reader
```

## Start Here

- use [Data System Overview](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/data-system-overview/) for the shortest
  description of the tracked data model
- use [Directory Layout](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/directory-layout/) when the real question is file
  placement and ownership
- use [Provenance Model](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/provenance-model/) before changing how upstream
  origin is represented
- use [Migration Issues](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/migration-issues/) before renaming directories,
  moving files, or changing output expectations across the tree

## Pages In Foundation

- [Data System Overview](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/data-system-overview/)
- [Directory Layout](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/directory-layout/)
- [Source Selection Rules](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/source-selection-rules/)
- [Update Lifecycle](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/update-lifecycle/)
- [Provenance Model](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/provenance-model/)
- [Naming Conventions](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/naming-conventions/)
- [Coordinate Policy](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/coordinate-policy/)
- [Publication Linkage](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/publication-linkage/)
- [Migration Issues](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/migration-issues/)

## Use This Section When

- the question is about the shared rules of the tracked data tree rather than
  one source family in isolation
- you need to know how provenance, layout, naming, or publication linkage are
  supposed to stay stable
- you are evaluating whether a data-layout change will create wide review cost

## Move On When

- the real question is about one concrete upstream source and its caveats
- you only need one normalized output family rather than the shared tree rules
- the issue belongs to runtime commands or maintainer automation rather than
  tracked data structure

## Concrete Anchors

- `data/` for the repository-owned tracked source tree
- `docs/report/` for the publication-facing outputs that depend on the shared
  data rules staying stable
- [Directory Layout](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/directory-layout/) and [Publication Linkage](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/publication-linkage/)
  for the rule set that ties repository structure to visible publication
- [Migration Issues](https://bijux.io/bijux-pollenomics/02-bijux-pollenomics-data/foundation/migration-issues/) for the cost surface when the tree
  shape changes

## Reader Takeaway

This section is the stable rulebook for the tracked data tree. It should make
the shape, provenance, and migration constraints visible before a reader drops
into one source page or one published output family.

## What You Get

Open this page when you need the shared layout, provenance, naming,
coordinate, and migration route through the tracked data tree before you
inspect one source family or one output bundle.

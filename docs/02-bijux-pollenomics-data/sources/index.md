---
title: Sources
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Sources

This section catalogs the supported upstream source families that feed the
tracked data tree.

This section should help a reader answer three practical questions quickly:
which upstream family they are looking at, which caveats travel with that
family, and which shared normalization rules apply before the data appears in
the published atlas or reports.

```mermaid
flowchart LR
    upstream["upstream source family"]
    page["source-specific page"]
    shared["shared normalization rules"]
    compare["source comparison and refresh policy"]
    outputs["normalized outputs and reports"]
    reader["reader question<br/>what should I trust about this source?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class upstream,page reader;
    class page,shared,compare,outputs positive;
    upstream --> page --> shared --> outputs --> reader
    page --> compare
```

## Start Here

- open one source page when reviewing one upstream family in isolation
- open [Shared Normalization](shared-normalization.md) for rules that apply
  across source families
- open [Source Comparison](source-comparison.md) when deciding which source is
  relevant for one kind of atlas or report question

## Pages In This Section

- [AADR](aadr.md)
- [Boundaries](boundaries.md)
- [LandClim](landclim.md)
- [Neotoma](neotoma.md)
- [RAÄ](raa.md)
- [SEAD](sead.md)
- [Shared Normalization](shared-normalization.md)
- [Source Comparison](source-comparison.md)
- [Refresh Policy](refresh-policy.md)

## Use This Section When

- the question is about one upstream family and its caveats
- you need to compare what different source families contribute to the atlas or
  reports
- you need to understand what normalization and refresh rules apply before
  downstream publication

## Do Not Start Here When

- the real question is about one checked-in output family rather than its
  upstream origin
- the issue is about tracked data layout rather than source behavior
- the concern belongs to package runtime commands or maintainer automation

## Reader Takeaway

This section is where source-specific uncertainty becomes explicit. It should
help readers distinguish raw upstream behavior from the normalized, checked-in
outputs they see later in the data and atlas pages.

## Purpose

This page organizes the upstream source material that feeds the tracked data
tree.

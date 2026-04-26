---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Foundation

Use this section when the most important question is not how the runtime is
implemented, but why it exists and where its responsibility stops.

`bijux-pollenomics` is the repository's execution surface. It owns the code
that collects tracked evidence, normalizes it into governed repository files,
and turns those files into reviewable publication outputs. It does not own the
meaning of the science, the full provenance handbook, or repository-wide
maintenance policy. This page should let a reader see that boundary quickly.

```mermaid
flowchart LR
    reader["reader question<br/>why does this package exist?"]
    commands["commands and entrypoints"]
    collect["collect and normalize<br/>tracked source material"]
    publish["publish bundles and atlas artifacts"]
    data["data handbook<br/>provenance and file families"]
    maintain["maintainer handbook<br/>automation and release policy"]
    science["scientific interpretation<br/>stays explicit and limited"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class reader page;
    class commands,collect,publish positive;
    class data,maintain,science caution;
    reader --> commands
    commands --> collect
    collect --> publish
    collect -.provenance explained in.-> data
    publish -.release and verification owned by.-> maintain
    publish -.does not imply.-> science
```

## Start Here

- open [Package Overview](package-overview.md) for the shortest durable
  statement of the runtime's job
- open [Ownership Boundary](ownership-boundary.md) when a proposed change may
  belong in the data handbook, maintainer handbook, or checked-in docs instead
- open [Lifecycle Overview](lifecycle-overview.md) when you need the
  collect-normalize-publish loop before reading any module detail
- open [Scope and Non-Goals](scope-and-non-goals.md) before expanding the
  runtime into a new data, workflow, or interpretation surface

## Pages In This Section

- [Package Overview](package-overview.md)
- [Scope and Non-Goals](scope-and-non-goals.md)
- [Ownership Boundary](ownership-boundary.md)
- [Repository Fit](repository-fit.md)
- [Capability Map](capability-map.md)
- [Domain Language](domain-language.md)
- [Lifecycle Overview](lifecycle-overview.md)
- [Dependencies and Adjacencies](dependencies-and-adjacencies.md)
- [Change Principles](change-principles.md)

## Use This Section When

- you need the durable ownership story before changing code, commands, or file
  contracts
- you are deciding whether a change belongs in runtime behavior or in a nearby
  repository surface
- you need language that distinguishes evidence collection, normalization,
  publication, and interpretation without blending them together

## Do Not Use This Section When

- the real question is already about command syntax, file layouts, or imports
- you need code structure, dependency direction, or execution seams
- the issue is operational, such as rebuild workflow, diagnostics, or release

## Concrete Anchors

- `src/bijux_pollenomics/cli.py` and `src/bijux_pollenomics/command_line/`
  for the operator-facing runtime boundary
- `src/bijux_pollenomics/data_downloader/collector.py` and
  `src/bijux_pollenomics/data_downloader/pipeline/` for the collection and
  normalization loop
- `src/bijux_pollenomics/reporting/` and
  `src/bijux_pollenomics/reporting/bundles/` for publication ownership
- `tests/regression/test_repository_contracts.py` for the repository-facing
  proof that package ownership still matches tracked outputs

## Read Across The Package

- open [Architecture](../architecture/index.md) when the question becomes
  structural rather than boundary-oriented
- open [Interfaces](../interfaces/index.md) when the concern is a public
  command, config, or artifact contract
- open [Operations](../operations/index.md) when you need a repeatable runtime
  workflow
- open [Quality](../quality/index.md) when the question becomes proof, risk, or
  validation sufficiency

## Reader Takeaway

Use `Foundation` to answer the ownership question with integrity:
`bijux-pollenomics` exists to execute a controlled evidence loop from tracked
inputs to tracked publication outputs. If a proposal makes the package broader
without making that loop clearer, it is probably crossing a boundary rather
than strengthening the runtime.

## Purpose

This page introduces the boundary-setting material for the runtime package and
routes readers to the specific scope, ownership, lifecycle, and language pages
that explain why the package exists.

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

The aim here is not to defend the runtime as "the main thing" in the
repository. The aim is to show why a distinct runtime package is necessary at
all: there has to be one accountable place where collection, normalization, and
publication behavior are held together without letting provenance, release
policy, or interpretation blur into the same layer.

```mermaid
flowchart LR
    reader["reader question<br/>why does this package exist?"]
    boundary["runtime boundary<br/>collect, normalize, publish"]
    inputs["tracked source inputs<br/>AADR, pollen, archaeology,<br/>boundaries, field context"]
    outputs["tracked publication outputs<br/>data/ and docs/report/"]
    data["data handbook<br/>provenance and file families"]
    maintain["maintainer handbook<br/>automation and release policy"]
    science["scientific interpretation<br/>stays explicit and limited"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class reader page;
    class boundary,inputs,outputs positive;
    class data,maintain,science caution;
    reader --> boundary
    inputs --> boundary
    boundary --> outputs
    boundary -.provenance explained in.-> data
    outputs -.release and verification owned by.-> maintain
    outputs -.do not settle.-> science
```

## Start Here

- use [Package Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/package-overview/) for the shortest durable
  statement of the runtime's job
- use [Ownership Boundary](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/ownership-boundary/) when a proposed change may
  belong in the data handbook, maintainer handbook, or checked-in docs instead
- use [Lifecycle Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/lifecycle-overview/) when you need the
  collect-normalize-publish loop before reading any module detail
- use [Scope and Non-Goals](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/scope-and-non-goals/) before expanding the
  runtime into a new data, workflow, or interpretation surface

## Pages In Foundation

- [Package Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/change-principles/)

## Use This Section When

- you need the durable ownership story before changing code, commands, or file
  contracts
- you are deciding whether a change belongs in runtime behavior or in a nearby
  repository surface
- you need language that distinguishes evidence collection, normalization,
  publication, and interpretation without blending them together

## Move On When

- the real question is already about command syntax, file layouts, or imports
- you need code structure, dependency direction, or execution seams
- the issue is operational, such as rebuild workflow, diagnostics, or release

## What This Section Clarifies

- why the runtime owns the controlled transition from source material to
  checked-in outputs
- why provenance detail belongs in the data handbook instead of being folded
  into runtime ownership claims
- why publication behavior and scientific meaning must stay separable even when
  they touch the same visible atlas layer

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

- use [Architecture](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/) when the question becomes
  structural rather than boundary-oriented
- use [Interfaces](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/) when the concern is a public
  command, config, or artifact contract
- use [Operations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/) when you need a repeatable runtime
  workflow
- use [Quality](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/) when the question becomes proof, risk, or
  validation sufficiency

## Reader Takeaway

Use `Foundation` to answer the ownership question with integrity:
`bijux-pollenomics` exists to execute a controlled evidence loop from tracked
inputs to tracked publication outputs. If a proposal makes the package broader
without making that loop clearer, it is probably crossing a boundary rather
than strengthening the runtime.

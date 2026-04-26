---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Foundation

Open this section when the main question is not how the runtime is
implemented, but why it exists and where its responsibility stops.

`bijux-pollenomics` is the repository's execution surface. It owns the code
that collects tracked evidence, normalizes it into governed repository files,
and turns those files into reviewable publication outputs. It does not own the
meaning of the science, the full provenance handbook, or repository-wide
maintenance policy. The boundary needs to stay visible quickly and honestly.

The aim here is not to defend the runtime as "the main thing" in the
repository. The aim is to show why a distinct runtime package is necessary at
all: there has to be one accountable place where collection, normalization, and
publication behavior are held together without letting provenance, release
policy, or interpretation blur into the same layer.

## Start Here

- open [Package Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/package-overview/) for the shortest durable
  statement of the runtime's job
- open [Ownership Boundary](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/ownership-boundary/) when a proposed change may
  belong in the data handbook, maintainer handbook, or checked-in docs instead
- open [Lifecycle Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/lifecycle-overview/) when you need the
  collect-normalize-publish loop before reading any module detail
- open [Scope and Non-Goals](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/scope-and-non-goals/) before expanding the
  runtime into a new data, workflow, or interpretation surface

## Pages In This Section

- [Package Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/package-overview/)
- [Scope and Non-Goals](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/scope-and-non-goals/)
- [Ownership Boundary](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/ownership-boundary/)
- [Repository Fit](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/repository-fit/)
- [Capability Map](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/capability-map/)
- [Domain Language](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/domain-language/)
- [Lifecycle Overview](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/lifecycle-overview/)
- [Dependencies and Adjacencies](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/dependencies-and-adjacencies/)
- [Change Principles](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/change-principles/)

## Open This Section When

- you need the durable ownership story before changing code, commands, or file
  contracts
- you are deciding whether a change belongs in runtime behavior or in a nearby
  repository surface
- you need language that distinguishes evidence collection, normalization,
  publication, and interpretation without blending them together

## Open Another Section When

- the real question is already about command syntax, file layouts, or imports
- you need code structure, dependency direction, or execution seams
- the issue is operational, such as rebuild workflow, diagnostics, or release

## What This Section Covers

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

## Across This Package

- open [Architecture](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/) when the question becomes
  structural rather than boundary-oriented
- open [Interfaces](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/) when the concern is a public
  command, config, or artifact contract
- open [Operations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/) when you need a repeatable runtime
  workflow
- open [Quality](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/) when the question becomes proof, risk, or
  validation sufficiency

## Bottom Line

Open this section to answer the ownership question directly:
`bijux-pollenomics` exists to execute a controlled evidence loop from tracked
inputs to tracked publication outputs. If a proposal makes the package broader
without making that loop clearer, it is probably crossing a boundary rather
than strengthening the runtime.

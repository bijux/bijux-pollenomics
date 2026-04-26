---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Foundation

Use this section when the important question is why the runtime package exists
at all: what `bijux-pollenomics` is supposed to own, where that ownership
stops, and which nearby repository surfaces it depends on without absorbing.

These pages should help readers separate runtime behavior from repository
maintenance, data reference, and interpretation work. When this section is
clear, a maintainer can explain why a change belongs in the package without
having to fall back on team memory.

```mermaid
flowchart LR
    commands["runtime commands"]
    collect["collection and normalization"]
    publish["report and atlas publishing"]
    boundary["boundary<br/>docs, data reference, and maintainer systems stay outside"]
    language["shared runtime language"]
    reader["reader question<br/>what should this package own?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class collect,page reader;
    class commands,publish,language positive;
    class boundary caution;
    commands --> collect --> publish
    collect --> boundary
    language --> reader
    publish --> reader
    boundary --> reader
```

## Start Here

- open [Package Overview](package-overview.md) for the shortest statement of the
  package's job
- open [Ownership Boundary](ownership-boundary.md) when the question may belong
  in repository, data, or maintainer docs instead
- open [Scope and Non-Goals](scope-and-non-goals.md) before adding new runtime
  responsibilities
- open [Lifecycle Overview](lifecycle-overview.md) when you need the runtime
  loop before reading module or contract detail

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

- you need the durable ownership story before changing code or contracts
- you are deciding whether a change belongs in runtime behavior or in a nearby
  repository surface
- you need stable language for collection, normalization, publishing, and
  review-oriented outputs

## Do Not Use This Section When

- the real question is already about command syntax, file layouts, or imports
- you need code structure, dependency direction, or execution seams
- the issue is operational, such as rebuild workflow, diagnostics, or release

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
`bijux-pollenomics` exists to turn tracked evidence inputs into reviewable
tracked outputs through explicit runtime commands. If a proposal broadens the
package without making that runtime loop clearer, it is probably crossing the
boundary rather than improving it.

## Purpose

This page introduces the boundary-setting material for the runtime package and
routes readers to the specific scope, ownership, lifecycle, and language pages
that explain why the package exists.

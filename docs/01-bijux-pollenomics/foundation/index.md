---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Foundation

The foundation pages explain why `bijux-pollenomics` exists, what it owns on
purpose, and which neighboring repository surfaces it depends on without
absorbing.

Use this section before changing module boundaries or public contracts. It is
the place to confirm that a change still matches the package's intended role.

```mermaid
flowchart LR
    overview["package overview"]
    scope["scope and non-goals"]
    ownership["ownership boundary"]
    lifecycle["lifecycle overview"]
    language["domain language"]
    change["change principles"]
    reader["reader question<br/>what should this package own?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class overview,page reader;
    class scope,ownership,lifecycle,language,change positive;
    overview --> reader
    scope --> reader
    ownership --> reader
    lifecycle --> reader
    language --> reader
    change --> reader
```

## Start Here

- open [Package Overview](package-overview.md) for the shortest statement of the
  package's job
- open [Scope and Non-Goals](scope-and-non-goals.md) before adding new runtime
  responsibilities
- open [Ownership Boundary](ownership-boundary.md) when the question may belong
  in repository, data, or maintainer docs instead

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

## What This Section Should Answer

- why the runtime package exists at all
- which responsibilities belong inside the package and which belong elsewhere
- which words, lifecycle steps, and review principles should stay stable across
  future changes

## Purpose

This page organizes the boundary-setting material for the runtime package.

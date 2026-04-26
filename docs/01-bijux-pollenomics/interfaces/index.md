---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Interfaces

Use this section when the question is which runtime surfaces are real
contracts: commands, defaults, tracked data layouts, publication artifacts, and
the import surfaces that operators or other repository layers can safely rely
on.

These pages should stop accidental dependencies from hardening around incidental
implementation details. In this package, that matters because command behavior
and tracked file outputs are reviewed like code and exposed directly on the
docs site.

```mermaid
flowchart LR
    cli["CLI surface"]
    config["configuration defaults"]
    data["tracked data contracts"]
    artifacts["publication artifact contracts"]
    imports["public imports and examples"]
    compat["compatibility commitments"]
    reader["reader question<br/>what can I safely rely on?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class cli,page reader;
    class config,data,artifacts,imports,compat positive;
    cli --> reader
    config --> reader
    data --> reader
    artifacts --> reader
    imports --> reader
    compat --> reader
```

## Start Here

- open [CLI Surface](cli-surface.md) for the operator-facing command contract
- open [Artifact Contracts](artifact-contracts.md) when the file outputs matter
  more than the command syntax
- open [Data Contracts](data-contracts.md) when the tracked `data/` layout is
  the real dependency
- open [Entrypoints and Examples](entrypoints-and-examples.md) for concrete
  command expansions and usage examples

## Pages In This Section

- [CLI Surface](cli-surface.md)
- [API Surface](api-surface.md)
- [Configuration Surface](configuration-surface.md)
- [Data Contracts](data-contracts.md)
- [Artifact Contracts](artifact-contracts.md)
- [Entrypoints and Examples](entrypoints-and-examples.md)
- [Operator Workflows](operator-workflows.md)
- [Public Imports](public-imports.md)
- [Compatibility Commitments](compatibility-commitments.md)

## Use This Section When

- you need to know which runtime surface is deliberate and supportable
- a change may affect command behavior, tracked files, or docs-facing outputs
- reviewers need a crisp answer about what counts as an interface change

## Do Not Use This Section When

- the real question is why the package owns a behavior at all
- you need structural layout or execution flow before you can judge a surface
- the issue is mainly operational, such as which workflow to run or how to
  recover from a failure

## Read Across The Package

- open [Foundation](../foundation/index.md) when the interface concern is
  really an ownership question
- open [Architecture](../architecture/index.md) when the surface depends on
  deeper collection, helper, or reporting structure
- open [Operations](../operations/index.md) when you need a repeatable workflow
  for exercising or shipping the contract
- open [Quality](../quality/index.md) when the real issue is whether the
  documented surface is sufficiently defended

## Reader Takeaway

Use `Interfaces` to separate stable runtime contracts from whatever merely
happens to be visible in the implementation today. If a dependency cannot be
defended in terms of named commands, defaults, file layouts, artifacts,
examples, and tests, it is not yet an honest public surface.

## Purpose

This page introduces the public interface material for the runtime package and
routes readers to the command, config, data, artifact, and compatibility pages
they are expected to rely on.

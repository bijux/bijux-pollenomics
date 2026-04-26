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

This package publishes files directly into the repository and onto the docs
site. That means a weak interface story becomes a repository-wide maintenance
problem very quickly. These pages should make it obvious which surfaces are
deliberate and which ones are only incidental implementation visibility.

```mermaid
flowchart LR
    reader["reader question<br/>what can I safely depend on?"]
    cli["CLI flags, subcommands, and defaults"]
    config["configuration values and repository paths"]
    data["tracked data layout contracts"]
    artifacts["country bundles and atlas artifacts"]
    imports["public imports and examples"]
    compat["compatibility commitments"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class reader page;
    class config,data,artifacts,imports,compat positive;
    class cli positive;
    cli --> reader
    config --> reader
    data --> reader
    artifacts --> reader
    imports --> reader
    compat --> reader
```

## Start Here

- open [CLI Surface](cli-surface.md) for the operator-facing command contract
- open [Artifact Contracts](artifact-contracts.md) when the public output files
  matter more than command syntax
- open [Data Contracts](data-contracts.md) when the tracked `data/` tree is the
  real dependency
- open [Compatibility Commitments](compatibility-commitments.md) before
  changing defaults, file names, or output shapes that other readers may have
  automated against

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

## Concrete Anchors

- `src/bijux_pollenomics/cli.py` and
  `src/bijux_pollenomics/command_line/parsing/subcommands.py` for the command
  surface
- `src/bijux_pollenomics/config.py` for defaults and repository-path behavior
- `src/bijux_pollenomics/data_downloader/data_layout.py` and
  `src/bijux_pollenomics/data_downloader/contracts.py` for tracked file
  contracts
- `src/bijux_pollenomics/reporting/rendering/artifacts.py` and
  `src/bijux_pollenomics/reporting/bundles/paths.py` for publication artifact
  shapes
- `tests/e2e/test_cli.py` and `tests/regression/test_repository_contracts.py`
  for interface-facing proof

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
examples, and tests, it is not yet an honest public surface for this
repository.

## Purpose

This page introduces the public interface material for the runtime package and
routes readers to the command, config, data, artifact, and compatibility pages
they are expected to rely on.

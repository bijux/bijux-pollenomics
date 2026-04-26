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

Readers should be able to leave this section with a practical answer, not an
abstract one: which commands are stable enough to run, which tracked files are
safe to automate against, and which atlas-facing outputs are treated as real
publication contracts rather than accidental byproducts.

```mermaid
flowchart LR
    reader["reader question<br/>what can I safely depend on?"]
    cli["CLI flags, subcommands,<br/>and defaults"]
    config["config.py defaults<br/>and repository paths"]
    data["tracked data layout contracts<br/>normalized files under data/"]
    artifacts["country bundles and atlas artifacts<br/>published under docs/report/"]
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

- use [CLI Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/cli-surface/) for the operator-facing command contract
- use [Artifact Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/artifact-contracts/) when the public output files
  matter more than command syntax
- use [Data Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/data-contracts/) when the tracked `data/` tree is the
  real dependency
- use [Compatibility Commitments](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/compatibility-commitments/) before
  changing defaults, file names, or output shapes that other readers may have
  automated against

## Pages In Interfaces

- [CLI Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/compatibility-commitments/)

## Use This Section When

- you need to know which runtime surface is deliberate and supportable
- a change may affect command behavior, tracked files, or docs-facing outputs
- reviewers need a crisp answer about what counts as an interface change

## Move On When

- the real question is why the package owns a behavior at all
- you need structural layout or execution flow before you can judge a surface
- the issue is mainly operational, such as which workflow to run or how to
  recover from a failure

## What This Section Clarifies

- which runtime surfaces are safe for operators and maintainers to script
  against
- which tracked file layouts and published artifacts are treated as stable
  contracts instead of convenient current shapes
- which changes require compatibility review because they would alter a visible
  repository or docs surface

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

- use [Foundation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/) when the interface concern is
  really an ownership question
- use [Architecture](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/) when the surface depends on
  deeper collection, helper, or reporting structure
- use [Operations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/) when you need a repeatable workflow
  for exercising or shipping the contract
- use [Quality](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/) when the real issue is whether the
  documented surface is sufficiently defended

## Reader Takeaway

Use `Interfaces` to separate stable runtime contracts from whatever merely
happens to be visible in the implementation today. If a dependency cannot be
defended in terms of named commands, defaults, file layouts, artifacts,
examples, and tests, it is not yet an honest public surface for this
repository.

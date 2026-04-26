---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Interfaces

Open this section when the question is which runtime surfaces are real
contracts: commands, defaults, tracked data layouts, publication artifacts,
and the import surfaces that operators or other repository layers can safely
rely on.

This package publishes files directly into the repository and onto the docs
site. That means a weak interface story becomes a repository-wide maintenance
problem very quickly. The deliberate surfaces need to stay distinct from
incidental implementation visibility.

This section leaves a practical answer, not an abstract one: which commands
are stable enough to run, which tracked files are safe to automate against,
and which atlas-facing outputs are treated as real publication contracts
rather than accidental byproducts.

## Start Here

- open [CLI Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/cli-surface/) for the operator-facing command contract
- open [Artifact Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/artifact-contracts/) when the public output files
  matter more than command syntax
- open [Data Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/data-contracts/) when the tracked `data/` tree is the
  real dependency
- open [Compatibility Commitments](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/compatibility-commitments/) before
  changing defaults, file names, or output shapes that other readers may have
  automated against

## Pages In This Section

- [CLI Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/interfaces/compatibility-commitments/)

## Open This Section When

- you need to know which runtime surface is deliberate and supportable
- a change may affect command behavior, tracked files, or docs-facing outputs
- reviewers need a crisp answer about what counts as an interface change

## Open Another Section When

- the real question is why the package owns a behavior at all
- you need structural layout or execution flow before you can judge a surface
- the issue is mainly operational, such as which workflow to run or how to
  recover from a failure

## What This Section Covers

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

## Across This Package

- open [Foundation](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/foundation/) when the interface concern is
  really an ownership question
- open [Architecture](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/architecture/) when the surface depends on
  deeper collection, helper, or reporting structure
- open [Operations](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/operations/) when you need a repeatable workflow
  for exercising or shipping the contract
- open [Quality](https://bijux.io/bijux-pollenomics/01-bijux-pollenomics/quality/) when the real issue is whether the
  documented surface is sufficiently defended

## Bottom Line

Open this section to separate stable runtime contracts from whatever merely
happens to be visible in the implementation today. If a dependency cannot be
defended in terms of named commands, defaults, file layouts, artifacts,
examples, and tests, it is not yet an honest public surface for this
repository.

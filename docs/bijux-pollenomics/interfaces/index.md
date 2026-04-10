---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Interfaces

This section records the public surfaces that other repository layers and human
operators rely on: commands, configs, artifacts, and frozen API contracts.

Use it when the question is how callers and reviewers are supposed to interact
with the package without reading every implementation module first.

## Start Here

- open [CLI Surface](cli-surface.md) for the operator-facing command contract
- open [Entrypoints and Examples](entrypoints-and-examples.md) for concrete
  command expansions and usage examples
- open [Artifact Contracts](artifact-contracts.md) when the file outputs matter
  more than the command syntax

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

## Purpose

This page organizes the public interfaces that reviewers and operators are
expected to rely on.

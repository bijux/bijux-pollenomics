---
title: Workflows
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Workflows

This section is the shortest honest path from a fresh checkout to a working local environment, a rebuilt `data/` tree, and regenerated outputs.

It is ordered to keep environment verification separate from commands that rewrite tracked repository state.

```mermaid
flowchart LR
    Checkout[Clone repo] --> Install[make install]
    Install --> Verify[make lint and make test]
    Verify --> DataPrep[make data-prep]
    DataPrep --> Reports[Publish report artifacts]
```

## Pages in This Section

- [Install and verify](install-and-verify.md)
- [Rebuild the data tree](rebuild-data-tree.md)
- [Publish report artifacts](publish-report-artifacts.md)
- [Troubleshoot local setup](troubleshoot-local-setup.md)

## Outcome

By the end of this section you should be able to:

- create the local virtual environment under `artifacts/.venv/`
- confirm that the local Python and tooling match repository expectations
- run lint and tests
- rebuild `data/` with one command
- regenerate the shared Nordic map and country reports

## Workflow Boundary

This section is operational. It explains when a command should be run, what tracked state it rewrites, and what success should leave behind. It is not the place for architectural justification or full command inventories; those live in `Architecture` and `Reference`.

## Reading Rule

Start with [Install and verify](install-and-verify.md) even if you already know the repository. That page is the contract for what a clean environment must satisfy before any data or report outputs are regenerated.

## Purpose

This page organizes the first-run workflow into a sequence that matches the repository’s actual dependency order.

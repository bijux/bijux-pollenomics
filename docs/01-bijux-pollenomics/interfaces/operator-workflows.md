---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Operator Workflows

Most operators meet the package through a short set of repository workflows.
The crucial distinction is between verification and mutation.

## Common Operator Flows

- validate a checkout without changing tracked outputs
- refresh source data into `data/`
- regenerate published report bundles into `docs/report/`
- inspect the resulting atlas and country outputs in the docs site

## First Proof Check

- `makes/`
- `tests/e2e/test_cli.py`
- `tests/regression/test_repository_contracts.py`

---
title: Deployment Boundaries
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Deployment Boundaries

The package does not deploy a long-lived application. Its deployable unit is a
publishable Python distribution plus the checked-in docs site that exposes the
generated outputs.

## What Gets Deployed

- Python package artifacts built from `packages/bijux-pollenomics/`
- the MkDocs site that exposes checked-in docs and `docs/report/` outputs

## What Does Not Get Deployed

- a runtime server for interactive data collection
- mutable remote state owned by this package

## First Proof Check

- `packages/bijux-pollenomics/`
- `docs/report/`
- MkDocs deployment workflow

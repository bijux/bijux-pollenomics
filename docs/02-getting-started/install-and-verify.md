---
title: Install and Verify
audience: mixed
type: workflow
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Install and Verify

Use the local `Makefile` workflow from the repository root.

## Prerequisites

- `python3.11`
- network access for first-time dependency and data collection

## Commands

```bash
make install
make lint
make test
```

## What These Commands Do

- `make install` creates `artifacts/.venv/` and installs the project with dev tooling
- `make lint` runs `ruff` across `src/` and `tests/`
- `make test` runs the checked-in unittest suite

## Expected Result

After these commands:

- `artifacts/.venv/` exists locally
- lint passes
- the test suite passes

## Why Verification Comes Before Data Preparation

The repository should validate the code before pulling or regenerating data. That keeps failures easier to interpret and avoids mixing environment problems with acquisition problems.

## Purpose

This page gives the minimum reliable setup path before any data or report workflow is attempted.

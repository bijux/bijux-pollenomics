---
title: Local Workflow
audience: mixed
type: workflow
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Local Workflow

Use the `Makefile` as the main local interface.

## Primary Commands

```bash
make install
make lock
make lock-check
make reports
make app-state
make check
make clean
make lint
make test
make test-unit
make test-regression
make test-e2e
make data-prep
make build
make package-check
make docs
make docs-serve
```

## Artifact Paths

- `make install` syncs `artifacts/.venv/` from `uv.lock`
- `make lock` rewrites the tracked dependency lockfile after dependency changes
- `make lock-check` verifies that the tracked dependency lockfile is current
- `make reports` regenerates the checked-in report bundles under `docs/report/`
- `make app-state` rebuilds the checked-in repository outputs end to end
- `make check` runs the main repository verification suite in one command
- `make test-unit` runs the logic-level unit suite
- `make test-regression` runs artifact and workflow-regression checks
- `make test-e2e` runs command-line end-to-end checks
- `make build` writes distributions into `artifacts/dist/`
- `make package-check` rebuilds and validates the source and wheel distributions
- `make docs` writes the site into `artifacts/docs/site/`
- `make docs-serve` serves the local docs at `http://127.0.0.1:8000/`

## Why The Makefile Exists

The repository now has enough moving parts that a checked-in local workflow is more reliable than asking contributors to remember raw commands.

## Scope-Based Verification

Choose the smallest honest verification surface for the change:

- docs-only edits: run `make docs`
- logic or command-surface edits: run `make lint`, the relevant test targets, and `make package-check` when packaging or console entrypoints changed
- collector or reporting contract edits: run the relevant tests and regenerate affected checked-in artifacts
- repository-wide refactors: run `make check` and rebuild whichever tracked outputs the change touches

## Accuracy Rule

When docs or code comments describe a command, file, or artifact, verify it against the current repository state before merging the change.

## Purpose

This page records the preferred local development surface.

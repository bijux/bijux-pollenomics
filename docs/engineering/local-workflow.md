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
artifacts/.venv/bin/bijux-pollenomics --version
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
make package-verify
make package-check
make package-smoke
make package-source-smoke
make docs
make docs-serve
```

## Artifact Paths

- `make install` syncs `artifacts/.venv/` from `uv.lock`
- `artifacts/.venv/bin/bijux-pollenomics --version` is the direct smoke check that the editable CLI is installed where the `Makefile` expects it
- `make lock` rewrites the tracked dependency lockfile after dependency changes
- `make lock-check` verifies that the tracked dependency lockfile is current
- `make reports` regenerates the checked-in report bundles under `docs/report/`
- `make app-state` rebuilds the checked-in repository outputs end to end
- `make check` runs the main repository verification suite in one command
- `make test-unit` runs the logic-level unit suite
- `make test-regression` runs artifact and workflow-regression checks
- `make test-e2e` runs command-line end-to-end checks
- `make build` writes distributions into `artifacts/dist/`
- `make package-verify` rebuilds distributions, validates metadata, and smoke-tests both distribution formats
- `make package-check` rebuilds and validates the source and wheel distributions
- `make package-smoke` installs the built wheel into a temporary environment and runs the CLI there
- `make package-source-smoke` installs the built source distribution into a temporary environment and runs the CLI there
- `make docs` writes the site into `artifacts/docs/site/`
- `make docs-serve` serves the local docs at `http://127.0.0.1:8000/`

## Why The Makefile Exists

The repository now has enough moving parts that a checked-in local workflow is more reliable than asking contributors to remember raw commands.

## Scope-Based Verification

Choose the smallest honest verification surface for the change:

- docs-only edits: run `make docs`
- logic or command-surface edits: run `make lint`, the relevant test targets, `artifacts/.venv/bin/bijux-pollenomics --version` for editable-install sanity, and `make package-verify` when packaging or console entrypoints changed
- collector or reporting contract edits: run the relevant tests and regenerate affected checked-in artifacts
- repository-wide refactors: run `make check` and rebuild whichever tracked outputs the change touches

## Accuracy Rule

When docs or code comments describe a command, file, or artifact, verify it against the current repository state before merging the change.

## Purpose

This page records the preferred local development surface.

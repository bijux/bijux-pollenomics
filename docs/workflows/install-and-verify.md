---
title: Install and Verify
audience: mixed
type: workflow
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Install and Verify

Use the local `Makefile` workflow from the repository root. This page is intentionally limited to environment setup and code verification. It does not rebuild tracked data or tracked reports.

## Prerequisites

- `python3.11`
- `uv`
- network access for first-time dependency installation
- permission to create the local virtual environment under `artifacts/.venv/`

## Confirm The Python Runtime

Before creating the virtual environment, verify the interpreter the repository expects:

```bash
python3.11 --version
```

Expected result:

- the command exists locally
- the reported version is Python `3.11.x`

If `python3.11` is not available, fix that first. Do not continue with `make install` and hope the repository will select a compatible interpreter automatically.

## Commands

```bash
make install
make lock-check
make lint
make test
make package-check
make package-smoke
make package-source-smoke
make docs
```

## What These Commands Do

- `make install` syncs `artifacts/.venv/` from the tracked `uv.lock` with the project installed in editable mode
- `make lock-check` verifies that `uv.lock` still matches `pyproject.toml`
- `make lint` runs `ruff` across `src/` and `tests/`
- `make test` runs the checked-in unittest suite with verbose discovery output
- `make package-check` rebuilds the source and wheel distributions and validates them with `twine check`
- `make package-smoke` installs the built wheel into a temporary environment and runs the CLI there
- `make package-source-smoke` installs the built source distribution into a temporary environment and runs the CLI there
- `make docs` verifies that the documentation shell still builds in strict mode

## What `make install` Actually Adds

The local development dependency set currently includes:

- `ruff` for linting
- `mkdocs` plus the Material theme and documentation plugins
- `build` for source and wheel packaging checks

That means a successful `make install` is enough to support linting, tests, builds, and docs work from the same environment.

The repository also checks in `uv.lock` so dependency resolution is explicit and repeatable across machines. When dependency declarations change, refresh the lockfile with `make lock`.

## Expected Result

After these commands:

- `artifacts/.venv/` exists locally
- `artifacts/.venv/bin/python` exists locally
- `uv.lock` matches `pyproject.toml`
- lint passes
- the test suite passes
- source and wheel distributions validate successfully
- the built wheel installs and runs in a temporary environment
- the built source distribution installs and runs in a temporary environment
- the docs site builds successfully

## What This Page Does Not Verify

This page does not prove that:

- network-backed collectors can reach upstream data providers
- the tracked `data/` tree can be rebuilt successfully
- the tracked `docs/report/` tree can be republished successfully
- published report artifacts are up to date with the code and data in the same repository state

Those checks belong to later workflow pages because they mutate more state or depend on more external systems.

## Why Verification Comes Before Data Preparation

The repository should validate the code before pulling or regenerating data. That keeps failures easier to interpret and avoids mixing environment problems with acquisition problems.

## Purpose

This page gives the minimum reliable setup path before any data or report workflow is attempted.

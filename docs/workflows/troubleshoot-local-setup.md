---
title: Troubleshoot Local Setup
audience: mixed
type: troubleshooting
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Troubleshoot Local Setup

Use this page for local setup and publication failures before moving into deeper architecture or source-specific debugging.

## `make install` fails

Check:

- `python3.11 --version`
- `uv --version`
- whether `artifacts/.venv/` is in a broken partial state
- whether `uv.lock` still matches `pyproject.toml`
- whether `pyproject.toml` metadata still installs cleanly with the current lockfile

If needed:

```bash
make clean
make install
make lock-check
```

## `make package-check` fails

Check:

- whether `make build` succeeds first
- whether package metadata still renders cleanly for both source and wheel distributions
- whether `LICENSE` and `NOTICE` are still included through `pyproject.toml`
- whether `twine check` is reporting malformed metadata rather than a missing build artifact

## `make data-prep` is slow

This can be expected when the RAÄ density layer is being rebuilt, because the collector issues repeated RAÄ WFS count queries across Swedish grid cells.

## `make docs` fails

Check:

- missing Markdown pages referenced in navigation
- broken relative links
- files moved without updating `mkdocs.yml`
- warnings emitted by plugins that become hard failures under `strict: true`

## `make docs-serve` fails

Check:

- whether `make install` completed successfully first
- whether port `127.0.0.1:8000` is already in use
- whether the local editable install is blocked by invalid packaging metadata
- whether a stale `artifacts/.venv/` should be removed and rebuilt

## The map opens but some layers are missing

Check:

- whether `make data-prep` completed successfully
- whether `report-multi-country-map` ran after the last data refresh
- whether the copied files exist under `docs/report/nordic-atlas/`

## Docs pages or links look wrong

Check:

- whether `make docs` passes in strict mode
- whether a page was moved without updating `mkdocs.yml`
- whether a link still points to a retired path instead of the durable section names under `foundation/`, `workflows/`, `data-sources/`, `outputs/`, `architecture/`, `engineering/`, and `reference/`

## `make reports` finishes but the atlas does not match expectations

Check:

- whether `make data-prep` ran after the last collector change
- whether `docs/report/nordic-atlas/nordic-atlas_map.html` was regenerated in the same repository state
- whether supporting gallery assets or context artifacts are present where the atlas expects them

## Purpose

This page captures the most likely local setup and publication problems before deeper architecture or reference material is needed.

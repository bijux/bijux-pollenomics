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

The fastest way to troubleshoot is to classify the failure first:

- editable environment creation
- package build or package installation
- docs shell build
- source collection
- report publication

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
artifacts/.venv/bin/bijux-pollenomics --version
make lock-check
```

If the console script still does not run after `make install`, treat that as an environment failure first, not as a collector or report failure.

## `make package-check` fails

Check:

- whether `make build` succeeds first
- whether package metadata still renders cleanly for both source and wheel distributions
- whether `LICENSE` and `NOTICE` are still included through `pyproject.toml`
- whether `twine check` is reporting malformed metadata rather than a missing build artifact

This is the right place to debug build metadata. Do not jump straight to report or docs issues until this passes.

## `make package-verify` fails

Check:

- whether `make package-check` already isolates the failure to package metadata instead of installation
- whether the built wheel starts correctly under `make package-smoke`
- whether the built source distribution starts correctly under `make package-source-smoke`
- whether the editable install already fails under `artifacts/.venv/bin/bijux-pollenomics --version`
- whether a packaging change introduced a mismatch between `pyproject.toml`, `uv.lock`, and the package version exposed in `src/bijux_pollenomics/__init__.py`

Use `make package-check`, `make package-smoke`, and `make package-source-smoke` to isolate which proof surface failed inside the broader packaging workflow.

## `make data-prep` is slow

This can still be expected when upstream sources are slow or large, but the RAÄ collector no longer rebuilds density through repeated live count queries per grid cell. It now archives the published feature inventory first and derives density locally from that snapshot.

## `make data-prep` fails with certificate or TLS verification errors

Check:

- whether the failure comes from an upstream provider with an incomplete certificate chain rather than from local packaging or import errors
- whether you ran `make data-prep` instead of a raw `collect-data` command, because the `Makefile` already enables `BIJUX_POLLENOMICS_ALLOW_INSECURE_TLS=1` for this workflow
- whether a direct CLI run succeeds once you add the same environment variable explicitly
- whether your local network inserts an intercepting proxy or custom certificate authority that changes TLS behavior

If `make data-prep` still fails after that fallback is enabled, treat the failure as an upstream outage or broader network issue rather than as a missing repository shim.

## `make docs` fails

Check:

- missing Markdown pages referenced in navigation
- broken relative links
- files moved without updating `mkdocs.yml`
- warnings emitted by plugins that become hard failures under `strict: true`

## `make docs-serve` fails

Check:

- whether `make install` completed successfully first
- whether `artifacts/.venv/bin/bijux-pollenomics --version` succeeds from that environment
- whether port `127.0.0.1:8000` is already in use
- whether the local editable install is blocked by invalid packaging metadata
- whether a stale `artifacts/.venv/` should be removed and rebuilt

## `make check` fails late

Check which stage failed before rerunning everything blindly:

- lock or install failures belong to environment setup
- test failures belong to code or artifact contracts
- docs failures belong to navigation, links, or strict-build warnings
- package failures belong to metadata or installation surfaces

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
- whether a failed report regeneration left the previous published tree in place instead of partially replacing it

## Reading Rule

Use this page to isolate a failure class. Move to [Architecture](../architecture/index.md) only after you know which seam failed, and move to [Data Sources](../data-sources/index.md) only after you know which collector or source artifact is involved.

## Purpose

This page captures the highest-probability local failures in the order that makes them easiest to isolate.

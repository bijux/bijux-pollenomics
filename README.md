# bijux-pollenomics

`bijux-pollenomics` rebuilds a checked-in Nordic evidence workspace from tracked source data and publishes the resulting atlas, country bundles, and documentation from the same repository state.

The fastest way to understand the current product is to open the Nordic Evidence Atlas, then use the docs to trace where each layer and artifact comes from.

## Start Here

- inspect the shared map: [`docs/report/nordic-atlas/nordic-atlas_map.html`](docs/report/nordic-atlas/nordic-atlas_map.html)
- read the canonical docs home: [`docs/index.md`](docs/index.md)
- verify a fresh checkout: [`docs/workflows/install-and-verify.md`](docs/workflows/install-and-verify.md)
- rebuild tracked data: [`docs/workflows/rebuild-data-tree.md`](docs/workflows/rebuild-data-tree.md)
- republish checked-in outputs: [`docs/workflows/publish-report-artifacts.md`](docs/workflows/publish-report-artifacts.md)

## What This Repository Produces

Today, the checked-in repository produces four durable outcomes:

- a tracked `data/` tree with six source categories and normalized outputs
- the Nordic Evidence Atlas bundle under `docs/report/nordic-atlas/`
- country-level AADR report bundles for Sweden, Norway, Finland, and Denmark
- a MkDocs documentation site that builds into `artifacts/root/docs/site/`

## Current Scope

The current repository scope is deliberately narrower than later site-selection research.

What exists today:

- AADR is used from public `.anno` metadata files
- boundaries, LandClim, Neotoma, SEAD, and RAÄ are collected into tracked `data/` subtrees
- report bundles and the shared atlas are rebuilt from local commands and checked in
- the shared map is a publication artifact for inspection, not an analysis engine

What does not exist today:

- AADR genotype processing from `.geno`, `.ind`, or `.snp`
- lake-intersection analysis
- archaeological-site scoring or ranking
- automated sampling recommendations

## Working With Commands

The root `Makefile` is the main local interface. Some targets only validate the checkout, while others rewrite tracked files.

Validation-first targets:

- `make install` creates or updates the editable environment under `artifacts/.venv/`
- `make lock-check`, `make lint`, `make test`, `make api`, `make docs`, `make package-verify`, and `make check` verify the repository without rewriting tracked data or report outputs

State-changing targets:

- `make lock` rewrites `uv.lock`
- `make data-prep` rewrites tracked source outputs under `data/`
- `make reports` rewrites tracked publication outputs under `docs/report/`
- `make app-state` runs the full rebuild path and rewrites tracked data, tracked reports, and the local docs build

If your goal is only to validate the repository, stop at the verification targets and do not start with `make app-state`.

## Quick Start

### Verify A Fresh Checkout

Prerequisites: `python3.11` and `uv` must be available locally.

```bash
python3.11 --version
uv --version
make install
artifacts/.venv/bin/bijux-pollenomics --version
make lock-check
make lint
make test
make package-verify
make docs
```

This is the safest first run because it proves the editable environment, test surface, packaging surface, and docs build before any tracked data or report tree is regenerated.

### Rebuild The Checked-In Repository State

Use the explicit sequence when you want reviewable rebuild steps:

```bash
make data-prep
make reports
make docs
```

Use `make app-state` when you want that same sequence as a single convenience target.

Expect the rebuild path to take longer than lint and tests, to require network access, and to overwrite generated files that are intentionally checked in.

## Common Workflows

- `make install` syncs the editable environment from the tracked `uv.lock`
- `make check` runs the main repository verification pass: lock check, lint, tests, docs, and distribution verification
- `make data-prep` runs `collect-data all --version v62.0 --output-root data`
- `make reports` runs `publish-reports --aadr-root data/aadr --version v62.0 --output-root docs/report --context-root data`
- `make app-state` runs the full rebuild path: data, reports, and docs
- `make docs-serve` serves the docs locally at `http://127.0.0.1:8000/`
- `make clean` removes transient virtualenv, packaging, and cache artifacts

For exact CLI expansions, narrower test targets, and package troubleshooting targets, use [`docs/reference/command-reference.md`](docs/reference/command-reference.md).

The narrower verification and packaging targets remain available when you need them: `make test-unit`, `make test-regression`, `make test-e2e`, `make package-check`, `make package-smoke`, and `make package-source-smoke`.

## Repository Layout

Treat the top-level paths by ownership and review expectations:

- `Makefile` is the main local interface for verification, rebuilds, docs, and packaging
- `pyproject.toml` and `uv.lock` define and lock the Python environment
- `data/` contains tracked source snapshots, normalized outputs, and the collection manifest
- `docs/report/` contains tracked publication artifacts, including the shared atlas and country bundles
- `docs/` contains the canonical narrative and reference documentation that explains the checked-in outputs
- `packages/bijux-pollenomics/src/` contains the CLI, collectors, and report publishing logic
- `packages/bijux-pollenomics/tests/` contains unit, regression, and end-to-end coverage
- `artifacts/` contains transient local outputs such as `.venv/`, `dist/`, and the built docs site

Key checked-in contract files:

- `packages/bijux-pollenomics/src/bijux_pollenomics/config.py` centralizes publication defaults such as the current AADR version
- `apis/bijux-pollenomics/v1/` contains the checked-in public API contract, pinned canonical JSON, and schema digest
- `packages/bijux-pollenomics/src/bijux_pollenomics/data_downloader/contracts.py` and `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/paths.py` centralize file and directory naming contracts

## Published Outputs

The main checked-in publication artifacts are:

- Nordic Evidence Atlas: [`docs/report/nordic-atlas/nordic-atlas_map.html`](docs/report/nordic-atlas/nordic-atlas_map.html)
- shared Nordic report index: [`docs/report/nordic-atlas/README.md`](docs/report/nordic-atlas/README.md)
- published report manifest: [`docs/report/published_reports_summary.json`](docs/report/published_reports_summary.json)
- data collection manifest: [`data/collection_summary.json`](data/collection_summary.json)
- country bundles under `docs/report/sweden/`, `docs/report/norway/`, `docs/report/finland/`, and `docs/report/denmark/`

Important output limits:

- the shared map is an inspectable publication artifact, not a site-selection engine
- the published map bundles local Leaflet assets, but basemap tiles still come from external providers at runtime
- RAÄ coverage is Sweden-only
- country reports are file bundles and summaries, not standalone web applications

## Documentation

The canonical project documentation lives in `docs/` and is built with MkDocs.

Useful entry points:

- docs home: [`docs/index.md`](docs/index.md)
- API governance: [`docs/bijux-pollenomics/api-and-schema-governance.md`](docs/bijux-pollenomics/api-and-schema-governance.md)
- product overview: [`docs/foundation/product-overview.md`](docs/foundation/product-overview.md)
- data guide: [`docs/data-sources/index.md`](docs/data-sources/index.md)
- install and verify workflow: [`docs/workflows/install-and-verify.md`](docs/workflows/install-and-verify.md)
- report publishing workflow: [`docs/workflows/publish-report-artifacts.md`](docs/workflows/publish-report-artifacts.md)
- atlas and report outputs guide: [`docs/outputs/index.md`](docs/outputs/index.md)
- command reference: [`docs/reference/command-reference.md`](docs/reference/command-reference.md)

## Working Rules

These behaviors matter in review:

- collectors replace source-specific output directories before rewriting them, so reruns are intentionally destructive to stale generated files
- `data/` and `docs/report/` are tracked outputs that should change only when the corresponding rebuild intent is explicit
- `artifacts/` is disposable local state and should not be treated as a publication surface
- this README should describe only commands, outputs, and limits that exist in the current repository state
- if a change rewrites generated artifacts, review those diffs together with any narrative or workflow updates that explain them

## License

This repository is licensed under the Apache License 2.0. Copyright 2026 Bijan Mousavi <bijan@bijux.io>. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).

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
- a MkDocs documentation site that builds into `artifacts/docs/site/`

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

## Repository Layout

The main checked-in areas are:

```text
.
├── data/
│   ├── aadr/
│   ├── boundaries/
│   ├── landclim/
│   ├── neotoma/
│   ├── raa/
│   └── sead/
├── docs/
│   ├── report/
│   └── ...
├── src/
├── tests/
└── artifacts/
```

Use this distinction when working in the repo:

- `data/` contains tracked source inputs and normalized source outputs
- `docs/report/` contains tracked published report and map bundles
- `artifacts/` contains transient local build outputs such as `.venv/`, `dist/`, and the built docs site
- `src/bijux_pollenomics/settings.py` centralizes the checked-in publication defaults
- `src/bijux_pollenomics/data_downloader/contracts.py` and `src/bijux_pollenomics/reporting/paths.py` centralize file-contract names

## Working With Commands

The root `Makefile` is the main local interface. Some targets only validate the checkout, while others rewrite tracked files.

Validation-first targets:

- `make install` creates or updates the editable environment under `artifacts/.venv/`
- `make lock-check`, `make lint`, `make test`, `make docs`, `make package-verify`, and `make check` verify the repository without rewriting tracked data or report outputs

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

## Operational Notes

These points are easy to miss and matter in review:

- collectors replace source-specific output directories before rewriting them, so reruns are intentionally destructive to stale generated files
- `docs/report/` is not a scratch directory; it is a tracked publication tree that should change only when report outputs actually change
- the shared Nordic HTML map carries local Leaflet assets, but its basemap tiles still come from external services at runtime
- the checked-in map is an inspectable publication artifact, not an authenticated web application or an analysis backend

## Published Outputs

The main checked-in publication artifacts are:

- Nordic Evidence Atlas: [`docs/report/nordic-atlas/nordic-atlas_map.html`](docs/report/nordic-atlas/nordic-atlas_map.html)
- shared Nordic report index: [`docs/report/nordic-atlas/README.md`](docs/report/nordic-atlas/README.md)
- published report manifest: [`docs/report/published_reports_summary.json`](docs/report/published_reports_summary.json)
- data collection manifest: [`data/collection_summary.json`](data/collection_summary.json)

Country bundles currently exist for:

- Sweden
- Norway
- Finland
- Denmark

## Map Notes

The shared map is an interactive publication artifact built from tracked outputs in this repository.

Important limits:

- it shows collected and normalized evidence layers; it does not decide where sampling should happen
- it bundles local Leaflet and marker-cluster assets in the published map directory
- it still depends on external basemap tiles at runtime, so full map display is not completely offline
- RAÄ coverage is Sweden-only

## Documentation

The canonical project documentation lives in `docs/` and is built with MkDocs.

- local docs build target: `make docs`
- local docs serve target: `make docs-serve`
- deploy workflow: [`.github/workflows/deploy-docs.yml`](.github/workflows/deploy-docs.yml)
- docs homepage source: [`docs/index.md`](docs/index.md)

Useful entry points:

- data guide: [`docs/data-sources/index.md`](docs/data-sources/index.md)
- reports guide: [`docs/outputs/index.md`](docs/outputs/index.md)
- local workflow: [`docs/engineering/local-workflow.md`](docs/engineering/local-workflow.md)
- command reference: [`docs/reference/command-reference.md`](docs/reference/command-reference.md)

## Honesty Notes

This README tries to describe only the repo behavior that exists today.

- If a command is not in the `Makefile` or CLI, this README should not imply it exists.
- If an output is not checked in or reproducibly generated here, this README should not present it as available.
- Scientific goals for later work belong in the docs as future direction, not as claims about current functionality.

# bijux-pollenomics

`bijux-pollenomics` is a repository for collecting tracked Nordic context datasets and publishing checked-in map and report outputs from them.

Today, this repository does four concrete things:

- collects six tracked data categories under `data/`
- generates one shared Nordic map bundle under `docs/report/nordic/`
- generates country-level AADR report bundles for Sweden, Norway, Finland, and Denmark
- builds a MkDocs documentation site under `artifacts/docs/site/`

It does not yet rank candidate sampling locations, compute lake intersections, or produce automated site-selection scores.

## What Running Commands Changes

This repository has both verification commands and state-changing commands.

- `make install`, `make lint`, `make test`, and `make docs` validate or build local artifacts
- `make data-prep` rewrites tracked source snapshots and normalized outputs under `data/`
- `make reports` rewrites checked-in report artifacts under `docs/report/`
- `make app-state` does the full current rebuild path and will rewrite both tracked data and tracked report artifacts

Use that distinction deliberately. A fresh contributor who only wants to verify the codebase should not start with the full rebuild command.

## Current Scope

The current checked-in scope is deliberately narrow:

- AADR is used from public `.anno` metadata files
- boundaries, LandClim, Neotoma, SEAD, and RAÄ are collected into tracked `data/` subtrees
- published outputs are rebuilt from local commands and kept in the repository
- the shared map is a publication artifact, not an analysis engine

The repository does not currently:

- ingest AADR genotype matrices such as `.geno`, `.ind`, or `.snp`
- perform lake-distance intersection analysis
- perform archaeological-site scoring
- infer scientific conclusions from proximity alone

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

## Quick Start

### Verify The Environment First

Prerequisite: `python3.11` must be available locally.

```bash
make install
make lint
make test
```

That path is the safest first run because it validates the local environment before any network-heavy or state-changing data workflow.

### Rebuild The Current Checked-In State

Prerequisite: `python3.11` must be available locally.

```bash
make app-state
```

That sequence does the full current rebuild path:

1. creates the local virtual environment under `artifacts/.venv/`
2. rebuilds the tracked `data/` tree
3. republishes the checked-in map and report bundles under `docs/report/`
4. rebuilds the MkDocs site under `artifacts/docs/site/`

Expect this path to take longer than lint and tests, to require network access, and to overwrite generated files that are intentionally checked in.

## Main Commands

The root `Makefile` is the main local interface:

```bash
make install
make data-prep
make reports
make app-state
make lint
make test
make check
make docs
make docs-serve
make build
make clean
```

What they do:

- `make data-prep` runs `collect-data all --version v62.0 --output-root data`
- `make reports` regenerates the current checked-in shared map and country bundles under `docs/report/`
- `make app-state` runs the full current rebuild path: data, reports, and docs
- `make check` runs the repository verification pass: lint, tests, and docs
- `make docs-serve` serves the docs locally at `http://127.0.0.1:8000/`

## Operational Notes

These points are easy to miss and matter in review:

- collectors replace source-specific output directories before rewriting them, so reruns are intentionally destructive to stale generated files
- `docs/report/` is not a scratch directory; it is a tracked publication tree that should change only when report outputs actually change
- the shared Nordic HTML map carries local Leaflet assets, but its basemap tiles still come from external services at runtime
- the checked-in map is an inspectable publication artifact, not an authenticated web application or an analysis backend

## Published Outputs

The main checked-in publication artifacts are:

- Nordic Evidence Atlas: [`docs/report/nordic/nordic_aadr_v62.0_map.html`](docs/report/nordic/nordic_aadr_v62.0_map.html)
- shared Nordic report index: [`docs/report/nordic/README.md`](docs/report/nordic/README.md)
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

- data guide: [`docs/03-data-guide/index.md`](docs/03-data-guide/index.md)
- reports guide: [`docs/04-reports/index.md`](docs/04-reports/index.md)
- local workflow: [`docs/06-development/local-workflow.md`](docs/06-development/local-workflow.md)
- command reference: [`docs/07-reference/command-surface.md`](docs/07-reference/command-surface.md)

## Honesty Notes

This README tries to describe only the repo behavior that exists today.

- If a command is not in the `Makefile` or CLI, this README should not imply it exists.
- If an output is not checked in or reproducibly generated here, this README should not present it as available.
- Scientific goals for later work belong in the docs as future direction, not as claims about current functionality.

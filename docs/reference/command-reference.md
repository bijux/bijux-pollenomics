---
title: Command Reference
audience: mixed
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Command Reference

## Verification And Local Build Commands

```bash
artifacts/.venv/bin/bijux-pollenomics --version
make install
make lock
make lock-check
make lint
make test
make docs
make docs-serve
make build
make package-check
make package-smoke
make package-source-smoke
make check
```

These commands create or validate local artifacts. They do not recollect source data unless you explicitly invoke the data or report workflows below.

## Data Collection Commands

```bash
artifacts/.venv/bin/bijux-pollenomics collect-data all --version v62.0 --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data aadr --version v62.0 --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data boundaries --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data landclim --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data neotoma --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data raa --output-root data
artifacts/.venv/bin/bijux-pollenomics collect-data sead --output-root data
```

These commands rewrite tracked source outputs under `data/`.

## Report Commands

```bash
artifacts/.venv/bin/bijux-pollenomics report-multi-country-map Sweden Norway Finland Denmark --version v62.0 --name nordic-atlas --title "Nordic Evidence Atlas" --context-root data
artifacts/.venv/bin/bijux-pollenomics publish-reports --aadr-root data/aadr --version v62.0 --output-root docs/report --context-root data
artifacts/.venv/bin/bijux-pollenomics report-country Sweden --version v62.0 --shared-map-label "Nordic Evidence Atlas" --shared-map-path "../nordic-atlas/nordic-atlas_map.html"
artifacts/.venv/bin/bijux-pollenomics report-country Norway --version v62.0 --shared-map-label "Nordic Evidence Atlas" --shared-map-path "../nordic-atlas/nordic-atlas_map.html"
artifacts/.venv/bin/bijux-pollenomics report-country Finland --version v62.0 --shared-map-label "Nordic Evidence Atlas" --shared-map-path "../nordic-atlas/nordic-atlas_map.html"
artifacts/.venv/bin/bijux-pollenomics report-country Denmark --version v62.0 --shared-map-label "Nordic Evidence Atlas" --shared-map-path "../nordic-atlas/nordic-atlas_map.html"
```

These commands rewrite checked-in report outputs under `docs/report/`.

## Make Targets That Change Tracked State

```bash
make data-prep
make reports
make app-state
```

Use these only when you intend to regenerate tracked data or tracked publication artifacts.

## Notes

- `make data-prep` expands to `collect-data all --version v62.0 --output-root data`
- `make reports` expands to `publish-reports --aadr-root data/aadr --version v62.0 --output-root docs/report --context-root data`
- `make app-state` expands to `make data-prep`, `make reports`, and `make docs`
- `make check` expands to `make lock-check`, `make lint`, `make test`, `make docs`, and `make package-check`
- `make install` syncs the local environment under `artifacts/.venv/` from `uv.lock`
- `make lock` refreshes `uv.lock` from `pyproject.toml`
- `make lock-check` verifies that `uv.lock` matches `pyproject.toml`
- `make build` writes distributions into `artifacts/dist/`
- `make package-smoke` installs the built wheel into a temporary environment and runs the CLI there
- `make package-source-smoke` installs the built source distribution into a temporary environment and runs the CLI there
- `make reports` is the canonical `make` target for regenerating the checked-in report bundles
- `make docs-serve` expects a healthy editable install and serves the site at `http://127.0.0.1:8000/`
- `report-country` requires `--shared-map-label` and `--shared-map-path` together when you want a shared-map link in the generated README
- `report-multi-country-map` builds only the shared map bundle; `publish-reports` builds the shared map plus country bundles

## Purpose

This page centralizes the checked-in command surface in one place.

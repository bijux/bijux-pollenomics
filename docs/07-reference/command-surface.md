---
title: Command Surface
audience: mixed
type: reference
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Command Surface

## Data Collection

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli collect-data all --version v62.0 --output-root data
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli collect-data aadr --version v62.0 --output-root data
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli collect-data boundaries --output-root data
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli collect-data neotoma --output-root data
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli collect-data raa --output-root data
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli collect-data sead --output-root data
```

## Reports

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli report-multi-country-map Sweden Norway Finland Denmark --version v62.0 --name nordic --title "Nordic Countries" --context-root data
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli report-country Sweden --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli report-country Norway --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli report-country Finland --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli report-country Denmark --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
```

## Local Workflow

```bash
make install
make clean
make lint
make test
make data-prep
make build
make docs
make docs-serve
```

## Notes

- `make data-prep` expands to `collect-data all --version v62.0 --output-root data`
- `make install` creates the local environment under `artifacts/.venv/`
- `make build` writes distributions into `artifacts/dist/`
- there is currently no `make` target that regenerates the report bundles; use the explicit CLI commands above

## Purpose

This page centralizes the checked-in command surface in one place.

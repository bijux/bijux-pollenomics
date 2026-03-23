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
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data all --version v62.0 --output-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data aadr --version v62.0 --output-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli collect-data raa --output-root data
```

## Reports

```bash
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli report-multi-country-map Sweden Norway Finland Denmark --version v62.0 --name nordic --title "Nordic Countries" --context-root data
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli report-country Sweden --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
```

## Local Workflow

```bash
make install
make lint
make test
make data-prep
make build
make docs
make docs-serve
```

## Purpose

This page centralizes the checked-in command surface in one place.

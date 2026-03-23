---
title: Country Reports
audience: mixed
type: explanation
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Country Reports

Country reports summarize AADR samples for one political entity.

## Current Published Countries

- Sweden
- Norway
- Finland
- Denmark

## What Each Country Bundle Contains

- `README.md`
- `*_samples.csv`
- `*_localities.csv`
- `*_samples.geojson`
- `*_samples.md`

## What They Do Not Contain

Country bundles do not contain their own standalone HTML map. They link back to the shared Nordic map when that link is provided during generation.

## Why Country Reports Exist Alongside The Shared Map

The map is good for exploration, but country reports are better for:

- exact sample inventories
- locality-level aggregation
- quick country-specific review without filtering the shared map
- stable file artifacts for git review

## Generation Command

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollen.cli report-country Sweden --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
```

The same command pattern is used for Norway, Finland, and Denmark in the current checked-in outputs.

## Purpose

This page explains why country reports remain first-class outputs even after the move to one shared map.

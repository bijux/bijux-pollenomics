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

## Why Country Reports Exist Alongside The Shared Map

The map is good for exploration, but country reports are better for:

- exact sample inventories
- locality-level aggregation
- quick country-specific review without filtering the shared map
- stable file artifacts for git review

## Generation Command

```bash
PYTHONPATH=src .venv/bin/python -m bijux_pollen.cli report-country Sweden --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
```

## Purpose

This page explains why country reports remain first-class outputs even after the move to one shared map.

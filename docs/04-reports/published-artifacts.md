---
title: Published Artifacts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-23
---

# Published Artifacts

The `docs/report/` tree contains checked-in report artifacts used both for review and for MkDocs-hosted documentation.

## Shared Map Bundle

The currently checked-in shared bundle is `docs/report/nordic/`. It includes:

- a combined sample GeoJSON
- the interactive HTML map
- a machine-readable summary JSON
- bundled map UI assets under `_map_assets/`
- copied Neotoma, SEAD, boundaries, and RAÄ map assets
- a short bundle README

## Country Bundles

The currently checked-in country bundles are:

- `docs/report/sweden/`
- `docs/report/norway/`
- `docs/report/finland/`
- `docs/report/denmark/`

Each country bundle includes:

- a summary README
- a machine-readable summary JSON
- sample-level CSV
- locality-level CSV
- sample GeoJSON
- full Markdown sample inventory

## Why These Are Checked In

Checked-in report outputs make it easier to:

- review changes in git
- verify that generated artifacts still match the source tree
- publish the map and summary pages through MkDocs without an additional deployment pipeline

## What This Page Is Not

This page documents the current checked-in artifact policy. It is not a promise that every future output type will live under `docs/report/`.

## Purpose

This page explains the checked-in output policy for the report tree.

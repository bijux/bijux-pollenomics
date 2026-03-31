---
title: Published Artifacts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Published Artifacts

The `docs/report/` tree contains checked-in report artifacts used both for review and for MkDocs-hosted documentation.

These artifacts are generated outputs. They are not maintained by hand.

Narrative pages under `docs/outputs/` explain those artifacts, but they are not themselves generated bundle files.

## Nordic Evidence Atlas Bundle

The checked-in Nordic Evidence Atlas bundle is `docs/report/nordic-atlas/`. It includes:

- a combined sample GeoJSON
- the interactive HTML map
- a machine-readable summary JSON
- bundled map UI assets under `_map_assets/`
- copied LandClim, Neotoma, SEAD, boundaries, and RAÄ map assets
- a short bundle README

The shared bundle is the only place where the interactive HTML map lives.

## Country Bundles

The checked-in country bundles are:

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

Country bundles intentionally stay file-oriented and map-light. They summarize one political entity and link back to the shared map instead of embedding a second standalone map application.

## Why These Are Checked In

Checked-in report outputs make it easier to:

- review changes in git
- verify that generated artifacts still match the source tree
- publish the map and summary pages through MkDocs without an additional deployment pipeline

## Review Rule

When a change affects `docs/report/`, reviewers should assume that:

- HTML, JSON, CSV, and GeoJSON diffs may all be meaningful
- generated text inside bundle `README.md` files is part of the artifact contract
- artifact changes are only trustworthy when they can be tied back to source or code changes in the same repository state

The practical consequence is that reviewers should read `docs/outputs/` pages and `docs/report/` diffs together when output behavior changes.

## What This Page Is Not

This page documents the checked-in artifact policy. It is not a promise that every future output type will live under `docs/report/`.

## Purpose

This page explains the checked-in output policy for the report tree.

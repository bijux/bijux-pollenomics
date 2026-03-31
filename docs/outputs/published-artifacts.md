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

Publication writes these bundles into a staging tree first and swaps that tree into `docs/report/` only after generation succeeds.

That staging step is an implementation detail. The checked-in summary JSON files inside the published bundles should always record the final `docs/report/...` output paths rather than hidden staging directories.

## Artifact Contract

Treat the `docs/report/` tree as a published file contract:

- bundle `README.md` files are generated artifacts, not hand-maintained docs
- summary JSON files are part of the machine-readable publication surface
- copied GeoJSON, CSV, Markdown, and HTML files are all reviewable outputs
- narrative pages under `docs/outputs/` explain this tree but are not themselves part of the generated bundle contract

## Nordic Evidence Atlas Bundle

The checked-in Nordic Evidence Atlas bundle is `docs/report/nordic-atlas/`. It includes:

- a combined sample GeoJSON
- the interactive HTML map
- a machine-readable summary JSON
- bundled map UI assets under `_map_assets/`
- copied LandClim, Neotoma, SEAD, boundaries, and RAÄ layer files used by the shared map
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

## Review Rule

When a change affects `docs/report/`, reviewers should assume that:

- HTML, JSON, CSV, GeoJSON, and generated README diffs may all be meaningful
- `output_dir` and sibling path fields inside summary JSON files should point at the final `docs/report/...` output paths, not at hidden `.tmp` directories
- artifact changes are only trustworthy when they can be tied back to source or code changes in the same repository state

The practical consequence is that reviewers should read `docs/outputs/` pages and `docs/report/` diffs together when output behavior changes.

If a report build fails before the staged swap completes, the previously published `docs/report/` tree should remain intact.

## Why These Are Checked In

Checked-in report outputs make it easier to:

- review changes in git
- verify that generated artifacts still match the source tree
- publish the map and summary pages through MkDocs without an additional deployment pipeline

## What This Page Is Not

This page documents the checked-in artifact policy. It is not a promise that every future output type will live under `docs/report/`.

## Purpose

This page explains the checked-in output policy for the report tree.

---
title: Provenance and Refresh Policy
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Provenance and Refresh Policy

The repository treats source collection as a documented, reviewable ingest process.

## What Every Source Refresh Should Preserve

- a stable top-level source root under `data/<source>/`
- enough raw upstream material to audit the normalized outputs later
- normalized outputs that are safe for downstream reports and the shared atlas
- machine-readable provenance or summary artifacts when the upstream source is mutable

## Raw And Normalized Contract

The general expectation is:

- `raw/` keeps upstream files, inventories, manifests, or archives that explain what was fetched
- `normalized/` keeps repository-specific outputs that the atlas, reports, or later tooling depend on

`aadr` is the main exception because the tracked `.anno` files already are the durable input contract used by the repository.

Because the repository has older checked-in snapshots as well as newer refreshed ones, not every current source directory exposes the full latest manifest set yet. The refresh contract on this page describes what future recollection should preserve so those older snapshots can be brought forward deliberately instead of being silently reinterpreted.

## Refresh Rule

Refreshing a source snapshot is not just “download again”.

A source refresh should:

1. resolve the intended upstream records or release assets explicitly
2. write or update auditable raw artifacts
3. replace stale normalized outputs for that source
4. leave behind enough metadata to explain what changed

## Review Rule

When a source snapshot changes, reviewers should be able to answer:

- which upstream endpoint, release, or asset set produced the new files
- whether the raw inventory and normalized outputs still match each other
- whether the resulting atlas or report changes are explained by the source refresh

## Why This Matters

Without an explicit provenance rule, a checked-in data tree becomes hard to trust over multi-year work. The repository is meant to support long-lived spatial interpretation, so collection history and normalization history need to stay inspectable instead of being collapsed into one opaque refresh step.

## Purpose

This page records the provenance and refresh contract shared by all tracked data sources.

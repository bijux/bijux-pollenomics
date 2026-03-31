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

The goal is not just to fetch files again. The goal is to leave behind enough evidence that a later reviewer can explain where the refreshed snapshot came from and why the downstream outputs changed.

## What Every Source Refresh Should Preserve

- a stable top-level source root under `data/<source>/`
- enough raw upstream material to audit the normalized outputs later
- normalized outputs that are safe for downstream reports and the shared atlas
- machine-readable provenance or summary artifacts when the upstream source is mutable

## Refresh Contract

A source refresh should preserve four facts:

1. what upstream release, endpoint, or asset set was targeted
2. which raw files or inventories were kept for later audit
3. which normalized outputs now define the repository-facing contract
4. which generated atlas or report changes should be expected downstream

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

## Why Summary Files Matter

The collector summary and source-specific manifests are not side notes. They are the machine-readable bridge between a refresh command and the changed repository tree. Without them, later review turns into guesswork.

## Why This Matters

Without an explicit provenance rule, a checked-in data tree becomes hard to trust over multi-year work. The repository is meant to support long-lived spatial interpretation, so collection history and normalization history need to stay inspectable instead of being collapsed into one opaque refresh step.

## Reading Rule

Use this page with [Source comparison](source-comparison.md): the comparison page tells you why a source matters, and this page tells you what a refresh of that source has to preserve.

## Purpose

This page records the provenance and refresh contract shared by all tracked data sources.

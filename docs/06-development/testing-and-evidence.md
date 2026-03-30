---
title: Testing and Evidence
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Testing and Evidence

The repository uses lightweight Python tests plus generated artifacts as evidence.

## Current Evidence Types

- unittest coverage for collection, normalization, and report generation logic
- checked-in `data/` source outputs
- checked-in `data/collection_summary.json`
- checked-in `docs/report/` outputs
- checked-in report summary JSON files
- explicit file-contract tests for normalized data paths, report bundle paths, and vendored map assets
- successful `make lint`, `make test`, `make build`, and `make docs`
- a combined `make check` run for one-command repository verification

## Why Generated Artifacts Matter

The project is output-heavy. A change that preserves test behavior but silently changes the generated map or report assets can still be important, so artifact diffs are part of normal review.

## Purpose

This page explains how evidence is gathered for repository changes.

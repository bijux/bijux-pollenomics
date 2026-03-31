---
title: Testing and Evidence
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Testing and Evidence

The repository uses explicit unit, regression, and end-to-end suites plus generated artifacts as evidence.

## Test Suites

- `tests/unit/` covers small logic boundaries and helper contracts
- `tests/regression/` covers generated outputs, artifact contracts, and workflow behavior that should not drift silently
- `tests/e2e/` covers CLI command flows from the user-facing entry point

The `Makefile` exposes these suites directly:

- `make test-unit`
- `make test-regression`
- `make test-e2e`
- `make test` for the full combined suite

## Evidence Types

- unittest coverage for collection, normalization, and report generation logic
- checked-in `data/` source outputs
- checked-in `data/collection_summary.json`
- checked-in `docs/report/` outputs
- checked-in report summary JSON files
- explicit file-contract tests for normalized data paths, report bundle paths, and vendored map assets
- successful `make lint`, `make test`, `make build`, `make package-check`, and `make docs`
- a combined `make check` run for one-command repository verification

## Evidence Matrix

- source-collection changes should leave behind test evidence plus changed `data/` artifacts or summaries
- reporting changes should leave behind test evidence plus changed `docs/report/` artifacts when output behavior moved
- documentation changes should leave behind a successful strict docs build
- packaging or command-surface changes should leave behind the relevant `make` or CLI command evidence, including `make package-check` when distribution metadata or entrypoints changed

## Why Generated Artifacts Matter

The project is output-heavy. A change that preserves test behavior but silently changes the generated map or report assets can still be important, so artifact diffs are part of normal review.

## Review Rule

Do not treat one green command as universal proof. The evidence should match the surface area of the change.

## Purpose

This page explains how evidence is gathered for repository changes.

---
title: Public Imports
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Public Imports

The public import surface is defined by `bijux_pollenomics.__all__`.

## Supported Imports

- report dataclasses such as `CountryReport` and `PublishedReportsReport`
- collection dataclasses such as `DataCollectionReport` and `ContextDataReport`
- top-level workflow functions including `collect_data`,
  `collect_context_data`, `generate_country_report`,
  `generate_multi_country_map`, and `generate_published_reports`
- `__version__`

## Import Guidance

Prefer importing through `bijux_pollenomics` for stable caller-facing code.
Reach into internal modules only when changing the package itself.

## Purpose

This page identifies the import surface that external callers should treat as
stable first.

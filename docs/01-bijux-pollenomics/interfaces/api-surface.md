---
title: API Surface
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# API Surface

The importable API is intentionally small and mirrors the package's major
workflow families.

## Runtime Entry Points

- `collect_data` and `collect_context_data` from `data_downloader.api`
- `generate_country_report`, `generate_multi_country_map`, and
  `generate_published_reports` from `reporting.api`

## Report Types

- `DataCollectionReport`
- `ContextDataReport`
- `CountryReport`
- `MultiCountryMapReport`
- `PublishedReportsReport`

## Frozen API Contract

Repository-level API expectations are pinned under `apis/bijux-pollenomics/v1/`
with `schema.yaml`, `pinned_openapi.json`, and `schema.hash`.

## Purpose

This page names the import and schema surfaces that count as public package API.

---
title: AADR
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# AADR

`data/aadr/` contains the tracked AADR metadata inputs used by the country reports and the shared map.

## Tracked Inputs

- `data/aadr/v62.0/1240k/v62.0_1240k_public.anno`
- `data/aadr/v62.0/ho/v62.0_HO_public.anno`

## Why Only `.anno`

The current repository logic needs:

- genetic IDs
- locality names
- political entity values
- latitude and longitude
- publication and date fields

Those fields are already in the public `.anno` files, so tracking the heavier genotype matrices would increase repository weight without helping the current report or map workflow.

## Collector Contract

The collector resolves the requested `.anno` files from the public AADR Harvard Dataverse version history and writes them into:

- `data/aadr/v62.0/1240k/v62.0_1240k_public.anno`
- `data/aadr/v62.0/ho/v62.0_HO_public.anno`

It also writes a release manifest with the Dataverse version number, release timestamps, file identifiers, and local paths, and it verifies downloaded payloads against the upstream `filesize` and `md5` metadata before keeping them.

The repository does not currently collect or use `.geno`, `.ind`, `.snp`, or spreadsheet companions.

## Audit Artifacts

- release manifests under `data/aadr/<version>/`
- one tracked `.anno` file per requested AADR dataset
- AADR versioned paths that make the checked-in source release explicit

## Acquisition Command

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollenomics.cli collect-data aadr --version v62.0 --output-root data
```

## Role In The Product

```mermaid
flowchart LR
    AADR[AADR .anno files] --> CountryReports[Country reports]
    AADR --> SharedMap[Shared Nordic map]
    AADR --> LocalitySummaries[Locality summaries]
```

## Purpose

This page explains why AADR is tracked as metadata-first input rather than as a full genotype repository.

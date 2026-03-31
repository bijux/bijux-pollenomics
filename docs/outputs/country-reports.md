---
title: Country Reports
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Country Reports

Country reports summarize AADR samples for one political entity.

They are intentionally narrower than the shared map. A country report is the durable inventory view for one country, not a second evidence-comparison surface.

## Published Countries

- Sweden
- Norway
- Finland
- Denmark

## What Each Country Bundle Contains

- `README.md`
- `*_summary.json`
- `*_samples.csv`
- `*_localities.csv`
- `*_samples.geojson`
- `*_samples.md`

## Why They Stay Separate From The Atlas

Country bundles exist because file-oriented review and country-specific inventory work are different jobs from multi-layer exploration in the shared atlas.

- use a country bundle when you need exact sample inventories or locality groupings
- use the atlas when you need cross-source visual comparison, context layers, or multi-country filtering

## What They Do Not Contain

Country bundles do not contain their own standalone HTML map. They link back to the shared Nordic map when that link is provided during generation.

They also do not include contextual layers such as LandClim, Neotoma, SEAD, boundaries, or RAÄ as standalone bundle files. Those remain part of the shared map bundle.

## Why Country Reports Exist Alongside The Shared Map

The map is good for exploration, but country reports are better for:

- exact sample inventories
- locality-level aggregation
- quick country-specific review without filtering the shared map
- stable file artifacts for git review

## Review Rule

Read country bundles as release-scoped AADR inventory outputs. They are not evidence-complete summaries of every contextual source used elsewhere in the repository, and they should not be reviewed as if they were mini atlases.

## Honesty Rule

Country reports should be read as AADR inventory outputs for one country in one release. They are not evidence-complete summaries of every contextual source used elsewhere in the repository.

## Empty-Match Behavior

If a requested country has zero matching AADR samples in the selected release, the generator still writes a complete bundle with empty inventories and an explicit zero-count summary instead of crashing.

## Generation Command

```bash
artifacts/.venv/bin/bijux-pollenomics report-country Sweden --version v62.0 --shared-map-label "Nordic Evidence Atlas" --shared-map-path "../nordic-atlas/nordic-atlas_map.html"
```

The same command pattern is used for Norway, Finland, and Denmark in the checked-in outputs.

## Purpose

This page explains why country reports remain first-class generated artifacts even after the move to one shared atlas.

---
title: Product Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# Product Overview

`bijux-pollenomics` builds a Nordic evidence workspace for inspecting where tracked aDNA, pollen-related, environmental archaeology, and archaeology layers occur together.

The checked-in workspace combines:

- ancient DNA sample locations from AADR
- Nordic pollen and paleoecology locations from Neotoma
- Nordic environmental archaeology locations from SEAD
- Swedish archaeology coverage from RAÄ / Fornsök
- country boundaries used to filter all compatible layers consistently

```mermaid
mindmap
  root((bijux-pollenomics))
    AADR
      aDNA points
      country reports
    Neotoma
      pollen sites
    SEAD
      environmental archaeology
    RAÄ
      Sweden archaeology density
    Boundaries
      country filters
      map framing
```

The repository is not just a static report dump. It is a file-oriented pipeline that:

1. collects tracked source inputs
2. normalizes them into a common geospatial shape
3. generates country reports
4. generates a shared Nordic map that can filter layers by country

The longer-term research goal is to use those layers as one input to later site-selection work. The repository does not rank sites or recommend field locations automatically.

## Intended Readers

- researchers who need to inspect the evidence surface before designing new spatial analysis
- maintainers who need to rebuild the checked-in state and publish outputs reproducibly
- reviewers who need to verify that a visible atlas or report change is grounded in tracked data and code

## Why The Map Is Central

The map is the fastest way to validate whether the repository is producing interpretable spatial structure:

- are the points in the right countries
- do archaeology and pollen layers appear where expected
- can readers filter the evidence set down to one country
- can researchers inspect the current checked-in evidence without reading raw tables first

That is why the docs homepage embeds the shared map before anything else.

## Durable Outputs

- tracked source inputs under `data/`
- normalized data products under `data/*/normalized/`
- country report bundles under `docs/report/<country>/`
- a shared Nordic interactive map under `docs/report/nordic-atlas/`

## Purpose

This page explains the product outcome of the repository so later workflow and architecture pages are read with the right expectations.

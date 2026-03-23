---
title: What bijux-pollen Does
audience: mixed
type: explanation
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# What bijux-pollen Does

`bijux-pollen` prepares a Nordic evidence surface for choosing pollenomic sampling locations.

Today that evidence surface combines:

- ancient DNA sample locations from AADR
- Nordic pollen and paleoecology locations from Neotoma
- Nordic environmental archaeology locations from SEAD
- Swedish archaeology coverage from RAÄ / Fornsök
- country boundaries used to filter all compatible layers consistently

```mermaid
mindmap
  root((bijux-pollen))
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

The repository is not just a static report dump. It is a reproducible pipeline that:

1. downloads tracked source inputs
2. normalizes them into a common geospatial shape
3. generates country reports
4. generates a shared Nordic map that can filter layers by country

The longer-term goal is to use those layers to identify places where pollen, archaeology, and ancient biomolecular evidence overlap closely enough to justify field sampling.

## Why The Map Is Central

The map is the fastest way to validate whether the repository is producing useful spatial structure:

- are the points in the right countries
- do archaeology and pollen layers appear where expected
- can readers filter the evidence set down to one country
- can researchers inspect candidate areas without reading raw tables first

That is why the docs homepage embeds the shared map before anything else.

## Current Durable Outputs

- tracked source inputs under `data/`
- normalized data products under `data/*/normalized/`
- country report bundles under `docs/report/<country>/`
- a shared Nordic interactive map under `docs/report/nordic/`

## Purpose

This page explains the product outcome of the repository so later workflow and architecture pages are read with the right expectations.

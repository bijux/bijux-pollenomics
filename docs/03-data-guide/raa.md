---
title: RAÄ
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-03-31
---

# RAÄ

`data/raa/` contains Swedish archaeology metadata and a map-optimized archaeology density layer derived from RAÄ / Fornsök.

## What It Produces

- raw capabilities, schema, and domain metadata under `data/raa/raw/`
- Swedish archaeology metadata and density GeoJSON under `data/raa/normalized/`

## What The Current Collector Does

The current collector:

- downloads RAÄ WFS capabilities and schema metadata
- downloads Fornsök domain metadata
- queries exact RAÄ feature counts for all published sites, `Fornlämning`, and `Fornlämning` plus `Möjlig fornlämning`
- builds a 1-degree Swedish density grid by issuing RAÄ WFS count queries cell by cell

## Why Density Instead Of Every Point

RAÄ currently contributes national-scale Swedish archaeology context. The checked-in map uses a density layer rather than individual point markers because the source count is large enough that direct marker rendering would be heavy and visually noisy in the current static HTML map.

```mermaid
flowchart LR
    WFS[RAÄ WFS counts] --> Density[Sweden archaeology density grid]
    Density --> SharedMap[Shared Nordic map]
```

## Acquisition Command

```bash
PYTHONPATH=src artifacts/.venv/bin/python -m bijux_pollenomics.cli collect-data raa --output-root data
```

## Scope Boundary

The current RAÄ layer is Sweden-only. That is an implementation fact of the current repository, not a claim about archaeology coverage in the other countries.

## What The Shared Map Is Honest About

The normalized RAÄ outputs are designed for national-scale archaeological context, not for feature-by-feature archaeological analysis.

- the shared map publishes a density surface, not every underlying point geometry
- the current layer is intended to show concentration and relative coverage, not exact archaeological site locations for downstream decision automation
- Swedish coverage in this repository should not be mistaken for a Nordic archaeology inventory

## Purpose

This page explains why RAÄ is both source-faithful and browser-optimized at the same time.

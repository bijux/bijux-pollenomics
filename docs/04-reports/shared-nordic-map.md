---
title: Shared Nordic Map
audience: mixed
type: explanation
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Shared Nordic Map

The shared Nordic map is the main interactive product surface in this repository.

## Current Behavior

- one map for Sweden, Norway, Finland, and Denmark
- include and exclude by country
- include and exclude by data layer
- grouped layer controls for primary evidence, environmental context, archaeology context, and orientation
- distance circles around point layers
- clustering, search, zoom, empty-state handling, and live layer summaries
- shareable URL state for country, layer, basemap, and distance selections

## Layer Model

```mermaid
flowchart LR
    AADR[AADR points] --> Map[Shared map]
    Neotoma[Neotoma pollen] --> Map
    SEAD[SEAD sites] --> Map
    RAA[RAÄ archaeology density] --> Map
    Boundaries[Country boundaries] --> Map
```

## Why One Shared Map

One shared map is better than multiple country-specific maps because readers can:

- compare countries quickly
- keep one mental model for controls and layers
- inspect borderland or regional patterns without changing pages
- apply the same distance logic across all countries

## Information Model

The map now treats AADR as one source inside a broader multi-evidence view.

- AADR release labels are shown as provenance, not as the map title
- every layer carries its own source and coverage description
- RAÄ archaeology is explicitly described as Sweden-only density coverage
- the live summary separates map build date from source release labels

## Current Published File

- `docs/report/nordic/nordic_aadr_v62.0_map.html`

## Purpose

This page explains the product logic behind the map-first documentation experience and the current shared-map design.

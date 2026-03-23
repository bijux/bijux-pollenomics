---
title: Data Collection Flow
audience: mixed
type: explanation
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Data Collection Flow

The repository now uses one unified collection command, but the implementation stays source-specific under the hood.

## Flow

```mermaid
flowchart TD
    CollectData[collect-data] --> Selector[Source selector]
    Selector --> AADR[aadr collector]
    Selector --> Boundaries[boundaries collector]
    Selector --> Neotoma[neotoma collector]
    Selector --> RAA[raa collector]
    Selector --> SEAD[sead collector]
    Boundaries --> Classification[country classification]
    Neotoma --> Classification
    SEAD --> Classification
```

## Important Design Choice

`collect-data all` is a convenience surface, not a collapse of source boundaries. Each source still has its own module, output directory, and normalization logic.

## Why This Matters

That design keeps the system:

- easy to reason about
- easy to test by source
- easy to update incrementally
- aligned with the top-level `data/` directory model

## Purpose

This page explains how the unified CLI command coexists with a source-aware internal architecture.

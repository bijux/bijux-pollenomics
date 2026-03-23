---
title: Introduction
audience: mixed
type: index
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Introduction

This section gives the mental model for `bijux-pollen` before you start running commands or reading code.

The repository is easiest to understand when you separate five concerns:

- tracked source data under `data/`
- normalization and acquisition logic under `src/bijux_pollen/data_downloader/`
- AADR-driven report generation under `src/bijux_pollen/reporting.py`
- the shared Nordic map as the primary interactive output
- future site-selection interpretation built on top of these reproducible layers

```mermaid
flowchart TD
    Sources[Tracked source data] --> Collector[collect-data workflow]
    Collector --> DataTree[data/ tree]
    DataTree --> Reports[Country reports]
    DataTree --> SharedMap[Nordic shared map]
    Reports --> Interpretation[Sampling interpretation]
    SharedMap --> Interpretation
```

The introduction pages answer four foundational questions:

- what the project is trying to achieve scientifically
- what the repository produces today
- which boundaries are intentional
- why the map is the primary experience but not the only durable output

## Pages in This Section

- [What bijux-pollen does](what-bijux-pollen-does.md)
- [Scope and non-goals](scope-and-non-goals.md)
- [Map-first product model](map-first-product-model.md)

## What You Should Know After This Section

- why the repository centers country-aware spatial evidence, not just raw files
- why AADR `.anno` metadata is tracked while heavy genotype files are not
- how the shared map and report outputs relate to the tracked `data/` tree
- which next section to read for your role

## Reading Advice

Start here if you are new to the repository, planning new data layers, or trying to understand why the docs homepage leads with the map instead of the codebase.

## Purpose

This page explains the introduction section and routes readers to the foundational pages that define what `bijux-pollen` is building.

## Stability

This page is part of the canonical docs spine. Keep it aligned with the current repository behavior and the actual checked-in outputs.

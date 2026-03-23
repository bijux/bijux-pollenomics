---
title: bijux-pollen Documentation
audience: mixed
type: index
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Docs Index

This is the canonical documentation home for `bijux-pollen`.

The first page leads with the live Nordic map because the map is the clearest expression of what this repository produces: a country-filterable view of AADR, pollen, environmental archaeology, and Swedish archaeology context layers assembled into one spatial decision surface.

<div class="bijux-callout">
  <strong>Start with the map.</strong> The documentation spine exists to explain how the map, the data tree, and the report outputs are produced, verified, and extended.
</div>

<div class="bijux-quicklinks">
  <a class="md-button md-button--primary" href="report/nordic/nordic_aadr_v62.0_map.html">Open the Nordic map in its own page</a>
  <a class="md-button" href="03-data-guide/index.md">Read the data guide</a>
  <a class="md-button" href="04-reports/index.md">Read the reports guide</a>
  <a class="md-button" href="06-development/index.md">Read the development workflow</a>
</div>

<div class="bijux-map-frame">
  <iframe src="report/nordic/nordic_aadr_v62.0_map.html" title="Nordic AADR map"></iframe>
</div>

## What This Documentation Set Explains

```mermaid
flowchart LR
    Data[Tracked data tree] --> Prep[collect-data workflow]
    Prep --> Reports[Country reports]
    Prep --> Map[Shared Nordic map]
    Reports --> Decisions[Sampling interpretation]
    Map --> Decisions
```

The docs are organized so a reader can move from the live output into the exact layers of explanation they need:

- what the repository is trying to achieve
- how the five tracked data categories are collected
- how reports and the shared map are generated
- how the source tree is organized
- how local workflows stay reproducible

## Reading Map

```mermaid
flowchart TD
    Home[Home and map] --> Intro[01 Introduction]
    Home --> GettingStarted[02 Getting Started]
    Home --> DataGuide[03 Data Guide]
    Home --> Reports[04 Reports]
    DataGuide --> Architecture[05 Architecture]
    Reports --> Architecture
    Architecture --> Development[06 Development]
    Development --> Reference[07 Reference]
```

## Canonical Sections

- [Introduction](01-introduction/index.md)
- [Getting Started](02-getting-started/index.md)
- [Data Guide](03-data-guide/index.md)
- [Reports](04-reports/index.md)
- [Architecture](05-architecture/index.md)
- [Development](06-development/index.md)
- [Reference](07-reference/index.md)

## Choose a Path

- trying to understand the product goal: start with [Introduction](01-introduction/index.md)
- trying to reproduce the repository state on a fresh machine: use [Getting Started](02-getting-started/index.md)
- trying to understand one source dataset: go to [Data Guide](03-data-guide/index.md)
- trying to understand the interactive outputs: go to [Reports](04-reports/index.md)
- trying to extend the pipeline safely: read [Architecture](05-architecture/index.md) and [Development](06-development/index.md)
- trying to find exact commands, paths, or artifact names: use [Reference](07-reference/index.md)

## Reading Rule

Use section index pages first when you are entering a topic for the first time. Use reference pages when you need exact command names, directories, file patterns, or output expectations.

## Purpose

This page explains the `bijux-pollen` documentation spine and routes readers to the live map and the checked-in documentation path that explains it.

## Stability

This page is part of the canonical docs spine. Keep it aligned with the checked-in outputs and the current repository workflow.

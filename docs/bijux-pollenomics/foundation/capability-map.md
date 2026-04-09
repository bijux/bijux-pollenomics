---
title: Capability Map
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Capability Map

The package has three durable capability families.

## Collection

- register supported sources through `data_downloader.pipeline.source_registry`
- fetch raw source data and stage it into source-specific trees
- normalize records so later reporting code can consume a stable shape

## Reporting

- build country bundles for AADR-driven report slices
- assemble the shared Nordic atlas with country and layer context
- write markdown, HTML, JSON, and auxiliary assets into `docs/report/`

## Coordination

- expose package defaults from `config.py`
- map CLI commands onto handlers and workflows
- centralize file, slug, and output-root conventions

## Purpose

This page names the core capabilities the package is expected to defend over
time.

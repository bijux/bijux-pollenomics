---
title: Capability Map
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Capability Map

The package has three durable capability families, but not all three are equal.
Collection and reporting define the runtime surface. Coordination exists to
keep those two families stable enough to review.

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

## First Proof Check

- `src/bijux_pollenomics/data_downloader/`
- `src/bijux_pollenomics/reporting/`
- `src/bijux_pollenomics/command_line/` and `config.py`

## Boundary Test

If a proposed capability cannot be placed cleanly into collection, reporting,
or coordination, it is probably crossing into provenance policy, maintainer
automation, or interpretation.

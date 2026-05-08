---
title: Module Map
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Module Map

The module tree should teach the evidence lifecycle by shape, not by local
lore.

## Lifecycle Owners

- `command_line/` owns parsing, dispatch, and the durable command registry
- `data_downloader/pipeline/`, `data_downloader/sources/`,
  `data_downloader/intake/`, and `data_downloader/exports/` own source-family
  collection, workbook intake, and context artifact writing
- `adna/` owns animal aDNA intake, sample extraction, locality recovery,
  chronology recovery, coordinate provenance, normalization, and validation
- `analysis/review/` owns candidate-site ranking packets and sensitivity
  surfaces
- `evidence/` owns atlas evidence and scientific review surfaces
- `reporting/adna/`, `reporting/bundles/`, `reporting/context/`,
  `reporting/map_document/`, `reporting/presentation/`,
  `reporting/rendering/`, and `reporting/review/` own publication assembly,
  presentation helpers, governed report packets, and public artifact writing
- `foundation/` owns architecture contracts, ownership maps, repository-truth
  builders, and release posture
- `core/` remains intentionally small: files, text, geojson, HTTP, time, and
  geo-distance primitives

## Animal aDNA Ownership

If a question is about project intake, paper linkage, supplement capture,
sample extraction, locality resolution, chronology evidence, coordinate
provenance, species review, or atlas-ready animal rows, the answer should
usually trace back into `src/bijux_pollenomics/adna/`.

If a question is about how those animal rows become country bundles, atlas
bundles, or repository-truth packets, the path should continue into
`reporting/adna/`, `reporting/bundles/`, `reporting/review/`, and
`foundation/`.

## What The Tree Refuses

- `data_downloader/shared/` and `reporting/shared/` remain compatibility shims,
  not canonical ownership areas
- `pollenomics` is an alias distribution, not a second runtime
- `bijux-pollenomics-dev` is maintainer tooling, not a home for runtime
  scientific logic

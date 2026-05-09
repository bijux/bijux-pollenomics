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
lore. A public reader should be able to look at the package map and understand
which parts gather evidence, which parts normalize it, which parts review it,
and which parts publish it.

## Lifecycle Owners

- `command_line/` owns parsing, dispatch, and the durable command registry
- `data_downloader/pipeline/`, `data_downloader/sources/`,
  `data_downloader/intake/`, and `data_downloader/exports/` own source-family
  collection, workbook intake, and context artifact writing
- `adna/` owns animal aDNA intake, sample extraction, locality recovery,
  chronology recovery, coordinate provenance, normalization, and validation
- `analysis/review/` owns candidate-site ranking reviews and sensitivity
  surfaces
- `evidence/` owns atlas evidence and scientific review surfaces
- `reporting/adna/`, `reporting/bundles/`, `reporting/context/`,
  `reporting/map_document/`, `reporting/presentation/`,
  `reporting/rendering/`, and `reporting/review/` own publication assembly,
  presentation helpers, governed report reviews, and public artifact writing
- `foundation/` owns architecture contracts, ownership maps, repository-truth
  builders, and release posture
- `core/` remains intentionally small: files, text, geojson, HTTP, time, and
  geo-distance primitives

Those boundaries matter because public outputs are only trustworthy when a
reader can trace them back through a stable ownership path.

## Animal aDNA Ownership

If a question is about project intake, paper linkage, supplement capture,
sample extraction, locality resolution, chronology evidence, coordinate
provenance, species review, or atlas-ready animal rows, the answer should
usually trace back into `src/bijux_pollenomics/adna/`.

If a question is about how those animal rows become country bundles, atlas
bundles, or repository-truth reviews, the path should continue into
`reporting/adna/`, `reporting/bundles/`, `reporting/review/`, and
`foundation/`.

## What The Tree Refuses

- `data_downloader/shared/` and `reporting/shared/` remain compatibility shims,
  not canonical ownership areas
- `pollenomics` is an alias distribution, not a second runtime
- `bijux-pollenomics-dev` is maintainer tooling, not a home for runtime
  scientific logic

## How To Read This Map

If a reader starts from a public artifact, the normal path backward is:

1. `reporting/` for the written output
2. `adna/`, `data_downloader/`, or `evidence/` for the upstream evidence state
3. `foundation/` for truth, posture, and ownership explanation

If a page forces the reader to guess instead of following that path, the module
map is not doing its job clearly enough.

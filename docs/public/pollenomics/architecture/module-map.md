---
title: Module Map
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Module Map

The module tree should teach responsibility by meaning, not by local lore. The
practical question is simple: if a visible surface changes, which part of the
repository is supposed to explain, govern, or rebuild it?

This page is not a directory dump. It is a responsibility map for moving from
one question to the right owner quickly.

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

Those boundaries matter because public outputs are only trustworthy when they
can be traced back through a stable ownership path.

## Fast Route By Question

- if the question is about commands, entrypoints, or argument handling, start
  with `command_line/`
- if the question is about where a source family came from or how raw material
  entered the repository, start with `data_downloader/`
- if the question is about animal sample extraction, chronology, coordinates,
  or species review, start with `adna/`
- if the question is about how evidence became a visible report, bundle, or
  map, start with `reporting/`
- if the question is about posture, refusal, ownership, or truth language,
  start with `foundation/`
- if the question is about small shared mechanics such as files, text, time, or
  geometry helpers, start with `core/`

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

## How To Use This Page

Use this page in this order when you need orientation:

1. start from the public question, not from the directory name
2. locate the lifecycle owner that governs that question
3. only then drill into the narrower modules and files underneath that owner

If a page forces you to guess whether you need `reporting/`, `adna/`,
`data_downloader/`, or `foundation/`, the module map is not doing its job well
enough.

---
title: Module Map
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Module Map

The runtime module map matters mainly for the animal aDNA publication boundary.

## Core Ownership

- `src/bijux_pollenomics/adna/` holds the species-aware ancient-DNA contracts
- `adna/` owns species-aware ancient-DNA contracts, non-human normalization,
  accession-family resolution, deterministic artifact plans, species curation,
  project, paper, supplement, sample, site, chronology, and coordinate
  evidence handling, Homo sapiens runtime manifests, metadata-only analysis
  boundaries, archive-integrity review, and scientist-facing species review
  packets
- `reporting/adna/` and `reporting/bundles/` turn those tracked contracts into
  country outputs, manifest diff outputs, and cross-species domestication coverage reporting

## Reader Meaning

If a question is about curated ENA archive intake metadata, paper linkage,
sample extraction, site evidence, chronology, coordinate provenance, species
review packets, or map-ready animal rows, the answer should usually be
traceable back into `src/bijux_pollenomics/adna/`.

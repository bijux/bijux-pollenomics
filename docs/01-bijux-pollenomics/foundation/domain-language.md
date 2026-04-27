---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Domain Language

Stable vocabulary matters here because one wrong noun can blur runtime
behavior, tracked data state, and scientific meaning into the same sentence.

## Preferred Terms

- `source` means an upstream dataset family such as AADR or Neotoma
- `raw` means fetched or copied upstream material before package normalization
- `normalized` means tracked outputs reshaped into repository-friendly files
- `context` means non-AADR layers that help interpret AADR locations
- `report bundle` means a published directory under `docs/report/<slug>/`
- `atlas` means the shared multi-country map bundle under
  `docs/report/nordic-atlas/`

## Terms To Avoid Or Qualify

- avoid calling the package a service when it is a file-producing runtime
- avoid using `database` for tracked file trees unless a real database exists
- avoid naming speculative research outcomes as if they are current outputs

## First Proof Check

- `docs/01-bijux-pollenomics/`
- `docs/02-bijux-pollenomics-data/`
- `docs/05-nordic-evidence-atlas/`

## Language Test

If a sentence makes it hard to tell whether the claim belongs to runtime,
provenance, or interpretation, the wording is too loose.

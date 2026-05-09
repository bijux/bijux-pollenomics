---
title: Runtime Purpose and Boundary
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# What This Repository Is For

`bijux-pollenomics` exists to make the repository's evidence publication loop
rebuildable. It is the package that turns tracked pollen, environmental,
archaeological, boundary, fieldwork, and aDNA source material into files that
readers can review under `data/` and `docs/report/`.

This page is here to answer the first public question: why does this repository
need one owned rebuild path at all?

## What The Runtime Must Keep Legible

- command entrypoints that rewrite tracked state
- tracked source-family and normalized evidence files
- country bundles plus world and regional geography outputs
- tests that fail when those publication contracts drift

If those four surfaces are not tied together, the repository turns into map
presentation without accountable evidence publication.

## What Readers Should Understand First

- [repository scope and limits](repository-scope-and-limits.md): what the
  repository claims today and where it stops
- [end-state product model](end-state-product-model.md): how world, region, and
  country outputs fit together
- [pollenomics engine roadmap](pollenomics-engine-roadmap.md): what broader
  pollenomics ambition still remains ahead
- [runtime scope and ownership](runtime-scope-and-ownership.md): what this
  package owns inside the repository

## Ownership Boundary

- the runtime owns collection, normalization, and publication behavior
- the data handbook owns source provenance and tracked file meaning
- the atlas handbook owns how visible map surfaces should be interpreted
- the maintainer handbook owns release, docs, and repository-health rules

## Reader Route

- if the question is "what is this product trying to do?" stay here
- if the question is "how do world, Europe-plus, Nordic, and country outputs fit together without forking the product?" move to
  [end-state product model](end-state-product-model.md)
- if the question is "what sample, site, or paper supports this?" move to
  [02-bijux-pollenomics-data](../../02-bijux-pollenomics-data/index.md)
- if the question is "how is this visible map point filtered or limited?" move
  to [05-nordic-evidence-atlas](../../05-nordic-evidence-atlas/index.md)
- if the question is "what blocks release?" move to
  [internal guide](../../internal/index.md)

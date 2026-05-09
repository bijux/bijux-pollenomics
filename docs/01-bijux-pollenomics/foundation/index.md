---
title: Runtime Purpose and Boundary
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Runtime Purpose and Boundary

`bijux-pollenomics` exists to make the repository's evidence publication loop
rebuildable. It is the package that turns tracked pollen, environmental,
archaeological, boundary, fieldwork, and aDNA source material into files that
readers can review under `data/` and `docs/report/`.

## What The Runtime Must Keep Legible

- command entrypoints that rewrite tracked state
- tracked source-family and normalized evidence files
- country bundles plus world and regional geography outputs
- tests that fail when those publication contracts drift

If those four surfaces are not tied together, the repository turns into map
presentation without accountable evidence publication.

## Next Pages

- [repository scope and limits](repository-scope-and-limits.md)
- [end-state product model](end-state-product-model.md)
- [pollenomics engine roadmap](pollenomics-engine-roadmap.md)
- [runtime scope and ownership](runtime-scope-and-ownership.md)

## Ownership Boundary

- the runtime owns collection, normalization, and publication behavior
- the data handbook owns source provenance and tracked file meaning
- the atlas handbook owns how visible map surfaces should be interpreted
- the maintainer handbook owns release, docs, and repository-health rules

## Reader Route

- if the question is "how do I rebuild this output?" stay here
- if the question is "how do world, Europe-plus, Nordic, and country outputs fit together without forking the product?" move to
  [end-state product model](end-state-product-model.md)
- if the question is "what sample, site, or paper supports this?" move to
  [02-bijux-pollenomics-data](../../02-bijux-pollenomics-data/index.md)
- if the question is "how is this visible map point filtered or limited?" move
  to [05-nordic-evidence-atlas](../../05-nordic-evidence-atlas/index.md)
- if the question is "what blocks release?" move to
  [03-bijux-pollenomics-maintain](../../03-bijux-pollenomics-maintain/index.md)

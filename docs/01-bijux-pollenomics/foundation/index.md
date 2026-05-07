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
rebuildable. It is the package that turns upstream metadata and tracked curation
rules into files that readers can review under `data/` and `docs/report/`.

## What The Runtime Must Keep Legible

- command entrypoints that rewrite tracked state
- tracked sample, site, and coordinate files
- country bundles and shared atlas outputs
- tests that fail when those publication contracts drift

If those four surfaces are not tied together, the repository turns into map
presentation without accountable evidence publication.

## Ownership Boundary

- the runtime owns collection, normalization, and publication behavior
- the data handbook owns source provenance and tracked file meaning
- the atlas handbook owns how visible map surfaces should be interpreted
- the maintainer handbook owns release, docs, and repository-health rules

## Reader Route

- if the question is "how do I rebuild this output?" stay here
- if the question is "what sample, site, or paper supports this?" move to
  [02-bijux-pollenomics-data](../../02-bijux-pollenomics-data/index.md)
- if the question is "how is this visible map point filtered or limited?" move
  to [05-nordic-evidence-atlas](../../05-nordic-evidence-atlas/index.md)
- if the question is "what blocks release?" move to
  [03-bijux-pollenomics-maintain](../../03-bijux-pollenomics-maintain/index.md)

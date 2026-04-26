---
title: Publication Linkage
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Publication Linkage

Tracked data and tracked publication outputs are separate trees, but they are
tightly linked by contract.

## Linkage Rules

- normalized context data under `data/` feeds report publishing
- AADR versioned data under `data/aadr/` feeds country and atlas outputs
- report bundles under `docs/report/` should remain explainable from the tracked
  data tree present in the same commit

## First Proof Check

- `data/`
- `docs/report/`
- output pages in `docs/02-bijux-pollenomics-data/outputs/`

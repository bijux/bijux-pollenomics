---
title: Provenance Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Provenance Model

Provenance is preserved through source-owned directories, stable naming, and
collection summaries written into the tracked tree.

## Provenance Anchors

- source-specific raw directories
- normalized outputs that stay adjacent to their source
- `data/collection_summary.json` as a repository-wide refresh summary
- report manifests under `docs/report/` for publication outputs

## Boundary Test

If a visible layer cannot be traced back through one source subtree, one
normalized family, or one checked-in summary, provenance is already too loose.

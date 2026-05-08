---
title: RAÄ
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# RAÄ

RAÄ supplies Sweden-specific archaeology context.

## RAÄ Source Model

```mermaid
flowchart TB
    source["RAÄ source data"]
    density["Swedish archaeology density context"]
    normalized["Sweden-scoped normalized outputs"]
    atlas["Swedish atlas context layer"]

    source --> density
    density --> normalized
    normalized --> atlas
```

RAÄ is intentionally narrow. Its value comes from Sweden-specific archaeology
context, not from pretending to cover the whole Nordic region.

## What This Source Adds

- archaeology density context that sharpens Swedish interpretation
- a national surface that helps the atlas show where contextual archaeological
  material clusters
- one clear example of a useful layer that is intentionally not pan-Nordic

## Boundary

RAÄ is valuable precisely because its scope is narrow and explicit. It should
not be presented as a Nordic-wide archaeology source, and it should not be read
as direct evidence outside the Swedish surface it actually covers.

## Downstream Outputs

- `data/raa/normalized/sweden_archaeology_density.geojson`
- `data/raa/normalized/sweden_archaeology_layer.json`
- Swedish atlas context under `docs/report/nordic-atlas/`

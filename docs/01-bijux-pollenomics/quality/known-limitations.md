---
title: Known Limitations
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Known Limitations

The package deliberately stops short of several tempting extensions.

```mermaid
flowchart LR
    genotype["no genotype payload processing"]
    atlas["atlas is not an analysis engine"]
    raa["RAA context is Sweden-specific"]
    upstream["upstream variability still matters"]
    limit["current package limit"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class limit,page genotype;
    class atlas,raa,upstream caution;
    genotype --> limit
    atlas --> limit
    raa --> limit
    upstream --> limit
```

## Current Limitations

- AADR handling is metadata-focused and does not process genotype payloads
- the atlas is a review artifact, not an analysis engine
- RAÄ context is Sweden-specific
- upstream source variability can still change collected content even when local
  code is stable

## Migration Issues To Watch

- old flat docs and the new handbook can drift during the migration unless links
  and nav move together
- output-path renames would require coordinated updates across tests, docs, and
  tracked report bundles

## Bottom Line

These limitations are not hidden defects. They are explicit boundaries readers
should understand before making broader scientific or product claims.


---
title: Domain Language
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Domain Language

Stable package language keeps code, docs, and review comments pointed at the
same objects.

```mermaid
flowchart LR
    source["source"]
    raw["raw"]
    normalized["normalized"]
    report["report bundle"]
    atlas["atlas"]
    reader["shared review language"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class source,page raw;
    class normalized,report,atlas,reader positive;
    source --> raw --> normalized --> report
    report --> atlas
    normalized --> reader
    report --> reader
    atlas --> reader
```

## Preferred Terms

- `source` means an upstream dataset family such as AADR or Neotoma
- `raw` means fetched or copied upstream material before package normalization
- `normalized` means tracked outputs reshaped into repository-friendly files
- `context` means non-AADR layers that help interpret AADR locations
- `report bundle` means a published directory under `docs/report/<slug>/`
- `atlas` means the shared multi-country map bundle under
  `docs/report/nordic-atlas/`

## Terms To Avoid

- avoid calling the package a service when it is a file-producing runtime
- avoid using `database` for tracked file trees unless a real database exists
- avoid naming speculative research outcomes as if they are current outputs

## Core Point

Stable language is not cosmetic. It prevents reviewers from confusing upstream
material with normalized files, or confusing one published output bundle with
the shared atlas.


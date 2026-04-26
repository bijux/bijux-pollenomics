---
title: Data Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Data Contracts

The package's data contracts are filesystem contracts.

```mermaid
flowchart LR
    source["source subtree"]
    raw["raw files"]
    normalized["normalized files"]
    summary["collection summaries"]
    review["reproducible tracked data contract"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class source,page raw;
    class normalized,summary,review positive;
    source --> raw --> normalized --> summary --> review
```

## Contracted Shapes

- each supported source owns a stable subtree under `data/<source>/`
- raw and normalized outputs are separated so source fidelity and repository
  friendliness are both inspectable
- collection summaries and source-specific normalized outputs must remain
  reproducible from one repository state

## Key Contract Modules

- `data_downloader/contracts.py`
- `data_downloader/data_layout.py`
- `data_downloader/pipeline/summary_writer.py`

## Migration Warning

Renaming source directories or normalized filenames is a high-friction change.
It ripples into docs, report publishing, tests, and reviewer expectations.

## Use This Page When

- a change touches `data/` layout or normalized filenames
- reviewers need to decide whether a file move is an interface change

## Purpose

This page shows the package's stable contracts for tracked data outputs.

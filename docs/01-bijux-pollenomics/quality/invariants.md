---
title: Invariants
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Invariants

Certain truths should remain stable across ordinary package changes.

```mermaid
flowchart LR
    commands["commands are explicit about validation vs rewrite"]
    data["data stays grouped by source"]
    reports["reports stay grouped under docs/report"]
    defaults["config defaults stay central"]
    imports["public imports stay real"]
    invariant["review invariants"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class invariant,page commands;
    class data,reports,defaults,imports positive;
    commands --> invariant
    data --> invariant
    reports --> invariant
    defaults --> invariant
    imports --> invariant
```

## Package Invariants

- commands either validate or rewrite tracked outputs deliberately
- source outputs stay grouped by source under `data/<source>/`
- report outputs stay grouped under `docs/report/`
- defaults in `config.py` remain the single obvious source for package-wide
  paths and publication identity
- public imports from `bijux_pollenomics` continue to describe real workflow
  entrypoints

## Reader Takeaway

These are the first truths to defend when a change looks productive but starts
to distort how the package is explained or reviewed.


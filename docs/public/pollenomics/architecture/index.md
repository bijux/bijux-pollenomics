---
title: Evidence Publication Flow
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# How Evidence Becomes Outputs

This section explains the whole public chain from source material to visible
outputs. The architecture matters only if it helps a reader answer a simple
question: how did this report, map point, or country bundle get here?

The answer should be traceable without already knowing the package tree.

## Flow

```mermaid
flowchart LR
    commands["command surface"]
    collection["source collection"]
    normalization["evidence normalization"]
    review["evidence review"]
    assembly["publication assembly"]
    writing["public artifact writing"]
    checks["unit and regression checks"]

    commands --> collection
    collection --> normalization
    normalization --> review
    normalization --> assembly
    review --> assembly
    assembly --> writing
    checks --> commands
    checks --> review
    checks --> writing
```

## Durable Boundaries

- `command_line/` owns CLI parsing, dispatch, and command registration
- `data_downloader/` owns source-family collection, intake helpers, and tracked
  context normalization
- `adna/` owns animal aDNA intake, extraction, normalization, and validation
- `analysis/review/` owns ranking review surfaces rather than public rendering
- `reporting/` owns publication assembly, rendering, and governed report
  writing
- `foundation/` owns repository-truth, release posture, and architecture
  contracts

## Read This Section If You Need To Know

- how the commands line up with tracked source material
- where evidence is normalized before it becomes public output
- which parts of the repository own review versus rendering
- where to look if an output changes unexpectedly

## Expanded Pages

- [runtime system model](runtime-system-model.md)
- [module map](module-map.md)
- [package split](package-split.md)

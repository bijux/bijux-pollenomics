---
title: Evidence Publication Flow
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# How Evidence Becomes Outputs

This section explains the public lifecycle from source material to visible
output. The only reason architecture belongs on a public surface is that
readers eventually need to answer hard practical questions:

- how did this report, map point, or bundle get here
- which part of the system governs it
- where should I look when a visible output seems stronger or weaker than I
  expected

The architecture is therefore presented as a reading aid, not as an internal
tour of module names.

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

## The Main Stages

- commands declare what kind of rebuild, check, or inspection is being
  requested
- collection brings governed source material into the repository
- normalization turns mixed upstream inputs into comparable repository-owned
  evidence files
- review surfaces expose strengths, blockers, caveats, and refusal reasons
- publication writes country, regional, and world-facing outputs
- checks fail when those layers drift apart or start implying too much

## What This Section Should Help You Understand

- why a visible output is never the whole story by itself
- why source intake, evidence normalization, review, and publication must stay
  visibly separate
- where to go next when your question is about system flow rather than evidence
  content

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

- how commands line up with tracked source material
- where evidence becomes reviewable before it becomes public output
- which parts of the repository own review versus rendering
- where to look if an output changes unexpectedly
- how to trace a reader-facing surface back to its governing evidence and rules

## Expanded Pages

- [runtime system model](runtime-system-model.md) explains the end-to-end flow
  in the order it actually runs
- [module map](module-map.md) explains which directories own which parts of the
  lifecycle
- [package split](package-split.md) explains why runtime, maintainer, and alias
  distributions stay separate

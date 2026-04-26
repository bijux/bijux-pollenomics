---
title: Test Strategy
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Test Strategy

`bijux-pollenomics` uses layered tests so command behavior, file contracts, and
source-specific transformations can fail close to the defect.

```mermaid
flowchart LR
    unit["tests/unit"]
    regression["tests/regression"]
    e2e["tests/e2e"]
    change["change under review"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class unit,page change;
    class regression,e2e positive;
    unit --> change
    regression --> change
    e2e --> change
```

## Current Layers

- `tests/unit/` for focused module and helper behavior
- `tests/regression/` for stable output and repository contract behavior
- `tests/e2e/` for CLI-level flows

## Strategy Rule

Add the narrowest test that proves the contract you are changing, then widen to
regression or end-to-end coverage only when the package boundary itself is what
changed.

## Reader Takeaway

More test layers are not automatically better. The honest goal is the smallest
proof surface that still matches the real contract risk.

## Purpose

This page records how the package proves correctness across different scopes.

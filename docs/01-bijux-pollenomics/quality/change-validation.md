---
title: Change Validation
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Change Validation

Validate changes at the narrowest level that still proves the contract.

```mermaid
flowchart LR
    logic["pure logic change"]
    output["output-shape or contract change"]
    workflow["command workflow change"]
    docs["docs structure change"]
    proof["matching validation path"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class logic,page proof;
    class output,workflow,docs positive;
    logic --> proof
    output --> proof
    workflow --> proof
    docs --> proof
```

## Common Validation Paths

- pure Python logic: unit tests
- output-shape or repository contract changes: regression tests
- command workflow changes: end-to-end CLI tests
- doc structure changes: strict MkDocs build

## Validation Rule

When a change spans code and tracked artifacts, validation is not complete until
both the executable checks and the resulting file diffs make sense together.

## Open This Page When

- the right validation depth is unclear
- a change affects both code and checked-in outputs

## Purpose

This page shows how package changes should be validated before merge.

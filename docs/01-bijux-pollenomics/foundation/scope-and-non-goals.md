---
title: Scope and Non-Goals
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Scope and Non-Goals

`bijux-pollenomics` is scoped to deterministic collection and publication work.
It keeps tracked evidence layers and report bundles reproducible from one
repository state.

```mermaid
flowchart LR
    in_scope["deterministic collection and publication"]
    outputs["tracked data and report files"]
    out_scope["site ranking, hosted services, speculative analysis"]
    review["review boundary"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class in_scope,page outputs;
    class out_scope caution;
    class review positive;
    in_scope --> outputs --> review
    out_scope -.keep outside.-> review
```

## In Scope

- downloading or refreshing supported source datasets
- normalizing those sources into stable, reviewable files
- publishing country report bundles and the Nordic Evidence Atlas
- exposing configuration defaults that keep those workflows explicit

## Out of Scope

- genotype processing beyond public AADR metadata files
- lake-intersection analysis and ranking logic
- automated field recommendation or site-selection decisions
- mutable hosted application behavior that depends on server state

## Review Rule

If a proposed change increases scientific ambition or product breadth without
also preserving deterministic file outputs and clear review boundaries, it does
not belong in this package yet.

## Reader Takeaway

This package is allowed to make the repository reproducible. It is not allowed
to quietly become a broader research platform just because nearby data or atlas
surfaces make that expansion tempting.

## Purpose

This page shows the package boundary in terms of what work it absorbs and what
it leaves outside.

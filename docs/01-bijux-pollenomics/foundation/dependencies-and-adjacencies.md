---
title: Dependencies and Adjacencies
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Dependencies and Adjacencies

`bijux-pollenomics` intentionally has a small runtime dependency surface and a
larger adjacency surface inside the repository.

```mermaid
flowchart LR
    runtime["runtime package"]
    direct["direct code dependency<br/>stdlib and defusedxml"]
    adjacent["repository adjacencies<br/>apis, dev package, makes, docs/report, data"]
    review["review question<br/>is this dependency essential or just nearby?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class runtime,page review;
    class direct positive;
    class adjacent caution;
    runtime --> direct
    runtime --> adjacent
    direct --> review
    adjacent --> review
```

## Direct Dependencies

- the Python standard library across CLI, collection, and rendering paths
- `defusedxml` for safe XML handling in source-processing workflows

## Close Repository Adjacencies

- `apis/bijux-pollenomics/v1/` for frozen public API contracts
- `packages/bijux-pollenomics-dev/` for repository-owned checks around the
  runtime surface
- `makes/` for reproducible local and CI command entrypoints
- `docs/report/` and `data/` as the tracked file surfaces the package rewrites

## Review Expectation

Keep new dependencies honest. If a new library or repo surface enters the
package, the reason should be visible in both code and docs, and the package
boundary should become clearer rather than blurrier.

## Reader Takeaway

Not every nearby repository surface is a dependency in the same sense. This
page separates what the runtime truly imports from what it merely coordinates
with or rewrites.

## Purpose

This page shows what the package relies on directly and what it merely sits
next to.

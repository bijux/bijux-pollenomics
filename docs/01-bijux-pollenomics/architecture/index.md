---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Architecture

This section explains how `bijux-pollenomics` is divided structurally across
CLI parsing, data collection, spatial helpers, and report publishing.

Use it when the question is about module seams, dependency direction, and how
tracked outputs are produced from the package internals.

```mermaid
flowchart LR
    module["module map"]
    direction["dependency direction"]
    execution["execution model"]
    seams["integration seams"]
    state["state and persistence"]
    risk["architecture risks"]
    reader["reader question<br/>how is this package shaped?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class module,page reader;
    class direction,execution,seams,state,risk positive;
    module --> reader
    direction --> reader
    execution --> reader
    seams --> reader
    state --> reader
    risk --> reader
```

## Start Here

- open [Module Map](module-map.md) for the shortest code-level tour
- open [Execution Model](execution-model.md) when you need to trace collection
  and publication flow
- open [Integration Seams](integration-seams.md) when the boundary between
  collectors, helpers, and report builders is the real question

## Pages In This Section

- [Module Map](module-map.md)
- [Dependency Direction](dependency-direction.md)
- [Execution Model](execution-model.md)
- [State and Persistence](state-and-persistence.md)
- [Integration Seams](integration-seams.md)
- [Error Model](error-model.md)
- [Extensibility Model](extensibility-model.md)
- [Code Navigation](code-navigation.md)
- [Architecture Risks](architecture-risks.md)

## What This Section Should Answer

- where command flow starts and where output-writing logic actually lives
- which dependencies are allowed to point inward or outward
- which structural risks deserve attention before a change becomes expensive

## Purpose

This page organizes the structural explanations for the runtime package.

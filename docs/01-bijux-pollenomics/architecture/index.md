---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Architecture

Use this section when the important question is how the runtime package is
shaped: where command flow starts, how collection and normalization modules
connect, and where report publishing turns tracked data into visible outputs.

These pages should make the runtime legible enough that readers can trace real
execution and structural seams without reverse-engineering the codebase from
imports alone.

```mermaid
flowchart LR
    cli["CLI and parser entrypoints"]
    dispatch["runtime dispatch and handlers"]
    collect["data collection and normalization"]
    report["report bundle and atlas publishing"]
    helpers["shared core and spatial helpers"]
    seams["integration seams<br/>tracked data and docs/report outputs"]
    reader["reader question<br/>how is this package shaped?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class dispatch,page reader;
    class cli,collect,report,helpers positive;
    class seams positive;
    cli --> dispatch
    dispatch --> collect
    dispatch --> report
    collect --> helpers
    report --> helpers
    collect --> seams
    report --> seams
    seams --> reader
```

## Start Here

- open [Module Map](module-map.md) for the shortest code-level tour
- open [Execution Model](execution-model.md) when you need to trace collection
  and publication flow
- open [Integration Seams](integration-seams.md) when the boundary between
  collectors, helpers, and report builders is the real question
- open [State and Persistence](state-and-persistence.md) when tracked outputs
  and rewrite boundaries are the hard part

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

## Use This Section When

- you need to trace structural ownership before refactoring the runtime
- you are checking where output-writing logic actually lives
- you need to understand how command dispatch, collection, and report building
  stay separated

## Do Not Use This Section When

- the question is mainly about public command syntax, file contracts, or
  defaults
- the issue is operational, such as rebuild workflow or release handling
- you need proof, risk posture, or validation criteria more than structural
  flow

## Read Across The Package

- open [Foundation](../foundation/index.md) when the structural question is
  really an ownership question
- open [Interfaces](../interfaces/index.md) when architecture reaches a public
  command, config, or artifact contract
- open [Operations](../operations/index.md) when structure affects repeatable
  rebuild or release workflows
- open [Quality](../quality/index.md) when you need proof that the documented
  structure is still protected

## Reader Takeaway

Use `Architecture` to make the runtime flow legible enough that a reviewer can
say where commands are parsed, where tracked data is rewritten, and where
publication output is assembled. If that answer only works from private memory,
the structure is still too implicit.

## Purpose

This page introduces the structural explanations for the runtime package and
routes readers to the module, execution, seam, state, and risk pages that
explain how the package is organized.

---
title: State and Persistence
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# State and Persistence

Persistent state in `bijux-pollenomics` is primarily file state.

```mermaid
flowchart TD
    runtime["runtime commands"]
    raw["data/<source>/raw"]
    normalized["data/<source>/normalized"]
    reports["docs/report/"]
    contracts["apis/bijux-pollenomics/v1/"]
    transient["artifacts/ and in-memory objects"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class runtime,page transient;
    class raw,normalized,reports,contracts positive;
    runtime --> raw
    runtime --> normalized
    runtime --> reports
    contracts --> runtime
    transient -.not durable state.-> runtime
```

## Durable State

- tracked source files under `data/<source>/raw/`
- normalized outputs under `data/<source>/normalized/`
- published report bundles under `docs/report/`
- frozen API contracts under `apis/bijux-pollenomics/v1/`

## Non-Durable State

- virtual environments and build artifacts under `artifacts/`
- command-local in-memory objects used during collection and reporting

## Review Implication

Because the runtime persists through files rather than a service database,
state-changing commands must be evaluated through their filesystem diffs. If a
change alters persistent outputs, the docs and review story should say why.

## Use This Page When

- reviewers need to separate durable repository state from disposable run state
- a change proposes a new persistent path or artifact family

## Purpose

This page explains where runtime state lives and how it should be reviewed.

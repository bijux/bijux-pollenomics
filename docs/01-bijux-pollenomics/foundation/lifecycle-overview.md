---
title: Lifecycle Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Lifecycle Overview

The runtime package moves work through one explicit lifecycle:

```mermaid
flowchart LR
    command["1. resolve command"]
    collect["2. collect or load inputs"]
    normalize["3. normalize tracked files"]
    publish["4. publish reports and atlas"]
    review["5. docs and review workflows inspect outputs"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class command,page collect;
    class normalize,publish,review positive;
    command --> collect --> normalize --> publish --> review
```

1. parse a command and resolve defaults
2. collect or load source inputs
3. normalize and stage tracked files
4. publish report artifacts from the tracked inputs
5. hand the resulting outputs to docs and review workflows

## Important Boundaries

- collection can rewrite tracked `data/` outputs
- reporting can rewrite tracked `docs/report/` outputs
- docs publishing is downstream of runtime outputs, not a substitute for them

## Why The Lifecycle Matters

When a change breaks the lifecycle order, reviewers lose the ability to reason
about whether a diff came from source refresh, report publishing, or unrelated
maintenance work.

## Use This Page When

- a change appears to blur collection, normalization, and publication steps
- reviewers need to explain why one command should not also mutate a later
  output surface

## Purpose

This page gives the package's high-level operational sequence before later
sections dive into module and contract detail.

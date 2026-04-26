---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Operator Workflows

Most operators encounter the package through a short set of repository workflows.

```mermaid
flowchart TD
    verify["verify checkout"]
    collect["refresh source data"]
    publish["regenerate report bundles"]
    inspect["inspect atlas and reports"]
    caution["verification should not rewrite state by accident"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class verify,page inspect;
    class collect,publish positive;
    class caution caution;
    verify --> collect --> publish --> inspect
    verify --> caution
```

## Common Operator Flows

- validate a checkout without changing tracked outputs
- refresh source data into `data/`
- regenerate published report bundles into `docs/report/`
- inspect the resulting atlas and country outputs in the docs site

## Expected Operator Stance

Treat collection and report publication as explicit rewrite operations. If the
intent is only verification, use the repository validation targets instead of
running state-changing package commands out of habit.

## Reader Takeaway

The key workflow distinction is between inspection and mutation. This package
is safe to trust when operators stay explicit about which one they are doing.

## Purpose

This page records the operator-facing ways the package is expected to be used.

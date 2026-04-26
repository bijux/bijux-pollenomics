---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Review Checklist

Use this checklist for package-facing changes.

```mermaid
flowchart TD
    boundary["boundaries still clear?"]
    diffs["tracked diffs intentional?"]
    docs["docs updated?"]
    tests["right test layer updated?"]
    defaults["default change reviewed?"]
    review["merge decision"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class review,page boundary;
    class diffs,docs,tests,defaults positive;
    boundary --> review
    diffs --> review
    docs --> review
    tests --> review
    defaults --> review
```

## Checklist

- does the change keep collection, reporting, and maintenance boundaries clear
- are tracked `data/` or `docs/report/` diffs intentional and explained
- do docs reflect any renamed paths, commands, or output contracts
- is the narrowest useful test layer updated
- if defaults changed, was the public contract impact reviewed explicitly

## How To Use This Page

Treat this checklist as the minimum bar, not as a substitute for judgment. If a
change affects a broader surface than these prompts capture, expand the review
instead of forcing the change to fit the checklist.

## Purpose

This page records the minimum review questions for runtime changes.

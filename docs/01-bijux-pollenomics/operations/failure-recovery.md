---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Failure Recovery

Recovery starts by identifying which boundary failed.

```mermaid
flowchart LR
    boundary["identify failed boundary"]
    inspect["inspect affected tracked outputs"]
    rerun["rerun the narrowest proving command"]
    review["review rewritten files before broadening scope"]
    avoid["avoid broad reset commands too early"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class boundary,page review;
    class inspect,rerun positive;
    class avoid caution;
    boundary --> inspect --> rerun --> review
    avoid -.do not skip ahead.-> review
```

## Recovery Sequence

1. determine whether the failure happened during environment setup, data
   collection, report publishing, or docs build
2. inspect the tracked output tree touched by that step
3. rerun the narrowest command that proves the problem is fixed
4. review any rewritten tracked files before moving to broader commands

## Recovery Warning

Do not jump straight to `make app-state` after a failure. That broad command can
rewrite multiple tracked surfaces and make the original fault harder to isolate.

## Reader Takeaway

Recovery is about reducing uncertainty first, not proving endurance by rerunning
everything at once.

## Purpose

This page explains the package-level recovery discipline for failed workflows.

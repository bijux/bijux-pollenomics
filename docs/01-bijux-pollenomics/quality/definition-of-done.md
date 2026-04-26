---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Definition of Done

A package change is done when it is both technically correct and reviewable.

```mermaid
flowchart LR
    boundary["matches package boundary"]
    checks["right checks run"]
    docs["docs and contracts updated"]
    diffs["tracked diffs are understandable"]
    done["done"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class done,page boundary;
    class checks,docs,diffs positive;
    boundary --> done
    checks --> done
    docs --> done
    diffs --> done
```

## Done Means

- the code change matches the documented package boundary
- the right tests or checks were updated and run
- affected docs and output contracts were updated in the same change
- tracked output rewrites are intentional and understandable in review

## Not Done Means

- behavior changed but docs still describe the old surface
- a source or report contract moved without matching test coverage
- a convenience shortcut blurred package and maintenance ownership

## Use This Page When

- a change looks complete technically but may still be incomplete for review
- a pull request needs a shared closure standard before merge

## Purpose

This page shows the quality bar for finishing runtime work honestly.

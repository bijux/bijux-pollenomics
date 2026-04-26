---
title: Risk Register
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Risk Register

```mermaid
flowchart TD
    diffs["large source refresh diffs"]
    upstream["mutable upstream services"]
    contracts["report artifact contract changes"]
    docs["stale internal links during migration"]
    mitigation["current mitigations"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class mitigation,page diffs;
    class upstream,contracts,docs caution;
    diffs --> mitigation
    upstream --> mitigation
    contracts --> mitigation
    docs --> mitigation
```

## Active Risks

- source refreshes can produce large tracked diffs that hide the meaningful
  logic change
- mutable upstream services can introduce surprising data churn
- report artifact contract changes can ripple into docs and review tooling
- incomplete doc migration can leave stale internal links

## Current Mitigations

- keep workflow boundaries explicit
- build docs strictly
- preserve output naming rules in one place
- require docs and tests to move with public contract changes

## Use This Page When

- a proposal is valid but raises operational or review risk that should be
  documented explicitly
- the package needs one place to summarize current structural uncertainty

## Purpose

This page gives maintainers one place to record the current runtime risks.

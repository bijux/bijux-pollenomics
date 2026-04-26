---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Error Model

The package uses command failure and incomplete output prevention as its main
error model.

```mermaid
flowchart LR
    parse["invalid command"]
    source["unsupported source or bad transformation"]
    report["report generation failure"]
    stop["stop early and loudly"]
    stale["avoid stale or half-written outputs"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    class parse,page source;
    class stop,stale positive;
    class report caution;
    parse --> stop
    source --> stop
    report --> stop --> stale
```

## Failure Expectations

- invalid command shapes should fail during argument parsing
- unsupported source names should fail before any write path begins
- source fetch or transformation problems should stop the affected command
- report generation failures should not be hidden behind partially successful
  publication claims

## Review Rule

Prefer failures that are loud, local, and early. A fast explicit command error
is easier to trust than a successful exit that leaves stale or half-written
artifacts in tracked paths.

## Open This Page When

- discussing whether a command should tolerate partial success
- deciding where a validation failure should stop execution

## Purpose

This page shows the package's failure behavior.

---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Observability and Diagnostics

Observability in this package comes from explicit command output and reviewable
files rather than from a separate telemetry stack.

```mermaid
flowchart LR
    command["command output and exit code"]
    summaries["tracked summaries and manifests"]
    tests["test failures"]
    diagnosis["package diagnosis"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class command,page diagnosis;
    class summaries,tests positive;
    command --> diagnosis
    summaries --> diagnosis
    tests --> diagnosis
```

## Diagnostic Surfaces

- command exit codes
- tracked summaries such as `data/collection_summary.json`
- generated report manifests under `docs/report/`
- unit, regression, and end-to-end test failures

## First Checks

- confirm the command and options being used match the documented defaults
- inspect whether `data/` or `docs/report/` changed unexpectedly
- compare the affected output family with the corresponding tests

## Reader Takeaway

Diagnosis starts with the observable repository surfaces the package already
produces. You should not need hidden runtime telemetry to explain most failures.


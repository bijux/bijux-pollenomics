---
title: Evidence Publication Flow
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Evidence Publication Flow

The runtime architecture matters only if it explains one chain clearly:
commands produce tracked evidence files, and those files produce atlas and
country outputs that can be reviewed outside the code.

## Flow

```mermaid
flowchart LR
    commands["CLI commands"]
    collection["collection and normalization"]
    evidence["tracked sample, site, and coordinate files"]
    reports["country bundles and atlas bundle"]
    checks["unit, regression, and e2e proof"]

    commands --> collection
    collection --> evidence
    evidence --> reports
    checks --> commands
    checks --> reports
```

## Durable Boundaries

- `command_line/` owns CLI parsing and dispatch
- `data_downloader/` owns collection and tracked data layout
- `adna/` owns species, sample, site, and coordinate normalization
- `reporting/` owns country bundles, shared atlas, and published report roots

## What To Check First

- `packages/bijux-pollenomics/src/bijux_pollenomics/cli.py`
- `packages/bijux-pollenomics/src/bijux_pollenomics/adna/`
- `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/`
- `packages/bijux-pollenomics/tests/`

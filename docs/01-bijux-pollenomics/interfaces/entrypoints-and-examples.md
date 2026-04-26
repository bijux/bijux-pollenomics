---
title: Entrypoints and Examples
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Entrypoints and Examples

The package supports both shell and import-based entrypoints.

```mermaid
flowchart LR
    shell["shell commands"]
    imports["imported workflow functions"]
    runtime["same runtime behavior"]
    outputs["same tracked outputs"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class shell,page imports;
    class runtime,outputs positive;
    shell --> runtime --> outputs
    imports --> runtime
```

## Shell Examples

```bash
bijux-pollenomics collect-data all --version v66 --output-root data
bijux-pollenomics publish-reports --aadr-root data/aadr --version v66 --output-root docs/report --context-root data
```

## Import Examples

```python
from pathlib import Path

from bijux_pollenomics import collect_context_data, generate_published_reports

collect_context_data(Path("data"))
generate_published_reports(
    aadr_root=Path("data/aadr"),
    version="v66",
    output_root=Path("docs/report"),
    context_root=Path("data"),
)
```

## How To Use This Page

- copy the shell examples when you want repository-facing command usage
- use the import examples when you need package calls from Python code or tests
- treat both patterns as public only when they stay aligned with the CLI and
  artifact contract pages

## Purpose

This page shows the supported entrypoint patterns without forcing readers to
reverse-engineer them from tests.

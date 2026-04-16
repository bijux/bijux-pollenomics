---
title: Entrypoints and Examples
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Entrypoints and Examples

The package supports both shell and import-based entrypoints.

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

## Purpose

This page shows the supported entrypoint patterns without forcing readers to
reverse-engineer them from tests.

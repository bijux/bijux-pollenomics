---
title: Installation and Setup
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Installation and Setup

The supported setup path is repository-first.

```mermaid
flowchart LR
    checkout["repository checkout"]
    install["make install"]
    env["editable environment"]
    version["verify CLI version"]
    work["package, docs, and check workflows"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    class checkout,page install;
    class env,version,work positive;
    checkout --> install --> env --> version --> work
```

## Expected Prerequisites

- Python 3.11
- `uv`
- a checkout that includes tracked `data/`, `docs/`, and `apis/` surfaces

## Recommended Setup Flow

```bash
make install
artifacts/root/check-venv/bin/bijux-pollenomics --version
```

`make install` creates the editable repository environment used for package,
docs, and verification work. Treat that environment as the supported local
entrypoint before troubleshooting command behavior elsewhere.

## Reader Takeaway

The repository environment is the reference setup. If a command behaves
differently elsewhere, debug that environment difference before assuming the
package contract changed.


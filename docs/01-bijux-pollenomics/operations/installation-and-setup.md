---
title: Installation and Setup
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Installation and Setup

The supported setup path is repository-first. Local setup should get a reader
to the runtime proof surface quickly instead of recreating the whole repository
in an ad hoc way.

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

## First Proof Check

- `make install`
- `artifacts/root/check-venv/bin/bijux-pollenomics --version`
- `packages/bijux-pollenomics/tests/`

---
title: Local Development
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Local Development

Local development should keep verification and rewrite operations separate.

## Safe Default Loop

```bash
make lock-check
make lint
make test
make docs
make package-verify
```

## Rewrite Loop

Use explicit rewrite targets only when the intent is to refresh tracked outputs:

- `make data-prep`
- `make reports`
- `make app-state`

## Purpose

This page explains the local package workflow that keeps review intent clear.

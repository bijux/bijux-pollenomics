---
title: Local Workflow
audience: mixed
type: workflow
status: canonical
owner: bijux-pollen-docs
last_reviewed: 2026-03-23
---

# Local Workflow

Use the `Makefile` as the main local interface.

## Primary Commands

```bash
make install
make clean
make lint
make test
make data-prep
make build
make docs
make docs-serve
```

## Artifact Paths

- `make install` uses `artifacts/.venv/`
- `make build` writes distributions into `artifacts/dist/`
- `make docs` writes the site into `artifacts/docs/site/`

## Why The Makefile Exists

The repository now has enough moving parts that a checked-in local workflow is more reliable than asking contributors to remember raw commands.

## Accuracy Rule

When docs or code comments describe a command, file, or artifact, verify it against the current repository state before merging the change.

## Purpose

This page records the preferred local development surface.

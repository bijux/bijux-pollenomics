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
make lint
make test
make data-prep
make build
make docs
make docs-serve
```

## Why The Makefile Exists

The repository now has enough moving parts that a checked-in local workflow is more reliable than asking contributors to remember raw commands.

## Purpose

This page records the preferred local development surface.

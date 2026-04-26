---
title: reusable-workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# reusable-workflows

The repository uses reusable workflows so verification and release logic stay
shared.

## Current Reusable Workflows

- `ci.yml` as the package-scoped verification worker
- `release-artifacts.yml` as the shared release-artifact builder and stager

## Boundary

These workflows are building blocks, not the primary reader entrypoints. Start
from `verify.yml` or the release workflows when the question begins with a GitHub
event.

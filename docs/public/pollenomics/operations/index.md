---
title: Install, Rebuild, Verify
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Install And Rebuild

This section exists for the shortest honest rebuild path: install the checked
environment, run the CLI, and verify that tracked outputs still match the code.

It is written for readers and operators who want the practical path first, not
for maintainers looking for workflow internals.

The main purpose is not to make every workflow look easy. It is to make the
supported paths understandable: what you run, what it changes, and where you
should stop when your question has been answered.

## Start Here

- start with [installation and setup](installation-and-setup.md) if you need a
  working local environment
- use [common workflows](common-workflows.md) if you want the shortest path for
  verification, data refresh, publication review, or full rebuild
- use [failure recovery](failure-recovery.md) when a rebuild has already failed
  and you need the narrowest honest recovery path
- use [operational boundaries](operational-boundaries.md) when you want to know
  what local operations are supported and what the runtime still refuses to
  imply
- use [CLI surface](../interfaces/cli-surface.md) if you need the command set
  itself
- use [test strategy](../quality/test-strategy.md) if you need to choose the
  right validation layer for the change you made

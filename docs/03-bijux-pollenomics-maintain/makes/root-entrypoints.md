---
title: Root Entrypoints
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# Root Entrypoints

The root entrypoint is intentionally small: `Makefile` includes `makes/root.mk`.

`makes/root.mk` then defines the stable repository command surface, including
`check`, `data-prep`, `reports`, `app-state`, and package verification flows.

## Purpose

This page records the durable root make entrypoints.

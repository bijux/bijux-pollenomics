---
title: Make System Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-26
---

# Make System Overview

The make system is the shared command language for repository maintenance.

## Current Structure

- `Makefile` includes `makes/root.mk`
- `makes/root.mk` loads shared env, package catalog, docs, standards, and
  repository command modules
- package-specific behavior stays under `makes/packages/*.mk`

---
title: Dependency Direction
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Dependency Direction

Dependency flow should move inward from command surfaces toward stable helpers
and file contracts.

## Intended Direction

- CLI entrypoints depend on parsing and runtime dispatch
- dispatch depends on collector and reporting services
- collector and reporting code depend on `core/`, `config.py`, and their own
  local contracts
- low-level helpers should not depend back on command registration or docs
  concerns

## Boundary Rule

Source-specific modules may know how to write their own files, but they should
not reach upward into report rendering policy. Reporting modules may consume
normalized source outputs, but they should not quietly redefine how raw source
collection works.

## Purpose

This page records the preferred dependency flow inside the package.

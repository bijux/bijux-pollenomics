---
title: Dependencies and Adjacencies
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Dependencies and Adjacencies

`bijux-pollenomics` intentionally has a small runtime dependency surface and a
larger adjacency surface inside the repository.

## Direct Dependencies

- the Python standard library across CLI, collection, and rendering paths
- `defusedxml` for safe XML handling in source-processing workflows

## Close Repository Adjacencies

- `apis/bijux-pollenomics/v1/` for frozen public API contracts
- `packages/bijux-pollenomics-dev/` for repository-owned checks around the
  runtime surface
- `makes/` for reproducible local and CI command entrypoints
- `docs/report/` and `data/` as the tracked file surfaces the package rewrites

## Review Expectation

Keep new dependencies honest. If a new library or repo surface enters the
package, the reason should be visible in both code and docs, and the package
boundary should become clearer rather than blurrier.

## Purpose

This page explains what the package relies on directly and what it merely sits
next to.

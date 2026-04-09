---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Ownership Boundary

The runtime package owns the behavior that turns source inputs into tracked data
and tracked publication artifacts. It should be the place where reviewers look
for output-shaping logic.

The package does not own generic repository health automation. That work lives
with `bijux-pollenomics-dev`, the make system, and GitHub workflows so runtime
changes and maintenance changes can be reviewed separately.

## Package-Owned Areas

- `command_line/` for public command registration and dispatch
- `data_downloader/` for source collection, staging, and normalization
- `reporting/` for country bundles, atlas generation, and artifact rendering
- `config.py` for package defaults and path contracts

## Adjacent Areas

- `packages/bijux-pollenomics-dev/` for repository-quality tooling
- `makes/` for command orchestration and shared automation contracts
- `docs/` for the checked-in explanatory surface that points at runtime outputs

## Purpose

This page helps reviewers decide whether a change belongs in the runtime
package or in an adjacent maintenance surface.

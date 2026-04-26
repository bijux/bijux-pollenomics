---
title: Migration Issues
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Migration Issues

The tracked data tree carries real migration cost when names, directories, or
publication expectations move.

## Current Migration Issues

- source-directory or normalized-filename renames can trigger wide downstream
  review cost
- output-path changes can break links between `data/`, `docs/report/`, and the
  handbook
- readers can miss contract movement if navigation and file moves are separated

## Mitigation

- move navigation and content together in the final migration step
- keep source and output names stable while the docs shape changes
- verify the site strictly after each batch

## First Proof Check

- cross-links between `data/`, `docs/report/`, and handbook pages
- strict docs validation

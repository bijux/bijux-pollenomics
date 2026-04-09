---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Definition of Done

A package change is done when it is both technically correct and reviewable.

## Done Means

- the code change matches the documented package boundary
- the right tests or checks were updated and run
- affected docs and output contracts were updated in the same change
- tracked output rewrites are intentional and understandable in review

## Not Done Means

- behavior changed but docs still describe the old surface
- a source or report contract moved without matching test coverage
- a convenience shortcut blurred package and maintenance ownership

## Purpose

This page records the quality bar for finishing runtime work honestly.

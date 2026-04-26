---
title: Definition of Done
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Definition of Done

A package change is done when it is both technically correct and reviewable.

## Done Means

- the code change matches the documented package boundary
- the right tests or checks were updated and run
- affected docs and output contracts were updated in the same change
- tracked output rewrites are intentional and understandable in review

## First Proof Check

- boundary still matches runtime ownership
- checks ran at the right layer
- docs and contracts moved with the change
- tracked output diffs are understandable

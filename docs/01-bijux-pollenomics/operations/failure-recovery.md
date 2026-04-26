---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Failure Recovery

Recovery starts by identifying which boundary failed.

## Recovery Sequence

1. determine whether the failure happened during environment setup, data
   collection, report publishing, or docs build
2. inspect the tracked output tree touched by that step
3. rerun the narrowest command that proves the problem is fixed
4. review any rewritten tracked files before moving to broader commands

## First Proof Check

- the affected command and options
- the touched subtree under `data/` or `docs/report/`
- the narrowest proving command
- the matching regression tests

---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Failure Recovery

Recovery starts by identifying which boundary failed.

## Recovery Sequence

1. determine whether the failure happened during environment setup, data
   collection, report publishing, or docs build
2. inspect the tracked output tree touched by that step
3. rerun the narrowest command that proves the problem is fixed
4. review any rewritten tracked files before moving to broader commands

## Recovery Warning

Do not jump straight to `make app-state` after a failure. That broad command can
rewrite multiple tracked surfaces and make the original fault harder to isolate.

## Purpose

This page explains the package-level recovery discipline for failed workflows.

---
title: reusable-workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# reusable-workflows

The repository uses reusable workflows so package release and CI logic stays
shared and explicit.

## Current Reusable Workflows

- `ci-package.yml`
- `build-release-artifacts.yml`

These files are workflow building blocks rather than top-level entrypoints, so
they run through `verify.yml` and `publish.yml` instead of appearing as
standalone manual workflows.

## Purpose

This page records the reusable workflow layer used by the repository.

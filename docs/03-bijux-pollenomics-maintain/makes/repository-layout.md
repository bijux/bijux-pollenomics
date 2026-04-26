---
title: Repository Layout
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-04-10
---

# Repository Layout

`makes/` is structured so shared logic, repository policy, and package profiles
stay in visibly different places.

## Core Areas

- `makes/bijux-py/` for shared make contracts
- `makes/packages/` for package profiles
- repository-owned top-level files such as `env.mk`, `packages.mk`,
  `publish.mk`, and `root.mk`

## Purpose

This page shows the intended layout of the make tree.

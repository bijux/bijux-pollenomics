---
title: Lifecycle Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Lifecycle Overview

The runtime package moves work through one explicit lifecycle:

1. parse a command and resolve defaults
2. collect or load source inputs
3. normalize and stage tracked files
4. publish report artifacts from the tracked inputs
5. hand the resulting outputs to docs and review workflows

## Important Boundaries

- collection can rewrite tracked `data/` outputs
- reporting can rewrite tracked `docs/report/` outputs
- docs publishing is downstream of runtime outputs, not a substitute for them

## Why The Lifecycle Matters

When a change breaks the lifecycle order, reviewers lose the ability to reason
about whether a diff came from source refresh, report publishing, or unrelated
maintenance work.

## Purpose

This page gives the package's high-level operational sequence before later
sections dive into module and contract detail.

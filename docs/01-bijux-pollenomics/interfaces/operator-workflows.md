---
title: Operator Workflows
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Operator Workflows

Most operators encounter the package through a short set of repository workflows.

## Common Operator Flows

- validate a checkout without changing tracked outputs
- refresh source data into `data/`
- regenerate published report bundles into `docs/report/`
- inspect the resulting atlas and country outputs in the docs site

## Expected Operator Stance

Treat collection and report publication as explicit rewrite operations. If the
intent is only verification, use the repository validation targets instead of
running state-changing package commands out of habit.

## Purpose

This page records the operator-facing ways the package is expected to be used.

---
title: Observability and Diagnostics
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Observability and Diagnostics

Observability in this package comes from explicit command output and reviewable
files rather than from a separate telemetry stack.

## Diagnostic Surfaces

- command exit codes
- tracked summaries such as `data/collection_summary.json`
- generated report manifests under `docs/report/`
- unit, regression, and end-to-end test failures

## First Checks

- confirm the command and options being used match the documented defaults
- inspect whether `data/` or `docs/report/` changed unexpectedly
- compare the affected output family with the corresponding tests

## Purpose

This page names the main signals maintainers should use to diagnose package
behavior.

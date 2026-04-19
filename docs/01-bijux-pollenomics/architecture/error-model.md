---
title: Error Model
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Error Model

The package uses command failure and incomplete output prevention as its main
error model.

## Failure Expectations

- invalid command shapes should fail during argument parsing
- unsupported source names should fail before any write path begins
- source fetch or transformation problems should stop the affected command
- report generation failures should not be hidden behind partially successful
  publication claims

## Review Rule

Prefer failures that are loud, local, and early. A fast explicit command error
is easier to trust than a successful exit that leaves stale or half-written
artifacts in tracked paths.

## Purpose

This page records the package's preferred failure behavior.

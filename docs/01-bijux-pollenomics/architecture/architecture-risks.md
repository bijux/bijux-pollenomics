---
title: Architecture Risks
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Architecture Risks

The package architecture is intentionally simple, but simplicity only helps if
the main failure modes stay visible.

## Current Risks

- tracked file outputs can make small code changes look large in review
- upstream source changes can pressure the package into source-specific special
  cases that leak across the runtime
- report rendering and data collection both touch durable files, so boundary
  drift between them is costly
- docs can lag behind package behavior if output contracts change without a
  matching handbook update

## Migration Risks

- moving existing flat docs into the package handbook can leave stale links if
  navigation and cross-references are updated incompletely
- renaming output paths or slugs would force wide downstream changes across
  tracked artifacts, tests, and published docs

## Purpose

This page records the structural risks maintainers should keep in view during
package changes.

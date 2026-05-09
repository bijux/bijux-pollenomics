---
title: Provenance and Publication Linkage
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Provenance and Publication Linkage

This page explains the line between tracked evidence and public publication.
The core principle is simple: every public-facing row, bundle, or map point
should still be traceable back to a narrower governing surface.

## What Provenance Means Here

In this repository, provenance is not only about where a file originally came
from. It is also about what chain of review turned that input into something
public. A visible point is meaningful only if readers can still inspect:

- the source family that supplied the material
- the normalized evidence file that owns the current claim
- the review surface that qualified, blocked, or approved it
- the published output that presents it to readers

## Publication Linkage Rules

- public reports must stay downstream of tracked evidence
- summary views must not outrank the files that govern sample, locality, date, or coordinate claims
- one public bundle should point readers toward the narrower evidence files that justify it
- blocked or partial evidence should remain visibly qualified instead of being promoted by convenience

## Where To Inspect The Links

- `data/source_fact_ownership_registry.json`
- `data/evidence_artifact_contracts.json`
- `docs/report/world/*_point_traceability.md`
- `docs/report/regions/nordic/nordic_point_traceability.md`
- `docs/report/countries/<country-slug>/*_bundle.json`

## Why Readers Should Care

When provenance and publication linkage are clear, a newcomer can audit one
claim without having to understand the whole repository first. That is the
standard this handbook is aiming for.

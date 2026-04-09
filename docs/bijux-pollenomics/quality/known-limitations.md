---
title: Known Limitations
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-10
---

# Known Limitations

The package deliberately stops short of several tempting extensions.

## Current Limitations

- AADR handling is metadata-focused and does not process genotype payloads
- the atlas is a review artifact, not an analysis engine
- RAÄ context is Sweden-specific
- upstream source variability can still change collected content even when local
  code is stable

## Migration Issues To Watch

- old flat docs and the new handbook can drift during the migration unless links
  and nav move together
- output-path renames would require coordinated updates across tests, docs, and
  tracked report bundles

## Purpose

This page records the package limits maintainers should keep visible.

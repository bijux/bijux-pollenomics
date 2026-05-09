---
title: Provenance and Publication Linkage
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Provenance and Publication Linkage

The data system only earns trust when a reader can move from a public output
back to the tracked repository state that produced it. This page explains that
linkage without pretending every source family has identical evidence
strength.

## Provenance Model

- raw or intake artifacts stay in their source-family roots under `data/`
- normalized repository artifacts keep source-family ownership instead of being
  collapsed into one generic export tree
- public outputs under `docs/report/` must be traceable to those tracked files
- docs pages explain the path but do not replace the governing artifacts

## Publication Linkage

- pollen and archaeology context layers publish as atlas-supporting files
- fieldwork publishes as a narrow direct-visit record
- animal aDNA publishes only after sample, site, chronology, and coordinate
  evidence survive release checks
- repository truth reviews under `docs/report/` describe whether public
  language is keeping pace with actual evidence depth

## Coordinate Policy

Coordinates are not one generic fact class. The repository distinguishes:

- direct coordinates backed by source-owned sample or site evidence
- indirect geocoding derived from weaker locality language
- blocked or refused rows that must stay out of strong public map claims

Use the evidence pages and the atlas honesty surfaces whenever the question is
which of those postures applies to a specific row.

---
title: Provenance and Publication Linkage
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Provenance and Publication Linkage

Public outputs in `bijux-pollenomics` are meant to be easy to use, but they
are not meant to become free-floating claims. Every visible row, bundle, or
map point should still lead back to the narrower file that owns the underlying
evidence.

## What This Page Helps You Check

- where a visible claim came from
- what review path stood between raw input and public output
- how coordinate claims stay tied to narrower evidence instead of drifting into
  map-first storytelling
- where to look when a report or point feels too broad for the evidence behind
  it

## The Provenance Chain

Here, provenance is not only about where a file first came from. It is also
about what happened between source capture and public publication. A visible
point is only trustworthy when you can still inspect:

- the source family that supplied the material
- the normalized evidence file that owns the current claim
- the review surface that qualified, blocked, or approved it
- the published output that presents it publicly

The public surface therefore stays downstream of a governing evidence chain.
Presentation can summarize the claim, but it never replaces the file that owns
it.

## Coordinate Policy

Coordinates need their own rule because maps create false confidence very
quickly. A polished point can look exact even when the supporting geography is
approximate, inferred, or still caveated.

The coordinate policy in this repository is:

- coordinates must stay linked to the governing record that explains why they
  were chosen
- caveated, inferred, or weakly supported coordinates must remain visibly
  qualified
- a map point cannot silently outrank the locality and provenance review that
  made it possible

## How Publication Stays Tied To Evidence

- public reports must stay downstream of tracked evidence
- summary views must not outrank the files that govern sample, locality, date, or coordinate claims
- one public bundle should point toward the narrower evidence files that justify it
- blocked or partial evidence should remain visibly qualified instead of being promoted by convenience

Publication linkage is what makes a public surface useful without making it
misleading. You should be able to start from the visible output and walk back
into the narrower record that governs it.

## Where To Inspect The Links

- `data/source_fact_ownership_registry.json`
- `data/evidence_artifact_contracts.json`
- `docs/report/world/*_point_traceability.md`
- `docs/report/regions/nordic/nordic_point_traceability.md`
- `docs/report/countries/<country-slug>/*_bundle.json`

## Why This Matters

When provenance and publication linkage are clear, you do not have to
understand the whole repository before checking one claim carefully. That is
the standard these pages are trying to hold.

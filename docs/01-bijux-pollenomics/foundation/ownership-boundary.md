---
title: Ownership Boundary
audience: mixed
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-04-26
---

# Ownership Boundary

The runtime package owns the behavior that turns source inputs into tracked
data and tracked publication artifacts. It does not own source provenance
policy, repository-health automation, or the interpretation limits of one
published map layer.

## Runtime-Owned Questions

- how commands collect, normalize, and publish tracked evidence
- how the package writes `data/` and `docs/report/` in repeatable ways
- how runtime-facing CLI, config, and artifact contracts stay stable enough to
  rerun and review

## Questions Owned Elsewhere

- source caveats, refresh rules, and provenance detail in the data handbook
- CI, docs, and release policy in the maintainer handbook
- field-visit context and atlas-reading limits in the fieldwork and atlas pages

## Hard Case

One atlas point can force three different questions at once:

- where the point came from: the data handbook
- how the point was rebuilt and published: the runtime package
- what the point safely means to a reader: the atlas or fieldwork pages

## First Proof Check

- `src/bijux_pollenomics/data_downloader/`
- `src/bijux_pollenomics/reporting/`
- `docs/02-bijux-pollenomics-data/`
- `docs/03-bijux-pollenomics-maintain/`

## Boundary Test

If the page has to explain upstream evidence quality or repository-wide
automation to justify a runtime change, the ownership line has already moved.

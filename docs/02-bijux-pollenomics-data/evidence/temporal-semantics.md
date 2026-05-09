---
title: Temporal Semantics
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Temporal Semantics

Bijux Pollenomics now treats time as one governed evidence surface rather than
one pile of numeric BP fields.

That matters because the repository mixes different kinds of time evidence:

- sample-owned animal aDNA chronology
- site-level archaeology context from SEAD
- broader publication bundles that combine direct and contextual layers

Those sources do not support the same claims. A direct sample interval can be
compared numerically. A broad cultural label or a site-level contextual period
can guide interpretation, but it should not pretend to be the same thing.

## The Shared Contract

Every governed time-aware surface now carries `temporal_semantics` with the
same core questions:

- what evidence class produced this time surface
- how precise the published time claim is
- whether the row supports numeric comparison, comparison only with caveats, or
  contextual reading only
- which time window the row belongs to when a numeric interval exists
- which original labels, normalized labels, and uncertainty notes remain visible

The current comparability postures are:

- `numeric_interval`
- `numeric_interval_with_caveat`
- `contextual_label_only`
- `mixed_interval_and_context`
- `unresolved`

## What Changes For Readers

Time filters and legends now rely on temporal semantics instead of assuming
that every row with a label belongs in one clean BP comparison space.

- animal chronology can remain visible while still being marked as approximate,
  contextual, or broad-period-only
- SEAD can publish site periods, duration ranges, and uncertainty without being
  flattened into fake sample-like dates
- publication guards can now fail if contextual-only rows leak into public
  outputs with misleading numeric chronology fields

## Direct Files

- `data/adna/governance/source_library/sample_chronology_provenance_review.json`
- `data/sead/review/temporal_review.json`
- `data/sead/review/evidence_legibility_review.json`
- [`docs/report/animal_temporal_comparison_review.md`](../../report/animal_temporal_comparison_review.md)
- [`docs/report/animal_publication_release_gate.md`](../../report/animal_publication_release_gate.md)

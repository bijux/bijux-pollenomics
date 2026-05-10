---
title: Temporal Semantics
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Temporal Semantics

Temporal semantics is the layer that keeps chronology readable across source
families that express time in different ways.

## Why This Layer Exists

The repository compares material from several domains:

- release-based human ancient DNA
- animal ancient DNA recovered from papers and supplements
- pollen and archaeology context with their own dating conventions

Those families do not describe time with one common grammar. Temporal semantics
exists so public outputs can compare them without pretending they are all
equally precise.

## What You Should Be Able To Tell

This layer should make the following visible:

- whether a time claim is exact, ranged, broad, or text-derived
- whether two records are reasonably comparable
- whether a public label is being simplified for readability
- where uncertainty has been preserved instead of erased

## Why It Matters In Public Outputs

Map filters and summary labels can make a dataset look more coherent than it
really is. Temporal semantics is one of the mechanisms that prevents that
illusion by keeping uncertainty attached to the claim.

## Direct Files Behind This Surface

- `data/sead/review/temporal_review.json`
- `data/sead/review/evidence_legibility_review.json`
- `data/sead/review/access_model.json`
- `data/sead/review/recovery_roadmap.json`

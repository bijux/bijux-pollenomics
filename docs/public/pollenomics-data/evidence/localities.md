---
title: Localities
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Localities

Locality evidence explains what place claim the repository is actually willing
to make for a sample. That may sound obvious, but it is where many historical
datasets become overstated if the documentation is sloppy.

This page matters because a place label can look precise long before it is
actually precise. A project name, a regional description, and a named site are
not the same kind of locality claim.

## What Locality Review Is Trying To Prevent

- treating a project-wide label as if it identified one precise site
- treating a broad regional note as if it were enough for exact map publication
- carrying forward place names that are still ambiguous across supplements,
  archive metadata, and article text

## What Readers Should Be Able To Learn

- whether a sample is tied to one named site
- whether the place claim is broad, uncertain, or contested
- whether the location is strong enough to support downstream coordinate work

## Why Place Claims Need Their Own Layer

A locality claim does more than name a place. It determines:

- whether a record can later be mapped precisely
- whether a country bundle is speaking about one site or only about a broader
  region
- whether the repository is showing direct archaeological context or a more
  cautious geographic approximation

## What A Reader Should Watch For

- a project or paper label being mistaken for one exact excavation site
- a regional note being read as if it were enough for exact coordinates
- a confident place name hiding unresolved disagreement between sources

## Direct Files Behind This Surface

- `data/adna/species/ovis_aries/normalized/site_evidence.json`
- `data/adna/species/ovis_aries/review/sample_locality_evidence.json`
- `data/adna/governance/source_library/project_sample_site_review.json`
- `data/adna/governance/source_library/sample_locality_conflict_ledger.json`

## Why This Page Matters

If locality evidence is weak, every later step stays weaker too. Chronology and
coordinates may still be useful, but they cannot rescue an unresolved place
claim on their own.

## Where To Go Next

- move to [sample records](sample-records.md) if the identity itself is still
  uncertain
- move to [coordinates](coordinates.md) if the locality is good enough to ask
  why a point did or did not publish
- move to [chronology](chronology.md) if the place is clear but the time claim
  is still the real source of doubt

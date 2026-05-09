---
title: Collection Summary
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Collection Summary

The collection summary is the compact ledger that says what the repository
currently holds after data preparation and refresh.

It is useful because readers often see the public website after a map, report,
or country bundle has already been generated. At that stage it is easy to miss
that the public product sits on top of a collection pipeline that changes over
time. The collection summary exists so that growth, imbalance, and refresh
state remain visible instead of disappearing behind polished pages.

## What Questions It Answers

- which source families were refreshed recently
- how much material is currently staged by family
- whether a visible change probably came from source collection rather than
  only from docs or presentation logic
- whether one family is much stronger or broader than another
- whether a reader should expect a newly published geography to reflect major
  new intake or only a new public route through older material

## Where To Inspect It

- `data/collection_summary.json` is the governing checked-in summary for this
  surface
- this page explains how that summary should be read as a refresh and breadth
  ledger rather than as a proof ledger

## Why Readers Should Care

The summary is not only a maintainer ledger. It helps answer audience questions
that naturally arise when using the repository:

- is this project growing, or only being repackaged
- does the public product rest on broad evidence or on one especially strong
  family
- when a new map or report appears, did the underlying collection actually
  change
- which families still look thin enough that they should be interpreted with
  extra caution

## How To Use It Well

Read the collection summary together with:

- [sources](../sources/index.md) if you want to understand where the material
  came from
- [evidence](../evidence/index.md) if you need to know how a claim becomes
  reviewable
- [reports](reports.md) and [maps](maps.md) if you want to compare visible
  publication breadth with actual collected breadth
- [limits](limits.md) if a family appears present in the repository but still
  does not publish strongly

## What It Cannot Tell You By Itself

The collection summary is a breadth ledger, not a proof ledger. It can show
that material exists, but it cannot by itself prove that:

- all rows are equally strong
- a sample has coordinate-grade locality evidence
- a geography is ready for stronger public language
- contextual families and sample-backed families should be read as equivalent

That is why the summary belongs in the handbook, but not at the top of the
interpretive chain.

## Why It Belongs In The Handbook

This summary helps readers understand that the public product sits on top of a
tracked data collection pipeline. It is not only a docs site or a map bundle.

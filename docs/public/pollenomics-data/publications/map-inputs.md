---
title: Map Inputs
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Map Inputs

Geographic input surfaces are the tracked files that feed the public map and
report bundles. They matter because a public map is only as honest as the
inputs it is allowed to draw from.

Readers usually meet the atlas from the front: a point is visible, a filter is
active, and a popup tells a compact story. This page explains the reverse
direction. If a reader wants to challenge what the map shows, these are the
surfaces that make that challenge possible.

## What Counts As A Map Input

In practice, map inputs include:

- normalized evidence files that carry sample, locality, chronology, and
  coordinate decisions
- scope and boundary files that decide where one view stops and another starts
- layer-specific ledgers that decide which families are allowed to appear in a
  world, regional, or country surface
- review artifacts that explain why some rows still publish cautiously or do
  not publish at all

That means a map input is not only a coordinate table. It is the wider set of
files that controls what a point means, where it can appear, and how strongly
it may be described.

## Why Readers Should Care

If a map point is challenged, the answer should not stop at the rendered HTML.
Readers should be able to trace the visible surface back to the input layer,
then further back to the evidence files and source families that produced it.

## What Questions This Page Helps Answer

- which files decided that a point could be shown at all
- which files decided that the point belongs to a specific geography
- whether a visible change came from better evidence, new intake, or only a
  presentation rewrite
- which source family contributed the visible context around one point
- where to look when a visible point seems broader, sharper, or more confident
  than expected

## How To Use The Input Chain

If a map raises a question, a useful reading order is:

1. start with [maps](maps.md) to identify the visible surface being challenged
2. move to [point rules](point-rules.md) to understand what publication rules
   had to be met
3. inspect the review and audit artifacts linked below to see which files fed
   the visible bundle
4. move back into the [evidence](../evidence/index.md) and [sources](../sources/index.md)
   sections if the real challenge is about chronology, locality, or source
   provenance rather than map rendering

## What These Inputs Protect Against

The input chain exists to stop the atlas from becoming a black box. It protects
against:

- a map point that cannot be traced back to a governing evidence decision
- geography filters that appear to work visually but are not backed by explicit
  scoped inputs
- context layers being read as sample-backed proof
- newly published regions looking stronger than the underlying inputs justify

## Direct Input Audits

- [repository atlas input audit](../../../report/repository_atlas_input_audit.md)
- [repository cross-domain evidence matrix](../../../report/repository_cross_domain_evidence_matrix.md)
- [repository truth posture](../../../report/repository_truth_posture.md)

---
title: Map Inputs
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Map Inputs

Map inputs are the files that decide what the public maps are allowed to show.
They matter because a visible atlas is only as honest as the evidence,
boundaries, and review surfaces that feed it.

Most readers meet the atlas from the front: a point is visible, a filter is
active, and the story looks compact. This page explains what sits behind that
surface so a reader can challenge the map without guessing.

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

## Why This Matters To A Reader

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

## How To Trace A Surprise On The Map

Use this route when a map raises a question:

1. identify the visible surface in [maps](maps.md)
2. check [point rules](point-rules.md) if the question is why one point exists
3. check [filters and popups](filters-and-popups.md) if the question is why the
   point behaves differently across scopes
4. inspect the audit anchors below to see which tracked files fed that public
   output
5. move back into [evidence](../evidence/index.md) or [sources](../sources/index.md)
   when the real disagreement is about chronology, locality, or provenance

## What This Input Chain Protects Against

The input chain exists to stop the atlas from becoming a black box. It protects
against:

- a map point that cannot be traced back to a governing evidence decision
- geography filters that appear to work visually but are not backed by explicit
  scoped inputs
- context layers being read as sample-backed proof
- newly published regions looking stronger than the underlying inputs justify

## What A Reader Should Learn From This Page

- a map is governed by several file families, not one magic export
- geography inclusion is a decision, not a visual accident
- context layers and sample-backed evidence have different responsibilities
- visible change does not automatically mean stronger evidence

## Direct Input Audits

- [repository atlas input audit](../../../report/repository_atlas_input_audit.md)
- [repository cross-domain evidence matrix](../../../report/repository_cross_domain_evidence_matrix.md)
- [repository truth posture](../../../report/repository_truth_posture.md)

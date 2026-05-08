---
title: Collection Summary
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Collection Summary

`data/collection_summary.json` is the shortest checked-in summary of a tracked
refresh.

## Summary Model

```mermaid
flowchart TB
    sources["source refresh work"]
    normalized["normalized trees"]
    summary["data/collection_summary.json"]
    outputs["published report and atlas changes"]
    review["reviewable repository change"]

    sources --> normalized
    normalized --> summary
    summary --> outputs
    outputs --> review
```

This page makes the summary file feel like a review bridge, not a stray
diagnostic. It exists so one refresh can be read quickly before a reviewer
dives into normalized trees or visible publication bundles.

The summary is now paired with four companion contract files:

- `data/source_family_contracts.json`
- `data/source_family_evidence_stage_matrix.json`
- `data/source_fact_ownership_registry.json`
- `data/evidence_artifact_contracts.json`

## What It Shows

- one cross-source view of the current collection state
- source counts and refresh outcomes that reviewers can inspect quickly
- one stage row per source family, including raw, normalized, review, and publication posture
- the checked-in contract paths that explain where recurring facts and artifact scopes are governed
- the bridge between source refresh work and later publication changes

## Boundary

The collection summary is a diagnostic ledger, not a reader-facing report. It
shows what changed in the tracked tree, but it does not replace the normalized
output pages or the published atlas and report surfaces.

## First Proof Check

- inspect `data/collection_summary.json`
- inspect `data/source_family_evidence_stage_matrix.json`
- compare it against the matching `data/*/normalized/` trees and `docs/report/` outputs
- compare with the [cross-domain evidence matrix](../../report/repository_cross_domain_evidence_matrix.md) when the real question is balanced domain coverage rather than one refresh snapshot

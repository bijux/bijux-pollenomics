---
title: Supplements
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Supplements

Supplements are where project metadata becomes row-level evidence. They often
carry the sample tables, locality notes, and chronology text that the paper
summarizes only loosely.

## Direct Files

- [`data/adna/governance/source_library/supplement_registry.json`](../../../data/adna/governance/source_library/supplement_registry.json)
- [`data/adna/governance/source_library/supplement_zip_member_registry.json`](../../../data/adna/governance/source_library/supplement_zip_member_registry.json)
- [`data/adna/governance/source_library/source_blockers.json`](../../../data/adna/governance/source_library/source_blockers.json)
- [`data/adna/governance/source_library/papers/10.1038-s42003-021-02794-8/supplementary_manifest.json`](../../../data/adna/governance/source_library/papers/10.1038-s42003-021-02794-8/supplementary_manifest.json)

## What This Layer Answers

- whether the repository archived the required supplement
- which files inside a zip or PDF bundle were inspected
- which unreadable or missing members still block extraction

If supplement capture is weak, the downstream sample, site, and chronology
pages should still expose that weakness instead of smoothing it away.

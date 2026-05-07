---
title: Supplements
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Supplements

Supplements are where project metadata becomes row-level evidence. They often
carry the sample tables, locality notes, and chronology text that the paper
summarizes only loosely.

## Direct Files

- [`data/adna/governance/source_library/supplement_registry.json`](../../../data/adna/governance/source_library/supplement_registry.json)
- [`data/adna/governance/source_library/supplement_zip_member_registry.json`](../../../data/adna/governance/source_library/supplement_zip_member_registry.json)
- [`data/adna/governance/source_library/supplement_file_family_audit.json`](../../../data/adna/governance/source_library/supplement_file_family_audit.json)
- [`data/adna/governance/source_library/supplement_acquisition_checklist.json`](../../../data/adna/governance/source_library/supplement_acquisition_checklist.json)
- [`data/adna/governance/source_library/source_blockers.json`](../../../data/adna/governance/source_library/source_blockers.json)
- [`data/adna/governance/source_library/papers/10.1038-s42003-021-02794-8/supplementary_manifest.json`](../../../data/adna/governance/source_library/papers/10.1038-s42003-021-02794-8/supplementary_manifest.json)

## What This Layer Answers

- whether the repository archived the required supplement
- whether the repository only knows the supplement from the local DOI-keyed stash and still needs governed ingestion
- which exact file families are expected for each paper: PDF appendix, XLSX table, ZIP bundle, image appendix, or other payload
- which publisher, DOI, Crossref, and PMC or PubMed anchors were checked during supplement verification
- which files inside a zip or PDF bundle were inspected
- which unreadable or missing members still block extraction

If supplement capture is weak, the downstream sample, site, and chronology
pages should still expose that weakness instead of smoothing it away.

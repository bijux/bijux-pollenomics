---
title: Papers
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Papers

Papers are the narrative anchor for each tracked project. They explain the
study design, cite the site names used later in the database, and point to the
supplements or archive tables that can be turned into sample-owned rows.

## Direct Files

- [`data/adna/governance/source_library/paper_registry.json`](../../../data/adna/governance/source_library/paper_registry.json)
- [`data/adna/governance/source_library/tracked_project_and_paper_inventory.md`](../../../data/adna/governance/source_library/tracked_project_and_paper_inventory.md)
- [`data/adna/governance/source_library/papers/10.1038-s42003-021-02794-8/supplementary_manifest.json`](../../../data/adna/governance/source_library/papers/10.1038-s42003-021-02794-8/supplementary_manifest.json)
- [`data/adna/governance/source_library/source_blockers.json`](../../../data/adna/governance/source_library/source_blockers.json)

## Why Papers Stay Separate From Projects

- one project accession can map to one paper or a paper cluster
- papers carry site wording that does not always appear in archive metadata
- citation and supplement provenance must survive even after rows are normalized

The paper layer keeps the database honest about where the site and chronology
claims were actually read.

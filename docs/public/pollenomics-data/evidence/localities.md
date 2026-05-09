---
title: Localities
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Localities

Locality evidence is where the repository decides whether a sample really owns
a named place, only inherits a project-level label, or still needs manual
review.

## Direct Files

- `data/adna/governance/source_library/project_sample_site_review.json`
- `data/adna/governance/source_library/sample_site_ambiguity_ledger.json`
- `data/adna/governance/source_library/sample_site_manual_curation_queue.json`
- `data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json`
- `data/adna/species/ovis_aries/normalized/site_evidence.json`

## What This Layer Decides

- whether a sample has direct site evidence
- whether it only has a broader project-level or region-level locality
- whether the place claim remains unresolved and should stay blocked from exact publication

## Why Locality Review Matters

- it prevents a multi-site project from becoming one fake project point
- it prevents region-only geography from being shown as an exact excavation site
- it keeps unresolved place claims visible instead of smoothing them away

Locality review is the checkpoint between text extraction and map publication.

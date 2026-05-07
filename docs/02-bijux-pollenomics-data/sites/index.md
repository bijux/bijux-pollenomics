---
title: Sites
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Sites

Site evidence is where the repository decides whether a sample really owns a
named locality, only inherits a project-level place label, or still needs
manual curation.

## Direct Files

- [`data/adna/governance/source_library/project_sample_site_review.json`](../../../data/adna/governance/source_library/project_sample_site_review.json)
- [`data/adna/governance/source_library/sample_site_ambiguity_ledger.json`](../../../data/adna/governance/source_library/sample_site_ambiguity_ledger.json)
- [`data/adna/governance/source_library/sample_site_manual_curation_queue.json`](../../../data/adna/governance/source_library/sample_site_manual_curation_queue.json)
- [`data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json`](../../../data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json)
- [`data/adna/species/ovis_aries/normalized/site_evidence.json`](../../../data/adna/species/ovis_aries/normalized/site_evidence.json)

## What This Layer Prevents

- flattening a multi-site project into one fake project point
- publishing region-only geography as if it were an exact excavation site
- hiding rows that still depend on manual locality interpretation

The site table is the checkpoint between text extraction and map publication.

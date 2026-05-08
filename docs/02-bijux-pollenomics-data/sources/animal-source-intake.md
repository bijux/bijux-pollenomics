---
title: Animal Source Intake
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Animal Source Intake

The animal ancient DNA work in this repository starts long before a point
appears on a map. It begins with project accessions, linked papers,
supplementary material, and the sample-recovery work needed to turn those
inputs into defensible locality and chronology evidence.

This page brings the intake chain together in one place so readers do not have
to jump between separate project, paper, and supplement pages to understand the
state of the data.

## Reader Anchors

- `data/adna/governance/source_library/tracked_project_and_paper_inventory.json`
- `data/adna/governance/source_library/tracked_project_and_paper_inventory.md`
- `data/adna/governance/source_library/project_registry.json`
- `data/adna/governance/source_library/paper_registry.json`
- `data/adna/governance/source_library/tracked_project_scope_audit.json`
- `data/adna/governance/source_library/project_source_evidence_matrix.json`
- `data/adna/governance/source_library/supplement_acquisition_checklist.json`
- `data/adna/governance/source_library/supplement_file_family_audit.json`
- `data/adna/governance/source_library/reference_stash_reconciliation.json`
- `data/adna/governance/source_library/reference_stash_doi_integrity_audit.json`
- `data/adna/governance/source_library/source_intake_audit.json`
- `data/adna/governance/source_library/source_intake_release_guard.json`
- `data/adna/governance/source_library/source_blocker_review.json`
- `data/adna/governance/source_library/cross_project_source_intake_dossier.json`
- `data/adna/governance/source_library/project_sample_master_completeness.json`
- `data/adna/governance/source_library/project_sample_site_review.json`
- `data/adna/governance/source_library/project_sample_chronology_review.json`
- `data/adna/governance/source_library/sample_chronology_normalization_audit.json`
- `data/adna/governance/source_library/sample_identity_ambiguity_ledger.json`
- `data/adna/governance/source_library/sample_site_ambiguity_ledger.json`
- `data/adna/governance/source_library/sample_site_manual_curation_queue.json`
- `data/adna/governance/source_library/sample_chronology_ambiguity_ledger.json`
- `data/adna/governance/source_library/projects/PRJEB36540/sample_master.json`
- `data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json`
- `data/adna/governance/source_library/projects/PRJEB36540/sample_chronology.json`

## Intake Stages

| Stage | What it asks |
| --- | --- |
| Project intake | Which archive accessions are in scope? |
| Paper linkage | Which papers anchor those projects? |
| Supplement capture | Which sample tables or appendices are available? |
| Sample recovery | Which sample rows can be recovered with defensible lineage? |
| Locality recovery | Which recovered samples already have usable site evidence? |
| Chronology recovery | Which recovered samples already have usable date evidence? |

## What This Page Answers

- Which tracked projects still need paper capture
- Which papers have archived supplementary material
- Which papers already have local supplementary material staged outside the repo even though governed repo ingestion is still missing
- Which projects already carry archive-native sample identifiers
- Which projects already ship a reviewed project sample master
- Which recovered sample rows already have direct site evidence and which still sit at project-level or region-level locality posture
- Which recovered sample rows already have normalized chronology, which still keep text-only dating claims, and which remain unresolved
- Which tracked papers and projects are blocked at paper capture, supplement ingestion, sample identity extraction, site extraction, or chronology extraction

The intake surface is broader than the Nordic atlas on purpose. Many projects
still matter to the repository even when they are not yet ready for map
publication.

When a page name above ends in `.json` or `.md`, it refers to a tracked file in
the repository tree rather than another page in this docs site.

---
title: Animal Source Intake
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Animal Source Intake

Animal ancient DNA does not enter this repository as one clean public-ready
table. It usually begins as a chain of archives, papers, supplementary files,
partial sample lists, ambiguous locality wording, and uneven chronology detail.

The map is the end of a review process, not the beginning of one. Before an
animal sample becomes a visible point, the repository has to decide whether
the project is in scope, whether the paper trail is complete, whether the
supplementary material is usable, and whether the recovered sample can support
locality and chronology claims honestly.

## Why Intake Is A Public Surface

Readers often assume that a missing point means "no evidence exists" or that a
visible point means "every underlying field was straightforward." Neither is
safe to assume in animal ancient DNA work.

The intake surface is public because it answers a more honest question: what
had to be recovered, checked, and governed before the repository was willing to
show this evidence as a public output?

## What Intake Has To Establish

| Stage | What it asks |
| --- | --- |
| Project intake | Which archive accessions are in scope? |
| Paper linkage | Which papers anchor those projects? |
| Supplement capture | Which sample tables or appendices are available? |
| Sample recovery | Which sample rows can be recovered with defensible lineage? |
| Locality recovery | Which recovered samples already have usable site evidence? |
| Chronology recovery | Which recovered samples already have usable date evidence? |
| Coordinate derivation | Which recovered samples already have mappable coordinate support? |
| Publication readiness | Which projects are credible enough to move into public map and country surfaces? |

This is not busywork around the science. It is the work that determines whether
public scientific language can be trusted.

## What You Can Learn Here

- which tracked projects still need paper capture
- which papers already have archived supplementary material
- which projects already carry archive-native sample identifiers
- which projects already ship a reviewed sample master
- which recovered sample rows already have direct site evidence and which still
  remain at project-level or region-level posture
- which recovered sample rows already have normalized chronology and which
  remain unresolved
- which projects are blocked at paper capture, supplement ingestion, sample
  identity extraction, site extraction, or chronology extraction
- which manual curation tasks still block sample identity, exact site,
  chronology, or coordinate recovery

## Repository-Owned Records Behind Intake

The intake chain is intentionally explicit. Important governed files include:

- `data/adna/governance/source_library/tracked_project_and_paper_inventory.json`
- `data/adna/governance/source_library/project_registry.json`
- `data/adna/governance/source_library/paper_registry.json`
- `data/adna/governance/source_library/supplement_acquisition_checklist.json`
- `data/adna/governance/source_library/supplement_file_family_audit.json`
- `data/adna/governance/source_library/source_intake_audit.json`
- `data/adna/governance/source_library/project_recovery_stage_review.json`
- `data/adna/governance/source_library/project_sample_master_completeness.json`
- `data/adna/species/<species-slug>/normalized/sample_master.json`
- `data/adna/governance/source_library/project_sample_site_review.json`
- `data/adna/species/<species-slug>/normalized/sample_sites.json`
- `data/adna/species/<species-slug>/review/locality_worksheet.json`
- `data/adna/species/<species-slug>/review/sample_locality_evidence.json`
- `data/adna/governance/source_library/project_sample_chronology_review.json`
- `data/adna/species/<species-slug>/normalized/sample_chronology.json`
- `data/adna/governance/source_library/sample_identity_ambiguity_ledger.json`
- `data/adna/governance/source_library/sample_locality_conflict_ledger.json`
- `data/adna/governance/source_library/sample_chronology_ambiguity_ledger.json`
- `data/adna/governance/source_library/site_name_normalization_dictionary.json`
- `data/adna/governance/source_library/reference_stash_reconciliation.json`
- `data/adna/governance/source_library/source_blocker_review.json`
- `data/adna/governance/source_library/project_expected_sample_yield_review.json`
- `data/adna/governance/source_library/manual_curation_worklist.json`
- `data/adna/governance/source_library/source_recovery_release_guard.json`

These records make it possible to see where a project is still thin, where a
sample can already support public claims, and where the repository has chosen
to stay narrow rather than overstate confidence.

## Why Intake Is Broader Than The Atlas

Many projects matter to the repository before they are ready for map
publication. That is not a failure. It is a sign that the repository keeps the
recovery work visible instead of pretending incomplete evidence is already
public-ready.

If you want to understand why the repository does not publish every tracked
animal project as if it were equally mature, this is the page that explains
the difference.

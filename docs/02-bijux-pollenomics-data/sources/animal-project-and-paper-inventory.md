---
title: Animal Project and Paper Inventory
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Animal Project and Paper Inventory

`bijux-pollenomics` should not hide behind the Nordic map at this stage. The
real intake surface is the tracked cross-species animal aDNA inventory: which
projects are in scope, which papers are pinned, which supplementary assets are
archived, and which projects are still blocked from sample extraction.

## Reader Anchors

- [`data/adna/governance/source_library/tracked_project_and_paper_inventory.json`](../../../data/adna/governance/source_library/tracked_project_and_paper_inventory.json)
- [`data/adna/governance/source_library/tracked_project_and_paper_inventory.md`](../../../data/adna/governance/source_library/tracked_project_and_paper_inventory.md)
- [`data/adna/governance/source_library/project_registry.json`](../../../data/adna/governance/source_library/project_registry.json)
- [`data/adna/governance/source_library/paper_registry.json`](../../../data/adna/governance/source_library/paper_registry.json)
- [`data/adna/governance/source_library/source_intake_audit.json`](../../../data/adna/governance/source_library/source_intake_audit.json)
- [`data/adna/governance/source_library/source_intake_release_guard.json`](../../../data/adna/governance/source_library/source_intake_release_guard.json)
- [`data/adna/governance/source_library/project_sample_master_completeness.json`](../../../data/adna/governance/source_library/project_sample_master_completeness.json)
- [`data/adna/governance/source_library/project_sample_site_review.json`](../../../data/adna/governance/source_library/project_sample_site_review.json)
- [`data/adna/governance/source_library/sample_identity_ambiguity_ledger.json`](../../../data/adna/governance/source_library/sample_identity_ambiguity_ledger.json)
- [`data/adna/governance/source_library/sample_site_ambiguity_ledger.json`](../../../data/adna/governance/source_library/sample_site_ambiguity_ledger.json)
- [`data/adna/governance/source_library/sample_site_manual_curation_queue.json`](../../../data/adna/governance/source_library/sample_site_manual_curation_queue.json)
- [`data/adna/governance/source_library/projects/PRJEB36540/sample_master.json`](../../../data/adna/governance/source_library/projects/PRJEB36540/sample_master.json)
- [`data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json`](../../../data/adna/governance/source_library/projects/PRJEB36540/sample_sites.json)

## What This Surface Answers

- Which tracked projects still need paper capture.
- Which papers have archived supplementary material.
- Which projects already carry archive-native sample identifiers.
- Which projects already ship a checked project sample master with row-level lineage.
- Which recovered sample rows already have direct site evidence and which still sit at project-level or region-level locality posture.
- Which projects already have enough structured evidence for automatic sample-site extraction and which remain in the manual curation queue.
- Which projects still have unresolved sample counts or unrecovered sample identities.
- Which projects are intentionally retained as rejected reference rows instead of
  silently disappearing.

The point of this inventory is breadth before map filtering. The Nordic atlas is
downstream. The tracked project and paper inventory is the durable intake view
for the future global animal aDNA database.

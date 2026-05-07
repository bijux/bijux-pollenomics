---
title: Project, Paper, and Supplement Capture
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-07
---

# Project, Paper, and Supplement Capture

At this stage of `bijux-pollenomics`, the real data task is not sequencing
analysis. It is evidence capture: archive metadata, paper linkage,
supplementary-material retrieval, and extraction of sample and site hints that
can later become curated rows.

The primary navigation now breaks that evidence chain into dedicated project,
paper, supplement, sample, site, chronology, coordinate, and output pages.
Use this legacy overview if you want one short bridge across those surfaces.

## What To Inspect

- [`data/adna/governance/source_library/project_registry.json`](../../../data/adna/governance/source_library/project_registry.json)
- [`data/adna/governance/source_library/paper_registry.json`](../../../data/adna/governance/source_library/paper_registry.json)
- [`data/adna/governance/source_library/supplement_registry.json`](../../../data/adna/governance/source_library/supplement_registry.json)
- [`data/adna/governance/source_library/source_blockers.json`](../../../data/adna/governance/source_library/source_blockers.json)
- [Projects](../projects/index.md)
- [Papers](../papers/index.md)
- [Supplements](../supplements/index.md)
- [Animal Project and Paper Inventory](./animal-project-and-paper-inventory.md)

## Current Rule

If the repository cannot point to readable project metadata, paper context, or
supplementary support for a sample or site claim, that weakness should stay
visible in the tracked files and downstream audits.

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

## What To Inspect

- [`data/adna/governance/source_library/project_registry.json`](../../../data/adna/governance/source_library/project_registry.json)
- [`data/adna/governance/source_library/paper_registry.json`](../../../data/adna/governance/source_library/paper_registry.json)
- [`data/adna/governance/source_library/supplement_registry.json`](../../../data/adna/governance/source_library/supplement_registry.json)
- [`data/adna/governance/source_library/source_blockers.json`](../../../data/adna/governance/source_library/source_blockers.json)

## Current Rule

If the repository cannot point to readable project metadata, paper context, or
supplementary support for a sample or site claim, that weakness should stay
visible in the tracked files and downstream audits.

---
title: Sources
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-08
---

# Sources

The repository brings together several different source families. Some are
primary pollenomics context, such as pollen records. Others are contextual
layers, such as archaeology or animal ancient DNA. They belong on one site,
but they should not be described as if they all answer the same question.

## Main Source Families

| Family | Main role in `bijux-pollenomics` | Start here |
| --- | --- | --- |
| LandClim | pollen sequence and REVEALS context | [LandClim](landclim.md) |
| Neotoma | paleoecological pollen-site context | [Neotoma](neotoma.md) |
| SEAD | environmental archaeology context | [SEAD](sead.md) |
| RAÄ | Sweden-specific archaeology context | [RAÄ](raa.md) |
| Boundaries | country framing and filtering | [Boundaries](boundaries.md) |
| AADR | human ancient DNA context | [AADR](aadr.md) |
| Animal source intake | project, paper, supplement, and sample recovery for non-human aDNA | [Animal source intake](animal-source-intake.md) |

## Start Here

- [Source comparison](source-comparison.md) for the shortest cross-family overview
- [Source family matrix](source-family-matrix.md) for the repository-wide balance view
- [Animal source intake](animal-source-intake.md) for project, paper, supplement, and sample-recovery status

## Direct Files

- [`data/adna/governance/source_library/project_registry.json`](../../../data/adna/governance/source_library/project_registry.json)
- [`data/adna/governance/source_library/paper_registry.json`](../../../data/adna/governance/source_library/paper_registry.json)
- [`data/adna/governance/source_library/supplement_registry.json`](../../../data/adna/governance/source_library/supplement_registry.json)
- [`data/adna/governance/source_library/project_source_evidence_matrix.json`](../../../data/adna/governance/source_library/project_source_evidence_matrix.json)
- [`docs/report/repository_source_family_matrix.json`](../../report/repository_source_family_matrix.json)

## What This Section Should Make Clear

- different source families do different jobs
- pollen, archaeology, boundaries, and aDNA should stay distinguishable
- animal ancient DNA depends on project and supplement recovery before it becomes sample-backed evidence
- public outputs are downstream of those source and intake decisions

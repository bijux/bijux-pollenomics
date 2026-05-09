---
title: Data Directory Layout
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-09
---

# Data Directory Layout

The repository stores data in a few deliberately different places so that
source material, normalized evidence, and public outputs do not blur together.

## Main Directories

| Path | What it is for |
| --- | --- |
| `data/` | repository-owned source material and normalized data |
| `data/adna/species/<latin_name>/` | species-centered animal ancient DNA recovery and normalization |
| `data/adna/governance/` | cross-species audits, ledgers, and source registries |
| `data/adna/final/` | shared downstream animal data prepared for atlas or country publication |
| `docs/report/` | public-facing report bundles and map support files |
| `data/source_family_contracts.json` | stage and ownership contract for each source family |
| `data/source_fact_ownership_registry.json` | governing surface for recurring facts such as project inventory or sample identity |
| `data/evidence_artifact_contracts.json` | file-contract standard for project, paper, sample, site, region, and country artifacts |

## Animal Ancient DNA Layout

The animal ancient DNA tree is split three ways because those files do
different jobs:

- `data/adna/species/<latin_name>/` keeps species-owned recovery and normalized evidence files.
- `data/adna/governance/` keeps the cross-species audits that compare projects, supplements, chronology, and mapping readiness.
- `data/adna/final/` keeps shared downstream products after the species-level evidence has already been organized.

## Reader Anchors

- `data/source_family_contracts.json`
- `data/source_family_evidence_stage_matrix.json`
- `data/source_fact_ownership_registry.json`
- `data/evidence_artifact_contracts.json`
- `data/adna/species/ovis_aries/`
- `data/adna/species/equus_caballus/`
- `data/adna/species/bos_taurus/`
- `data/adna/species/canis_lupus_familiaris/`
- `data/adna/species/camelus_dromedarius/`
- `data/adna/species/rangifer_tarandus/`
- `data/adna/species/equus_asinus/`
- `data/adna/species/felis_catus/`
- `data/adna/governance/source_library/`
- `data/adna/governance/surface_role_registry.json`
- `data/adna/governance/source_library/project_surface_contract.json`
- [`docs/report/countries/sweden/`](../../../report/countries/sweden/README.md)
- [`docs/report/world/`](../../../report/world/world_map.html)

## Why This Layout Matters

Readers should be able to tell the difference between:

- a source record that has only been captured,
- a sample or locality claim that has been normalized,
- and a report or atlas row that is ready for public reading.

If those layers were stored together without explanation, the repository would
look more complete than its evidence actually is.

The checked-in contract files now make that split explicit, and the governance
role registry prevents `data/adna/governance/` from reading like one shapeless
overflow directory.

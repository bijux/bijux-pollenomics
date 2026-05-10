---
title: Data Architecture Handbook
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-05-10
---

# Data Architecture Handbook

This page explains how the repository tree is organized so you can tell which
files capture upstream material, which ones govern evidence, which ones review
it, and which ones publish it.

## The Four Stages

Every tracked source family should be readable through four durable stages:

1. capture: the repository records what came from upstream
2. normalization: the repository reshapes that material into owned evidence files
3. review: the repository states what is thin, blocked, conflicted, or safe
4. publication: the repository emits public bundles, atlas inputs, or map layers

You do not need to memorize those names, but you do need the distinction. A
report page is not the same thing as a governing evidence file, and a raw
supplement is not the same thing as a reviewed sample record.

The machine-readable checkpoints for those stages live in:

- `data/source_family_contracts.json`
- `data/source_family_evidence_stage_matrix.json`
- `data/source_fact_ownership_registry.json`
- `data/evidence_artifact_contracts.json`

## Source Families

| Source family | Raw capture | Normalized evidence | Review surface | Publication surface |
| --- | --- | --- | --- | --- |
| LandClim | `data/landclim/raw/` | `data/landclim/normalized/` | `data/source_family_evidence_stage_matrix.json` | `docs/report/world/` |
| Neotoma | `data/neotoma/raw/` | `data/neotoma/normalized/` | `data/source_family_evidence_stage_matrix.json` | `docs/report/world/` |
| SEAD | `data/sead/raw/` | `data/sead/normalized/` | `data/source_family_evidence_stage_matrix.json` | `docs/report/world/` |
| RAÄ | `data/raa/raw/` | `data/raa/normalized/` | `data/source_family_evidence_stage_matrix.json` | `docs/report/world/` |
| Boundaries | `data/boundaries/raw/` | `data/boundaries/normalized/` | `data/source_family_evidence_stage_matrix.json` | `docs/report/world/` |
| AADR | `data/aadr/` | `data/adna/species/homo_sapiens/normalized/` | `data/adna/species/homo_sapiens/review/` | `docs/report/<country>/` |
| Animal ancient DNA | `data/adna/governance/source_library/` | `data/adna/species/<latin_name>/normalized/` | `data/adna/governance/` | `data/adna/final/` and `docs/report/` |

## Where Key Facts Are Owned

The repository repeats some concepts across recovery, normalization, and
publication surfaces. That is unavoidable. What matters is that one governing
surface owns each recurring fact.

- Project inventory is governed by `data/adna/governance/source_library/project_registry.json`.
- Paper inventory is governed by `data/adna/governance/source_library/paper_registry.json`.
- Sample identity is governed by `data/adna/governance/source_library/projects/<project_accession>/sample_master.json`.
- Sample-to-site linkage is governed by `data/adna/governance/source_library/projects/<project_accession>/sample_sites.json`.
- Locality evidence is governed by `data/adna/governance/source_library/projects/<project_accession>/sample_locality_evidence.json`.
- Chronology evidence is governed by `data/adna/governance/source_library/projects/<project_accession>/sample_chronology_evidence.json`.
- Species-normalized animal records are governed by `data/adna/species/<latin_name>/normalized/sample_records.json`.
- Region-level animal atlas inputs are governed by `data/adna/final/atlas/animal_atlas_point_candidates.json`.
- Country publication bundles are governed by `docs/report/countries/<country_slug>/<country_slug>_aadr_<version>_bundle.json`.

The full registry is in `data/source_fact_ownership_registry.json`.

That registry matters because the same sample or locality can appear in several
downstream places. What matters is having one stable answer to a simple
question: which file should win when two outputs appear to say the same thing
at different levels of detail?

## Why The Governance Tree Exists

`data/adna/governance/` should not be read as one vague side bucket.

- `data/adna/governance/source_library/` owns source recovery and per-project evidence capture.
- `data/adna/governance/*.json` owns cross-species review, truth, caveats, and coverage posture.
- `data/adna/governance/*product*.json` owns publication accounting and shipment discipline.

The repository states that split directly in
`data/adna/governance/surface_role_registry.json`.

## File Contracts

The repository publishes one file-contract standard so the recurring artifact
scopes stay predictable:

- project source bundles
- paper supporting-material manifests
- sample foundation surfaces
- site evidence surfaces
- regional atlas bundles
- country publication bundles

That contract is published in `data/evidence_artifact_contracts.json`, and the
shared animal project subtree contract is published in
`data/adna/governance/source_library/project_surface_contract.json`.

## When This Page Is Most Useful

Use this page when the repository feels sprawling and the immediate question is
not about one species or one map, but about where evidence becomes reviewable
and which file actually governs the claim you care about.

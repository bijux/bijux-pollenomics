---
title: Artifact Contracts
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Artifact Contracts

A published artifact is a claim-bearing product, not merely a generated file.
Its contract identifies the product scope, membership, evidence roles,
traceability, warnings, and exclusions needed to interpret it honestly.

## Publication Families

| Family | Reader question | Governing material |
| --- | --- | --- |
| world | What evidence can be viewed without a regional assumption? | world bundle, publication contract, evidence surface, traceability, and scientific review |
| Europe-plus | Which wider European records qualify under one regional scope? | regional bundle, scope metadata, feature tables, and exclusions |
| Nordic | Which records qualify for Nordic comparison? | Nordic bundle, country membership, evidence roles, and point traceability |
| country | What is admitted within one named country? | country manifest, samples, species, localities, citations, warnings, and summary |
| Sweden lake | Which basins remain interesting across evidence and sensitivity views? | ranking manifest, scenarios, registry, distance bands, map, and fieldwork-preparation packet |
| repository review | What is currently supported, incomplete, or blocked? | readiness, honesty, coverage, exclusion, truth-posture, and claim-audit reports |

```mermaid
flowchart LR
    Evidence["governed evidence"] --> Decision["admission or qualification"]
    Decision --> Manifest["product manifest"]
    Manifest --> Rows["structured rows and geometry"]
    Manifest --> Narrative["reader explanation"]
    Manifest --> Limits["warnings and exclusions"]
    Rows --> Product["map, table, or report"]
    Narrative --> Product
    Limits --> Product
```

## Bundle Anatomy

The manifest is the entrypoint for a bundle. It records what belongs to the
product and connects the visible rendering to structured members. Supporting
files then divide responsibilities:

- CSV and JSON expose rows, summaries, and machine-readable decisions;
- GeoJSON exposes geometry together with feature properties and evidence role;
- citations identify external evidence and source context;
- warnings preserve qualifications that affect interpretation;
- exclusions explain why known candidates are absent;
- Markdown and HTML provide a readable view over those governed materials.

No rendering outranks its inputs. If a map label and a structured evidence row
disagree, the discrepancy is a publication defect to investigate rather than
a choice between two equally authoritative stories.

## Reading One Feature

Start with the visible feature identifier, locate it in the bundle membership
or traceability surface, follow the governing evidence-row identifier, and
then inspect the source, locality, chronology, and coordinate basis. This path
separates six questions that a single marker cannot answer:

1. What object is shown?
2. Why is it in this product?
3. Which evidence role does it have?
4. Where and when is it supported?
5. Which source or curation decision owns that support?
6. Which warnings limit reuse?

## Direct Inspection

- [world product](../../../report/world/README.md)
- [world publication contract](../../../report/world/world_map_publication_contract.md)
- [world point traceability](../../../report/world/world_point_traceability.md)
- [Sweden country bundle](../../../report/countries/sweden/README.md)
- [Sweden lake evidence richness](../../../report/countries/sweden/sweden_lake_evidence_richness_v66.md)
- [animal atlas readiness](../../../report/animal_atlas_readiness.md)
- [animal atlas exclusions](../../../report/animal_atlas_exclusion_report.md)
- [repository claim audit](../../../report/repository_claim_audit.md)

## Contract Limits

A published bundle establishes declared membership and traceability at its
recorded state. It does not establish representative sampling, exhaustive
source recovery, equal maturity across evidence families, or suitability for
an undeclared analysis. Those stronger claims require separate evidence.

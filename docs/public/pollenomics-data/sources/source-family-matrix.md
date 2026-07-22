---
title: Source Family Matrix
audience: reader
type: reference
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Source Family Matrix

The source-family matrix describes what each governed family contributes and
where its authority stops. It is a role and lifecycle inventory, not a ranking
of scientific importance.

## Governed Families

| Family | Domain | Evidence role | Normalized unit | Characteristic review | Published use |
| --- | --- | --- | --- | --- | --- |
| LandClim | pollen context | primary context | site sequence and grid cell | freshness, coverage, temporal posture | world and regional pollen layers |
| Neotoma | pollen context | primary context | pollen-site record | site-level temporal comparability | world and regional pollen layers |
| SEAD | archaeology context | contextual domain | environmental-archaeology site | access, temporal, and normalization legibility | archaeology context layers |
| RAÄ | archaeology context | contextual domain | Swedish registry record and density surface | coverage and spatial interpretation | Sweden-focused archaeology layers |
| SVAR | hydrography | sampling context | lake, catchment, and water-body record | registry coverage and candidate linkage | Sweden lake products and overlays |
| boundaries | geography | framing | country and regional polygon | geometry and scope fitness | world, regional, and country selection |
| AADR | human ancient DNA | direct evidence | release-owned sample metadata | sample locality and chronology posture | human aDNA country and regional layers |
| animal aDNA | non-human ancient DNA | direct evidence | sample-owned species record | project, paper, supplement, place, time, coordinate, and archive integrity | admitted atlas and country members |

The machine-readable authority for these roles and lifecycle roots is
`data/source_family_contracts.json`. Publication maturity is reported
separately because a family can have a complete structural contract while
remaining scientifically qualified.

## Lifecycle Coverage

```mermaid
flowchart LR
    Contract["source-family contract"] --> Capture["captured layer"]
    Capture --> Normalized["normalized layer"]
    Normalized --> Review["reviewed layer"]
    Review --> Published["published layer"]
    Contract --> Metrics["coverage metrics"]
    Metrics --> Review
```

Every family declares captured, normalized, reviewed, and published surfaces.
Those surfaces may be family-owned directories or shared cross-family
registries, but their responsibilities remain distinct.

## Authority Boundaries

| Family class | May establish | Cannot establish alone |
| --- | --- | --- |
| direct evidence | a bounded claim about its governed observation or sample | collection completeness or representativeness |
| primary context | source-backed environmental setting central to comparison | identity, place, or time for an unrelated sample |
| contextual domain | surrounding archaeological or environmental interpretation | direct biological association |
| sampling context | candidate selection and fieldwork reasoning | feasibility, preservation, permits, or scientific outcome |
| geographic framing | membership in a declared spatial scope | scientific support for a member record |

## Read Across A Family, Then Down A Claim

The matrix supports two different readings:

```mermaid
flowchart LR
    Family["one source family"] --> Lifecycle["capture through publication"]
    Claim["one proposed claim"] --> Dimensions["identity, semantics, space, time, and role"]
    Lifecycle --> Fitness["family readiness for this claim"]
    Dimensions --> Fitness
```

Reading across one family shows whether its lifecycle is intact. Reading down
one claim compares only the dimensions needed for that claim. Neither reading
authorizes a global family ranking. LandClim can be mature for pollen context
while AADR is mature for release-owned human metadata; their record counts and
roles are not competing measures of quality.

This distinction also prevents lifecycle completion from being mistaken for
scientific readiness. A family may have captured, normalized, reviewed, and
published artifacts while still carrying a material temporal or geographic
qualification.

## Maturity Is Multidimensional

Maturity cannot be reduced to one color or score. Review source identity,
acquisition reproducibility, normalized semantics, spatial support, temporal
support, evidence-role clarity, product admission, and visible limits
independently.

A family can be:

- structurally complete but temporally uneven;
- geographically broad but locally weak;
- scientifically valuable but context-only;
- well captured but not publication-ready;
- admitted to one product while excluded from another.

## Evaluate Maturity By Claim

Use the matrix as a set of independent questions rather than a ladder:

| Axis | Question | Failure must remain visible as |
| --- | --- | --- |
| identity | Can each governed member be traced to one source-native object and release? | unresolved identity, collision, or missing locator |
| acquisition | Were expected assets captured under recorded access and use conditions? | blocked asset, partial capture, or unknown denominator |
| semantics | Does normalization preserve the family's observation unit and field meaning? | unsupported mapping, ambiguous value, or schema drift |
| space | Is location represented at the precision supported by the source? | approximate, regional, substituted, withheld, or unresolved geometry |
| time | Is chronology numeric, contextual, broad, absent, or inapplicable? | explicit temporal class and uncertainty |
| role | Is the family direct evidence, primary context, contextual, sampling context, or framing? | refusal of role substitution |
| publication | Which named product admits the record and under what qualification? | exclusion, deferral, warning, or empty membership |

A family can be strong on one axis and weak on another without contradiction.
For example, a stable national registry can have excellent identity and spatial
coverage while carrying no uniform chronology suitable for same-period
comparison.

```mermaid
flowchart LR
    Family["source family"] --> Identity["identity and acquisition"]
    Family --> Meaning["unit and semantics"]
    Family --> Space["spatial support"]
    Family --> Time["temporal support"]
    Family --> Role["evidence role"]
    Identity --> Fitness["claim-specific fitness"]
    Meaning --> Fitness
    Space --> Fitness
    Time --> Fitness
    Role --> Fitness
    Fitness --> Product["qualified product decision"]
```

## Current Review Surfaces

- [source-family matrix data](../../../report/repository_source_family_matrix.json)
- [cross-domain evidence matrix](../../../report/repository_cross_domain_evidence_matrix.json)
- [source explainer audit](../../../report/repository_source_explainer_audit.md)
- [source acquisition queue](../../../report/repository_source_acquisition_queue.json)
- [source ecosystem review](../../../report/repository_source_ecosystem_review.md)

These reports describe the checked-in state. They do not replace the captured
and normalized records that govern individual facts.

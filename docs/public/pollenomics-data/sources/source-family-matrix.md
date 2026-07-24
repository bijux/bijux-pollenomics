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
Each stage is proven by the exact materialized artifacts named in the family
contract. A publication can remain committed when an earlier current-stage
artifact is absent; the matrix preserves both facts rather than inferring the
missing authority backward from its descendant.

### Checked-In Stage Metrics

The current stage matrix reports this materialized state:

| Family | Raw | Normalized | Reviewed | Published | Checked-in metric and interpretation |
| --- | --- | --- | --- | --- | --- |
| LandClim | present | present | missing | present | 492 sequences and 88 model cells; the source-specific review artifact is absent |
| Neotoma | present | present | present | present | 200 normalized points; temporal capability remains member-specific |
| SEAD | present | present | present | present | 2,172 normalized points; review supports a contextual, not uniformly dated, role |
| RAÄ | present | present | missing | present | 761,917 registry and 318,265 heritage records; source-specific review is absent |
| boundaries | present | present | missing | present | four country geometries frame membership without scientific weight |
| SVAR | present | missing | missing | present | a 40,565-lake summary and retained products exist without the contracted normalized registry and review |
| AADR | present | missing | missing | present | three v66 capture files and retained products exist without governed Homo sapiens normalized and review members |
| animal aDNA | present | present | present | present | 10 species, 40 projects, and 894 species-owned sample-foundation rows are materialized |

The animal lifecycle count is the population of species-owned foundation rows,
not the 868 recovered project sample-master identities or the 234 admitted
point-evidence rows. All three quantities are valid only with their governing
unit. The corrected metric no longer reports zero merely because it was
reading a field name that the foundation summary does not own.

### Read The Matrix As An Evaluated Snapshot

The stage matrix is recomputed from the artifacts named by the family
contracts. It reports what is materially present in the inspected repository
state; it is not a history of every successful collection or publication.

That distinction explains an otherwise surprising pattern: a family can show
`published: present` while `normalized` or `reviewed` is missing. The product
is a retained checked-in descendant, while the prerequisite named by the
current contract is absent. The matrix refuses to infer the prerequisite from
the descendant.

| Matrix pattern | Defensible interpretation | Invalid inference |
| --- | --- | --- |
| raw present; normalized missing | capture exists, but the current normalized contract is not materialized | normalization must be valid because raw bytes exist |
| normalized present; review missing | represented members exist without the required family review surface | every normalized member is publication-ready |
| published present; prerequisite missing | a retained product exists but full rebuildability is not demonstrated | the prerequisite is implicitly present |
| all stages present | every required stage has a materialized artifact | every member supports every scientific use |

Historical continuity belongs in capture receipts, product manifests, and
revision history. Current stage presence belongs here. Mixing those questions
would turn retained outputs into evidence for missing preparation work.

## Authority Boundaries

| Family class | May establish | Cannot establish alone |
| --- | --- | --- |
| direct evidence | a bounded claim about its governed observation or sample | collection completeness or representativeness |
| primary context | source-backed environmental setting central to comparison | identity, place, or time for an unrelated sample |
| contextual domain | surrounding archaeological or environmental interpretation | direct biological association |
| sampling context | candidate selection and fieldwork reasoning | feasibility, preservation, permits, or scientific outcome |
| geographic framing | membership in a declared spatial scope | scientific support for a member record |

## Observation Units And Safe Joins

Cross-family analysis is valid only when the join preserves the unit on both
sides. Similar labels and nearby coordinates are candidates for review, not
keys.

| Family | Stable member identity | Safe cross-domain relation | Unsafe shortcut |
| --- | --- | --- | --- |
| LandClim | governed site or grid-cell identity | explicit site/grid relation with stated temporal basis | treating a model cell as an observed pollen sequence |
| Neotoma | database and site/deposit identifiers | retained database identity plus reviewed site relation | joining on site name alone |
| SEAD | SEAD site identifier | declared distance or containment from its reported point | interpreting proximity as sample association |
| RAÄ | national registry identity | declared spatial relation within Swedish registry scope | replacing SEAD or specimen provenance with a nearby heritage record |
| SVAR | registered water-body identity | reviewed candidate-to-lake relation | assuming a same-named water body is the intended sampling basin |
| boundaries | governed geometry identity and version | point-in-polygon membership | using country membership as coordinate validation |
| AADR | release-owned sample identifier | explicit reviewed locality or publication relation | matching a human sample by place label alone |
| animal aDNA | project, accession, sample, and evidence locators | sample-owned locality, chronology, and source relations | collapsing all samples in one project to one place or date |

Derived relations retain both member identifiers, the rule that connected
them, input versions, and the evidence posture of each input. This allows a
distance, containment, or comparison to be recomputed without turning it into
source truth.

## Product Admission Matrix

The same family can be eligible for one product and ineligible for another.

| Product use | Minimum source posture | Refusal condition |
| --- | --- | --- |
| spatial inventory | stable member identity and supported geometry | unresolved identity or geometry |
| country membership | supported geometry and governed boundary version | missing geometry or undeclared boundary basis |
| time-aware comparison | comparable numeric intervals with retained basis | absent, contextual-only, or incomparable chronology |
| contextual overlay | declared contextual role and reproducible spatial relation | context presented as direct association |
| specimen claim | sample-owned identity and claim-specific evidence | project-, paper-, or locality-level evidence substituted for the sample |
| fieldwork prioritization | governed lake identity plus explicit decision inputs and caveats | registry presence or proximity presented as feasibility |

Publication is therefore a claim-specific decision, not the final stage of a
uniform source pipeline. Eligibility must be recomputed when the source,
normalization, boundary, comparison rule, or product contract changes.

## Read Across A Family, Then Down A Claim

The matrix supports two different readings:

```mermaid
flowchart LR
    Family["one source family"] --> Lifecycle["capture through publication"]
    Claim["one proposed claim"] --> Dimensions["identity, semantics, space, time, and role"]
    Lifecycle --> Fitness["family readiness for this claim"]
    Dimensions --> Fitness
```

Reading across one family shows which lifecycle evidence is materialized. Reading down
one claim compares only the dimensions needed for that claim. Neither reading
authorizes a global family ranking. LandClim can be mature for pollen context
while AADR has a governed release capture but lacks its contracted normalized
and review members; their record counts and roles are not competing measures
of quality.

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

The [revision and state model](../database/revision-and-state-model.md)
explains why lifecycle presence, record fitness, and publication membership
remain separate database states.

---
title: Evidence Database
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Evidence Database

Pollenomics is built on a version-controlled evidence database. The database
retains source captures, governed identities, normalized facts, scientific
decisions, unresolved states, and publication membership. Maps and reports
are projections over that state; they are not the authority from which source
or sample facts are recovered.

## What The Database Governs

| Concern | Governed representation | Why it matters |
| --- | --- | --- |
| source identity | family, owner, release or accession, acquisition, licence posture, and content identity | establishes which upstream material was used |
| object identity | stable keys for releases, projects, papers, samples, sites, claims, and products | prevents names and row positions from becoming joins |
| fact ownership | one declared authority for each recurring fact | makes disagreement resolvable |
| evidence relations | typed links between objects with provenance and cardinality | keeps a plausible association from becoming an asserted identity |
| curation state | accepted, qualified, conflicted, unresolved, excluded, deferred, or outside scope | preserves negative and partial evidence |
| publication membership | product, version, scope, member identity, role, and admission decision | explains why an object appears in a public result |

The database is file-backed rather than service-backed. JSON, CSV, GeoJSON,
source artifacts, review ledgers, and manifests carry different parts of the
model. Their authority comes from explicit contracts and relations, not from
their file format.

### Five Database Questions

The database is designed to answer five classes of question without treating
one denormalized export as universal truth:

| Query | Start with | Resolve to |
| --- | --- | --- |
| identity | native key, accession, DOI, governed key, or product member | one typed object plus aliases and source locators |
| lineage | governed claim or public member | supporting artifact, source-native record, transformation, fact owner, and decision |
| population | source family, evidence posture, species, geography, or product | eligible members, admitted members, non-members, and denominator |
| impact | changed artifact, fact, relation, or rule | dependent claims, decisions, manifests, and rendered products |
| absence | expected object or relation | capture, normalization, curation, admission, scope, filter, or integrity boundary that explains non-membership |

```mermaid
flowchart TD
    Query["database question"] --> Class{"query class"}
    Class --> Identity["identity graph"]
    Class --> Lineage["evidence lineage"]
    Class --> Population["population accounting"]
    Class --> Impact["forward dependency graph"]
    Class --> Absence["anti-join and refusal state"]
    Identity --> Answer["typed, revision-bound answer"]
    Lineage --> Answer
    Population --> Answer
    Impact --> Answer
    Absence --> Answer
```

Every answer is revision-bound. “Which record is this?” and “why is it absent?”
can change when source identity, evidence, scope, or admission rules change,
even when the display label remains stable.

### Files Are Projections Of A Typed Graph

Directory position is useful for discovery, but the database model is the
network of typed identities and evidence-bearing relations:

```mermaid
flowchart LR
    Artifact["captured artifact"] -->|contains row| SourceRow["source-native record"]
    SourceRow -->|supports identity| Object["governed object"]
    SourceRow -->|supports claim| Claim["typed evidence claim"]
    Object -->|subject of| Claim
    Claim -->|evaluated by| Decision["curation or admission decision"]
    Decision -->|manifests as| Member["publication member"]
```

A JSON row can serialize several nodes for convenience, but it does not erase
their types. The source row is not the governed sample, the sample is not its
locality claim, and the locality claim is not the point feature. Readers
should join on stable typed identities and declared relation keys, never on
display labels, row positions, or coordinate equality.

## Database Boundaries

The database has three deliberately different surfaces:

| Surface | Primary responsibility | Read it as |
| --- | --- | --- |
| source and normalized data under `data/` | captured bytes, source-native facts, normalized evidence, provenance, and review state | the governed evidence state |
| publication data under `docs/report/` | versioned projections, manifests, accounting, and reader-facing products | a descendant of governed evidence |
| public documentation under `docs/public/` | contracts, interpretation rules, limitations, and navigation | an explanation of the system, never a substitute for evidence |

The boundary matters during correction. A statement in a guide cannot repair
a missing normalized artifact. A map cannot become the authority for the
sample or locality facts it displays. A governed JSON record does not become
reader-facing merely because it is committed beside the website source.

## Evidence Lifecycle

```mermaid
flowchart LR
    Capture["versioned source capture"] --> Object["governed objects and source-native facts"]
    Object --> Normalize["normalized claims and typed relations"]
    Normalize --> Review["curation decisions and review state"]
    Review --> Admission{"product-specific admission"}
    Admission -->|admit or qualify| Projection["manifested publication projection"]
    Admission -->|exclude or defer| Negative["retained negative evidence"]
```

Movement through the lifecycle does not transfer authority. A normalized
sample remains subordinate to its project-owned sample evidence. A published
point remains subordinate to the locality and coordinate claims that made it
eligible. An exclusion remains part of the database even though it is absent
from the visible projection.

## Database Contracts

Three registries make the file-backed model inspectable:

| Contract | Governs |
| --- | --- |
| `data/source_family_contracts.json` | source roles and captured, normalized, reviewed, and published roots |
| `data/source_fact_ownership_registry.json` | the authority for recurring source, sample, locality, chronology, species, and publication facts |
| `data/evidence_artifact_contracts.json` | required project, paper, sample, site, atlas, and country artifact sets |

`data/collection_summary.json` binds the current collected source versions,
retrieval state, hashes, and replacement rules. The evidence-stage matrix
reports lifecycle presence and counts, but its presence labels do not grant
uniform scientific readiness to every member.

Stage presence is established by the concrete artifacts named in the source
family contract. An empty directory, a `.gitkeep` file, a family summary, or
the evidence-stage matrix itself cannot stand in for a missing normalized or
review artifact. This makes absence machine-readable instead of allowing
repository shape to imply work that has not been materialized.

## Inspect A Database Claim

For a claim in a table, map, or narrative, inspect in this order:

1. identify the product and its manifested member;
2. follow the member to the governed sample, site, source, or contextual object;
3. locate the fact owner in `source_fact_ownership_registry.json`;
4. inspect the supporting locator, method, precision, and review posture;
5. read exclusions and unresolved competitors before interpreting coverage;
6. confirm that the evidence and product belong to the same repository state.

This order separates *what the product says* from *why the database permits it
to say that*. It also exposes the exact boundary at which a result becomes
qualified, conflicted, or non-reproducible.

### Minimum Inspection Packet

An independently reviewable answer retains more than the displayed value:

| Packet member | Why it is required |
| --- | --- |
| repository revision | fixes the joined database snapshot |
| product and member identity | fixes the projection and declared role |
| governed object identity | names the sample, site, source record, or context object |
| claim and relation identities | distinguishes identity, place, time, coordinate, and membership assertions |
| source artifact and locator | permits recovery of the supporting material |
| decision posture and rule | explains admission, qualification, exclusion, or refusal |
| precision, conflict, and recovery state | preserves the ceiling on reuse |

If an extract cannot supply this packet, it may still support display or
orientation, but it cannot independently carry the database claim.

## Read The Database In Two Directions

```mermaid
flowchart LR
    Upstream["upstream identity"] --> Captured["captured artifact"]
    Captured --> Authority["governing evidence authority"]
    Authority --> Decision["curation and admission decision"]
    Decision --> Member["published member"]
    Member -. "audit backward" .-> Decision
    Decision -. "impact forward" .-> Member
```

Backward traversal answers what supports a visible claim. Forward traversal
answers which products depend on a corrected source or evidence fact. Both
directions must preserve object type, role, version, and qualification.

## Continue By Question

| Question | Contract |
| --- | --- |
| Which objects exist and how may they relate? | [Object and relation model](object-and-relation-model.md) |
| What does a database state mean at one revision? | [Revision and state model](revision-and-state-model.md) |
| How does upstream material enter the database? | [Source families](../sources/index.md) |
| How are claims evaluated and conflicts retained? | [Curation](../curation/index.md) and [evidence chain](../evidence/index.md) |
| How does governed state become a map, table, or report? | [Publications](../publications/index.md) |

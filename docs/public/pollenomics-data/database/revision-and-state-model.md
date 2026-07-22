---
title: Revision and State Model
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Revision And State Model

A Git revision is a Pollenomics database snapshot. Trust depends on the
snapshot carrying authorities, required companions, review decisions,
manifests, exclusions, and public projections from the same causal state.

The [domain language](../domain-language.md) defines revision, lineage,
posture, product, and projection as separate identities.

## Lifecycle State Is Not A Quality Score

| State | Establishes | Does not establish |
| --- | --- | --- |
| captured | identified material entered the repository | correct interpretation or completeness |
| normalized | source meaning has a repository representation | fitness for a scientific claim |
| reviewed | named dimensions were evaluated under declared rules | fitness for every product |
| published | a governed object entered one manifested projection | universal acceptance or source completeness |

A family can be present at every lifecycle stage while individual records are
qualified, unresolved, or excluded. Stage presence reports infrastructure and
coverage state; record-level decisions report scientific fitness.

## How Stage Presence Is Proven

`data/source_family_contracts.json` names the artifact or artifacts that prove
each stage for each source family. The state evaluator requires those named
artifacts to contain governed content.

| Observation | Stage result | Reason |
| --- | --- | --- |
| contracted normalized GeoJSON exists and is non-empty | normalized may be `present` | the declared normalized evidence is materialized |
| normalized directory contains only `.gitkeep` | normalized is `missing` | directory structure is not evidence |
| a summary exists but the contracted member dataset does not | normalized is `missing` | counts cannot replace the governed records they summarize |
| evidence-stage matrix exists but a source-specific review does not | reviewed is `missing` | a status report cannot certify its own review input |
| a retained publication exists while an upstream stage is missing | published is `present`, readiness remains blocked | historical product existence and current reproducibility are different facts |

This last condition is intentional. A published artifact is not deleted merely
because the current database state exposes a missing prerequisite. Instead,
the matrix preserves the publication surface, marks the missing stage, and
sets a blocking posture. Readers can then distinguish retained output from a
product that can be regenerated and defended from the current snapshot.

## Claim And Membership States

| State | Meaning |
| --- | --- |
| accepted | the claim satisfies the declared evidence contract |
| qualified | the claim is usable only with an explicit limit |
| conflicted | incompatible supported values remain unresolved |
| unresolved | evidence is insufficient to select a defensible value |
| excluded | a known object fails a named product contract |
| deferred | a decision awaits recoverable evidence or review |
| outside scope | the object may be valid but is not part of the product population |

These states are database values. They must survive summaries and refreshes
even when only accepted and qualified members appear in a public map.

## Coherent Snapshot

```mermaid
flowchart TD
    Authority["governing authority changes"] --> Relations["dependent claims and relations"]
    Relations --> Decisions["curation and admission decisions"]
    Decisions --> Manifests["membership, exclusions, and accounting"]
    Manifests --> Views["tables, maps, reports, and warnings"]
    Views --> Coherence{"same revision and causal state?"}
    Coherence -->|yes| Snapshot["coherent database snapshot"]
    Coherence -->|no| Partial["partial state; publication refused"]
```

Updating a visible map without its manifest is a partial transaction. Updating
a normalized fact without reevaluating dependent admissions is also partial,
even if the map happens to remain visually unchanged.

### Evidence Changes Are Semantic Transactions

A coherent change begins at the earliest authority whose meaning changed and
ends only when every affected decision and projection has been accounted for:

| Authority change | Required transaction boundary |
| --- | --- |
| captured artifact replaced | capture identity, extraction locators, normalized descendants, review, and affected products |
| sample identity merged or split | aliases, project relations, dimension claims, species views, admissions, and member identities |
| locality or coordinate strengthened | prior claim, new provenance, point posture, geography predicates, and presentation caveats |
| chronology reclassified | source wording, normalized basis, comparability, temporal joins, and public labels |
| product rule changed | eligible population, decisions, manifest, exclusions, counts, and reader-facing claim |

```mermaid
flowchart LR
    Before["coherent prior snapshot"] --> Authority["governing change"]
    Authority --> Impact["typed dependent relations"]
    Impact --> Decisions["reevaluated decisions"]
    Decisions --> Products["regenerated products and accountability"]
    Products --> Compare["semantic and membership diff"]
    Compare --> After["coherent new snapshot"]
```

A transaction may legitimately produce no visible map change. In that case,
the review still explains why membership remained stable despite changed
evidence. Conversely, an unchanged total is not proof of a no-op because one
member or evidence class may have replaced another.

## Snapshot Invariants

A coherent revision satisfies all of these invariants:

- every repeated fact resolves to one declared authority;
- every admitted member resolves backward to typed evidence and a decision;
- every exclusion names a known object, rule, and product population;
- stage labels are reproducible from contracted artifacts, not directory names;
- public counts reconcile with manifests and their declared denominators;
- generated descendants do not become authorities for their own inputs;
- missing, conflicted, and unresolved states remain visible after refresh.

Violation of an invariant is a database defect even when every Markdown page
renders and every map opens.

### Snapshot Reconciliation Receipt

Before a revision is treated as one coherent evidence state, reconcile each
affected population through the complete lifecycle:

| Receipt member | Required reconciliation |
| --- | --- |
| source population | expected and captured members, additions, removals, retrieval failures, and content identities |
| normalized population | source-to-member mapping, exclusions, null states, identity merges or splits, and semantic changes |
| reviewed population | accepted, qualified, conflicted, unresolved, deferred, and refused members by claim dimension |
| admitted population | eligible denominator, product rule, admitted members, exclusions, and outside-scope members |
| published population | manifest members, stable feature identities, warnings, format parity, and parent–child scope relations |
| retained non-members | known objects absent from publication with one recoverable boundary and reason |

```mermaid
flowchart LR
    Source["captured population"] --> Normalized["normalized population"]
    Normalized --> Reviewed["reviewed population"]
    Reviewed --> Admitted["admitted population"]
    Admitted --> Published["manifested population"]
    Source --> NonMembers["accounted non-members"]
    Normalized --> NonMembers
    Reviewed --> NonMembers
    Admitted --> NonMembers
    Published --> Receipt["coherent snapshot receipt"]
    NonMembers --> Receipt
```

The populations need not have equal counts. Coherence means every transition
has a declared rule and every difference is accounted for at member level.
An unexplained equality is weaker evidence than an explained reduction.

## Version Identities

Different versions answer different questions:

| Identity | Fixes |
| --- | --- |
| upstream release or accession | the source program or archive material selected |
| captured content digest | the bytes or logical capture represented |
| schema version | the interpretation expected for one artifact shape |
| repository revision | the joined database state across authorities and descendants |
| product version | the declared membership and delivery contract |

None substitutes for another. A product filename containing `v66` does not
prove that every input comes from AADR v66, and an unchanged source release
does not prove unchanged normalized semantics.

### Coherent Read Set

A reproducible answer fixes all identities needed by the query, not only the
repository commit or product filename:

| Read-set identity | Why it must be fixed |
| --- | --- |
| repository revision | joins the checked-in authorities, decisions, and descendants |
| source family and upstream release | identifies the upstream population represented |
| captured content identity | distinguishes changed bytes or responses under the same release label |
| schema and rule identities | fixes how records were interpreted and admitted |
| product manifest identity | fixes scope, membership, roles, exclusions, and required companions |
| selected member and claim identities | fixes the exact evidence traversed by the answer |

Mixing a manifest from one revision with evidence rows from another produces a
plausible but ungoverned read. The same risk appears when a notebook caches a
normalized table while reopening a newer map, or when a copied GeoJSON loses
the manifest that identifies its product population. Reuse must either retain
the coherent read set or explicitly describe the result as an unverified
cross-revision comparison.

### A Modified Worktree Is A Candidate Snapshot

A commit names an immutable joined state. A worktree with modified governed
files does not. It is a candidate whose coherence must be established across
every affected authority and descendant before it can support the same claims
as a repository revision.

```mermaid
stateDiagram-v2
    [*] --> Revision: coherent committed snapshot
    Revision --> Candidate: authority or descendant modified
    Candidate --> Partial: dependents not reconciled
    Candidate --> Verified: identities and populations reconcile
    Partial --> Candidate: repair earliest incorrect boundary
    Verified --> Revision: commit complete owned state
```

Record the base revision and changed governed roots when inspecting a
candidate. A clean diff is not scientific proof, but an unnamed mixture of
committed and modified state cannot provide a reproducible database identity.

## Change Classes

| Change | Required review |
| --- | --- |
| new source release | identity, licence, schema, observation unit, coverage, and semantic diff |
| parser or normalization change | source-to-field lineage, null behavior, precision, and member equivalence |
| identity merge or split | aliases, relations, counts, species views, and every dependent product |
| locality or coordinate correction | spatial posture, containment, distances, maps, and exclusions |
| chronology correction | basis, interval semantics, overlap eligibility, summaries, and wording |
| product rule change | population, admissions, exclusions, manifests, counts, and public claims |

## Replacement And Failure

Collected source roots use staged replacement where declared by the collection
summary. A failed refresh preserves the preceding governed root. A successful
swap still requires semantic review: newer bytes can narrow coverage, expose a
conflict, or invalidate a previous publication decision.

External unavailability is not evidence that the governed state is false. It
is a blocked refresh condition. Conversely, a successful download is not
evidence that interpretation and publication remain valid.

## Reuse Contract

A reusable database extract retains the repository revision, product and
source versions, typed object identities, evidence roles, relation methods,
precision, admission posture, and material qualifications. If an extract
drops exclusions, unresolved states, or its denominator, it cannot carry the
same coverage claim as the governed snapshot.

For longitudinal comparison, retain both snapshot identities and compare
objects and relations before aggregate counts. The minimum diff classifies
added, removed, and modified identities; changed fact owners; relation changes;
decision changes; and publication effects. A textual changelog is useful
context, but the governed member-level diff is the evidence for what changed.

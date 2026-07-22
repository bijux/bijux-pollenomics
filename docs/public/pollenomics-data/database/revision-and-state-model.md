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

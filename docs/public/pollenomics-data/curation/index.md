---
title: Evidence Curation
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Evidence Curation

Curation is the accountable work between acquiring a source and publishing a
claim. It determines which object a source row describes, which facts the row
supports, how precise those facts are, and whether they are fit for one
declared product. Normalization makes records structurally consistent;
curation makes their scientific meaning and limits explicit.

## The Curation Boundary

```mermaid
flowchart LR
    Capture["captured source material"] --> Object["resolved object identity"]
    Object --> Claims["identity, place, time, and role claims"]
    Claims --> Evidence["source locators and provenance"]
    Evidence --> Review{"claim-specific review"}
    Review -->|supported| Admit["admit at declared strength"]
    Review -->|limited| Qualify["retain with qualification"]
    Review -->|conflicted| Conflict["preserve competing claims"]
    Review -->|insufficient| Refuse["exclude or defer with reason"]
```

The review is claim-specific. One sample can have a final identity, a directly
supported site, an approximate coordinate, and unresolved numeric chronology.
A single record-level quality flag would hide those independent outcomes.

## What Is Curated

| Curation object | Governing question | Durable result |
| --- | --- | --- |
| source | Which release, archive, paper, supplement, or service supplied the material? | source identity, retrieval context, content identity, and use boundary |
| object identity | Which project, paper, sample, site, sequence, lake, or registry record is this? | stable identity, native key, aliases, and ambiguity state |
| claim | What does the captured material say about taxonomy, locality, chronology, coordinates, or role? | source wording, subject, value, scope, precision, and locator |
| relation | How does one governed object relate to another? | typed sample-to-project, sample-to-site, paper-to-project, or product-to-member link |
| decision | Is the claim usable for the proposed comparison or publication? | admitted, qualified, conflicted, deferred, or refused posture with reason |
| recovery item | What evidence would change an unresolved decision? | named missing artifact, field, relationship, or review action |

These objects live at their natural scope. Project registries govern project
identity; project sample masters govern samples; per-sample evidence packets
govern locality and chronology claims; species views combine reviewed records;
publication manifests govern product membership.

## Fact Ownership

Facts often appear in several convenient exports. Repetition does not transfer
authority. `data/source_fact_ownership_registry.json` names the governing
surface for repeated facts and identifies downstream supporting surfaces.

```mermaid
flowchart TB
    Owner["governing fact owner"] --> Species["species-normalized view"]
    Owner --> Review["cross-project review"]
    Owner --> Candidate["publication candidate"]
    Candidate --> Product["world, regional, or country member"]
    Product -. "audit back to owner" .-> Owner
```

For example, a project-owned `sample_master.json` governs animal sample
identity. A species record, atlas candidate, CSV export, and popup may repeat
the label, but corrections begin in the project authority and propagate
through every descendant.

## Curation Outcomes

| Outcome | Meaning | Public effect |
| --- | --- | --- |
| admitted | required evidence and relations support the product claim | publish with its declared role and precision |
| qualified | the claim is useful but materially limited | publish only when the qualification remains visible |
| contextual | evidence informs interpretation without directly supporting the target object | retain as a separately labelled context layer |
| conflicted | two captured claims disagree and neither may be silently erased | preserve both, select an owner where justified, and expose the conflict |
| deferred | a named recovery action could resolve the decision | keep outside the stronger product until recovery and review complete |
| refused | the proposed claim exceeds the available evidence or product contract | publish the refusal or exclusion reason, not the unsupported claim |

Refusal is preserved evidence about the boundary of the database. It does not
mean that the source object is false or irrelevant; it means that the proposed
use is not currently justified.

## Audit One Curated Claim

Start from either the source or the public member and recover the same chain:

1. identify the governed object and its source-native key;
2. locate the captured artifact, field, table row, or excerpt;
3. identify which surface owns the disputed fact;
4. inspect normalization, precision, null, and conflict posture;
5. inspect the product-specific admission decision and scope;
6. confirm that warnings, exclusions, and recovery items remain reachable.

Continue with [record admission](record-admission.md) for the product gate and
[conflicts and recovery](conflicts-and-recovery.md) for unresolved evidence.
Use [source families](../sources/index.md) for acquisition context,
[evidence dimensions](../evidence/index.md) for claim semantics, and
[publications](../publications/index.md) for manifested outputs.

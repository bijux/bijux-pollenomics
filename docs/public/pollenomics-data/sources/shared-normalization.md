---
title: Shared Normalization
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Shared Normalization

Shared normalization makes records addressable and comparable while
preserving family-specific meaning. It does not force pollen sequences,
archaeology sites, hydrography, boundaries, and ancient-DNA samples into one
scientific schema.

## Common Envelope

A normalized record exposes enough shared structure to answer:

- what object is represented;
- which family and upstream identity supplied it;
- which repository-owned identifier addresses it;
- what geometry and spatial basis it carries;
- what temporal statement and basis it carries;
- which evidence role it may play;
- which captured record and transformation produced it;
- whether it is only normalized, reviewed, qualified, or published.

Family-owned fields remain beside this envelope. A pollen sequence retains
sequence meaning, a registry site retains registry semantics, and a sample
retains sample-level lineage.

## Field Lineage

Every normalized value should be classifiable by how it was obtained:

| Value class | Required lineage | Example |
| --- | --- | --- |
| preserved | source field and source-native value | accession, reported locality, or registry identifier |
| parsed | source text plus parsing rule | numeric interval parsed from a declared date field |
| normalized | source value plus vocabulary or unit mapping | country code, taxon label, or coordinate reference system |
| derived | named inputs plus deterministic method | bounding box, distance, density, or summary count |
| curated | competing evidence plus recorded decision and owner | sample-to-site link or qualified coordinate |
| absent | explicit missing, unresolved, inapplicable, or withheld state | chronology not supplied by the source |

This classification prevents a derived or curated value from appearing
source-native after it has moved downstream. It also makes review proportional:
preserved values need identity proof; parsed and normalized values need
transformation proof; derived values need method and input proof; curated
values need a decision record.

### Field Contract

Each non-trivial normalized field can be reconstructed as a compact contract:

| Contract member | Question it answers |
| --- | --- |
| subject | Which stable source-native object owns the field? |
| source | Which captured artifact and locator supplied the input? |
| native value | What did the source say before repository interpretation? |
| operation | Was the value preserved, parsed, normalized, derived, or curated, and by which rule? |
| result | What value, unit, vocabulary, geometry, or null state was retained? |
| posture | What precision, ambiguity, conflict, or review qualification applies? |

```mermaid
flowchart LR
    Subject["stable subject"] --> Field["normalized field"]
    Source["captured source locator"] --> Native["native value"]
    Native --> Operation["declared operation"]
    Operation --> Field
    Field --> Posture["precision and review posture"]
```

The contract is evaluated per field because identity, locality, chronology,
and coordinates may have different evidence. A record-level success flag would
allow one strong field to conceal another field's unresolved state.

## Lossless By Meaning

Normalization is lossless when every repository value can be interpreted
against the source statement that produced it, including deliberate absence.
It does not require the normalized file to reproduce the upstream file byte for
byte.

For every transformed field, the evidence chain retains:

1. the source member and field locator;
2. the verbatim or source-native value when interpretation matters;
3. the transformation class and named rule;
4. the normalized value, unit, vocabulary, or geometry;
5. the null, ambiguity, precision, or conflict state; and
6. the review or curation owner when the result is not mechanical.

```mermaid
flowchart LR
    Native["source-native value"] --> Rule["declared transformation"]
    Rule --> Normalized["normalized value"]
    Native --> Lineage["field lineage"]
    Rule --> Lineage
    Normalized --> Lineage
    Lineage --> Review["meaning and fitness review"]
```

A normalized value without this chain is structurally convenient but
scientifically brittle: readers cannot distinguish transcription, parsing,
mapping, derivation, or expert judgment.

```mermaid
flowchart TB
    subgraph Native["source-native meaning"]
        Pollen["pollen sequences and grids"]
        Archaeology["archaeology sites and density"]
        Water["lakes and catchments"]
        DNA["projects, samples, and evidence"]
    end
    Native --> Parser["family-specific interpretation"]
    Parser --> Envelope["shared identity, lineage, space, time, and role"]
    Envelope --> Review["comparability and fitness review"]
    Review -->|eligible| Product["scope-aware publication"]
    Review -->|not eligible| Gap["qualified record or explicit gap"]
```

## Family Semantics

| Family | Spatial meaning | Temporal meaning | Evidence role |
| --- | --- | --- | --- |
| LandClim | site-sequence point or REVEALS grid | sequence interval where captured | primary pollen context |
| Neotoma | pollen-site point | site span where present; uneven coverage | primary pollen context |
| SEAD | environmental-archaeology site | not uniformly time-resolved in the capture | contextual domain |
| RAÄ | registry point or density surface | no repository-owned uniform time window | contextual domain |
| SVAR | current lake, catchment, or water body | present-day sampling context | sampling context |
| boundaries | country or regional polygon | no temporal evidence claim | geographic framing |
| AADR | release-owned sample point | sample chronology where supported | direct human aDNA |
| animal aDNA | admitted sample-owned site at recorded precision | sample chronology with source and precision | direct animal aDNA |

## Preserved Distinctions

- reported and normalized values remain separately recoverable;
- exact, approximate, substituted, region-only, and withheld geography remain
  different states;
- numeric interval, textual period, project context, and absent chronology
  remain different states;
- direct evidence, context, sampling support, comparator, and framing remain
  different roles;
- missing and unresolved values are not converted to empty certainty;
- normalization status is not publication status.

## Nulls, Collisions, And Deduplication

Null states remain semantic. `missing`, `unresolved`, `not applicable`, and
`withheld` describe different relationships to the source and cannot be
collapsed into an empty string or zero. A consumer that does not understand a
state must preserve it rather than invent a default.

Identity collisions are reviewed within the family that owns the observation
unit. Matching labels, titles, place names, or rounded coordinates are
candidate signals, not proof of equality. Deduplication must retain the source
members, comparison rule, chosen governing identity, and any unresolved
conflict. Cross-family records are normally related, not deduplicated, because
they observe different objects.

## Join Eligibility

A shared identifier shape does not authorize a scientific join. A join must
declare the relation and compatible dimensions:

| Relation | Minimum support |
| --- | --- |
| same object | governing identity relation, not label similarity alone |
| same place | compatible geometry, basis, and precision |
| same period | compatible normalized chronology and uncertainty |
| contextual proximity | declared distance or containment rule plus evidence roles |
| product membership | named scope and admission decision |

Co-located records with incompatible time support remain spatially comparable
only. Records within one country remain co-members of a geographic scope, not
evidence of association.

A join result inherits the weakest compatible precision of its members. Two
records with point geometry are not an exact spatiotemporal match when one
point is approximate or one chronology is contextual. The normalized envelope
exposes those limits so comparison code and readers can refuse the stronger
relation.

## Audit A Normalization Change

A normalized diff is interpretable only when its cause is classified. Compare
member identities before counts, then route each changed field through its
lineage class:

| Observed change | Evidence to inspect | Legitimate consequence |
| --- | --- | --- |
| source-native value changed | capture version, member identity, and original field | normalized descendants may change under the same rule |
| parser or vocabulary changed | rule identity, affected source values, and before/after mapping | all members using the rule require semantic review |
| derived value changed | named inputs, method, units, and precision | dependent relations and products require recomputation |
| curated decision changed | competing evidence, decision reason, and owner | claim posture or admission may change without changing source text |
| null state changed | prior state, recovered evidence, and new state | only the newly supported claim may strengthen |
| count changed with stable members | grouping, scope, or denominator definition | narrative totals change; member evidence may remain identical |

```mermaid
flowchart LR
    Diff["normalized member diff"] --> Cause{"lineage class"}
    Cause --> SourceChange["source capture change"]
    Cause --> RuleChange["transformation rule change"]
    Cause --> DecisionChange["curation decision change"]
    SourceChange --> Impact["affected descendants"]
    RuleChange --> Impact
    DecisionChange --> Impact
    Impact --> Proof["member-level semantic proof"]
```

The proof is not merely that regenerated files match the new code. It must
show that source-native meaning is still recoverable, units and nulls retain
their semantics, identities did not merge accidentally, and every strengthened
claim has new supporting evidence. A mechanically stable count can still hide
a damaging field reinterpretation; a changed count can be harmless when scope
or grouping changed explicitly.

## Publication Boundary

The normalized collection is intentionally broader than the published subset.
Review evaluates fitness for one claim and product; publication admits only
records that satisfy that contract and preserves qualifications or exclusions
for those that do not.

Continue with the [spatiotemporal posture](spatiotemporal-posture.md) for
comparison limits and [map inputs](../publications/map-inputs.md) for the
publication handoff.

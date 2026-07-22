---
title: Source Families
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Source Families

Pollenomics combines eight contracted source families. Their records can share
a publication, but the source contract preserves what each family measures,
where it applies, how it was acquired, and which claims it can support.

## Contracted Sources

| Family | Evidence role | Suitable questions | Principal limit |
| --- | --- | --- | --- |
| [LandClim](landclim.md) | primary pollen context | pollen sequences and modelled vegetation context | model grids and observed sites have different semantics |
| [Neotoma](neotoma.md) | primary pollen context | palaeoecological site and pollen comparison | temporal coverage and resolution vary by site |
| [SEAD](sead.md) | environmental archaeology context | archaeological and environmental context | access, normalization, and chronology require explicit review |
| [RAÄ](raa.md) | Swedish archaeology context | heritage and archaeological context in Sweden | national coverage cannot be generalized beyond Sweden |
| [Boundaries](boundaries.md) | geographic framing | country selection, clipping, and map extent | boundaries are not scientific evidence |
| [SMHI SVAR](svar.md) | lake and hydrography context | registered Swedish waters and lake-oriented filtering | registry presence does not establish sampling suitability |
| [AADR](aadr.md) | human ancient-DNA evidence | release-versioned sample metadata | current scope excludes genotype processing |
| [Animal source intake](animal-source-intake.md) | sample-owned animal aDNA evidence | project, paper, supplement, sample, locality, and chronology recovery | source completeness varies by project and sample |

## Choose By Question And Observation Unit

The most convenient layer is not necessarily the right evidence. Select a
family by the object it observes and the claim it is allowed to support.

| Intended question | Appropriate starting family | Observation unit | Required qualification |
| --- | --- | --- | --- |
| What pollen or vegetation context is represented? | LandClim or Neotoma | sequence, site, or model grid | state whether the value is observed or modelled and retain its time basis |
| What archaeological context is registered nearby? | SEAD or RAÄ | environmental-archaeology site or Swedish heritage record | preserve national reach, registration bias, and chronology limits |
| Which geography contains a record? | boundaries | administrative polygon | use only for framing or selection, never evidential weight |
| Which registered lake is being considered? | SVAR | water-body registry record | distinguish registry identity from sampling suitability |
| Which human aDNA metadata record is represented? | AADR | release-versioned sample row | retain release and metadata precision; genotype analysis is separate |
| Which animal specimen supports a claim? | animal source library | project-owned sample with paper lineage | require sample-owned place, time, and coordinate evidence for exact publication |

If no family observes the required unit, combining nearby layers does not
repair the gap. The valid outcome is a contextual statement, a recovery item,
or a refusal.

## Source Identity

Every collected family is bound to repository evidence that includes:

- a source key and display name;
- selected version and retrieval date;
- acquisition method and output root;
- source-specific license posture;
- hashes for captured and normalized content;
- provenance linking the source to its repository representation; and
- replacement rules describing how refreshes affect tracked data.

The current bindings are recorded in `data/collection_summary.json`. A hash
identifies bytes; it does not certify scientific completeness, temporal
comparability, or publication fitness.

### Minimum Capture Packet

A captured member is usable evidence only when the repository can recover the
object and the context in which it was acquired:

| Packet field | Required meaning |
| --- | --- |
| source identity | family, upstream owner, dataset or archive name, and release or accession |
| member identity | source-native key and repository key without relying on row order |
| acquisition | canonical locator, retrieval method, retrieval time, and access outcome |
| content identity | physical or logical artifact path, media type, size, and digest |
| reuse posture | licence or terms evidence and any redistribution limit |
| intended role | observation unit, geographic and temporal reach, and permitted evidence role |
| preparation lineage | parser or extraction rule, normalized destination, and unresolved fields |

```mermaid
flowchart LR
    Upstream["upstream object"] --> Capture["capture packet"]
    Capture --> Bytes["content identity"]
    Capture --> Member["source-native member identity"]
    Capture --> Role["declared evidence role"]
    Member --> Prepared["normalized record"]
    Bytes --> Prepared
    Role --> Prepared
```

A DOI without the recovered table, an API URL without a release or response
identity, or a copied row without its source-native key is an incomplete
capture packet. Such material can remain in recovery state, but cannot silently
enter the normalized population.

## Source Contract As Scientific Interface

A family contract defines the stable boundary between an upstream ecosystem
and every repository consumer. It is more than an acquisition recipe.

| Contract dimension | Evidence retained | Promise to consumers |
| --- | --- | --- |
| identity | owner, dataset or archive identity, release, and source locator | records can be attributed to the intended upstream object |
| observation unit | site, sequence, sample, registry record, polygon, or project relation | counts and joins preserve what was actually observed |
| semantics | source-native fields, units, nulls, geometry, and time meaning | normalization does not silently strengthen the source |
| acquisition | retrieval method, date, license posture, payload identity, and replacement rule | a capture can be reproduced or challenged |
| role | direct evidence, primary context, contextual domain, sampling context, or framing | publication cannot promote context into direct proof |
| fitness | coverage, precision, conflict, and product-specific review | consumers can distinguish captured data from admitted evidence |

A source-name match is not enough to preserve this interface. A release that
changes observation unit, schema meaning, licensing, geographic reach, or time
semantics requires renewed interpretation before old publication assumptions
can be reused.

## Source Admission

```mermaid
flowchart LR
    Candidate["candidate source"] --> Identity{"stable identity and owner?"}
    Identity -->|no| Defer["defer with reason"]
    Identity -->|yes| Access{"recoverable and permitted?"}
    Access -->|no| Defer
    Access -->|yes| Semantics{"observation unit and role understood?"}
    Semantics -->|no| Review["retain for source review"]
    Semantics -->|yes| Contract["admit source-family contract"]
    Contract --> Capture["versioned capture and normalization"]
```

Admission requires more than topical relevance. The system needs a stable
source identity, an acquisition route, a reuse posture, a defined observation
unit, a geographic and temporal interpretation, and an explicit role in the
publication model. A source that fails one requirement may remain documented
for recovery without being presented as a collected evidence family.

Refresh does not repeat admission blindly. A new release can change schema,
licence terms, endpoints, coverage, or semantics; those changes require review
even when the source name remains stable.

### Admission Has Three Separate Decisions

Source-family admission, record capture, and product admission answer different
questions. Conflating them makes a large collection look more publishable than
its evidence warrants.

| Decision | Question | Durable outcome |
| --- | --- | --- |
| family contract | Is the upstream object identifiable, recoverable, interpretable, and legally usable for a declared role? | admitted family or documented deferral |
| record capture | Which source-native members were actually retrieved and normalized? | captured member, rejected row, or unresolved member with reason |
| product admission | Does this reviewed member satisfy one named product's identity, spatial, temporal, and role requirements? | admitted, qualified, excluded, or deferred membership |

A family may be fully contracted while some records remain unresolved. A
record may be captured correctly yet excluded from every public product. A
member admitted to a spatial inventory may remain ineligible for time-aware
analysis. Each state is meaningful and remains queryable.

### Source Substitution Is Forbidden

A source may fill only the claim dimension it owns. Boundaries can decide
spatial membership but cannot validate a sample coordinate. SEAD can supply
environmental archaeology context but cannot date a nearby specimen. SVAR can
identify a registered water body but cannot establish coring feasibility. AADR
cannot resolve animal sample identity, and animal project metadata cannot stand
in for sample-owned locality evidence.

Cross-domain products therefore join governed claims; they do not merge source
authority. When one required dimension is absent, the product must qualify,
defer, or refuse the claim instead of borrowing certainty from another family.

## Change Propagation

```mermaid
flowchart LR
    Release["new release or recovered artifact"] --> Capture["capture identity and diff"]
    Capture --> Normalize["member and semantic diff"]
    Normalize --> Review["coverage, conflict, and precision review"]
    Review --> Decision["admission impact"]
    Decision --> Product["affected product membership"]
    Decision --> None["no public change, with reason"]
```

The last branch is important: collection and curation are products even when a
record remains outside public scope. A refresh is trustworthy when its lack of
publication impact is explained, not merely when regenerated maps happen to
look unchanged.

## Direct Evidence, Context, And Framing

```mermaid
flowchart TB
    Direct["direct evidence\nAADR and sample-owned animal aDNA"]
    Primary["primary pollen context\nLandClim and Neotoma"]
    Context["contextual domains\nSEAD and RAÄ"]
    Sampling["sampling context\nSVAR"]
    Framing["geographic framing\nboundaries"]
    Publication["cross-domain publication"]
    Direct --> Publication
    Primary --> Publication
    Context --> Publication
    Sampling --> Publication
    Framing --> Publication
```

Co-publication does not make these roles equivalent. For example, a boundary
can determine whether a point appears in a country view, but it cannot validate
the point's date or coordinate. A lake record can support candidate discovery,
but not a coring recommendation without further evidence.

## Animal Source Recovery

Animal aDNA is not acquired as one uniform release. The source library links
papers, archive projects, supplements, sample identifiers, sites, locality
statements, and chronology claims while retaining their separate provenance.

A project can remain tracked even when it is not publishable. Missing
supplements, ambiguous identifiers, unresolved localities, and conflicting
dates enter recovery queues and review ledgers. This preserves the difference
between “no evidence exists” and “the necessary evidence has not yet been
recovered.”

## Infrastructure Is Not Evidence

[PalaeOpen](palaeopen.md) and similar collaboration or interoperability
networks can help align metadata and reuse practices. They are not direct
source families unless a specific governed dataset is acquired, versioned,
licensed, and admitted through the source contract.

## Compare And Inspect

- [Source comparison](source-comparison.md) compares the questions each family
  can answer.
- [Source-family matrix](source-family-matrix.md) compares role, reach,
  publication use, and limits.
- [Refresh policy](refresh-policy.md) describes source replacement and review.
- [Shared normalization](shared-normalization.md) describes common fields
  without erasing source-specific semantics.
- [Spatiotemporal posture](spatiotemporal-posture.md) compares place and time
  meaning across domains.
- [Evidence](../evidence/index.md) follows curated claims beyond acquisition.

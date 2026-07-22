---
title: Coordinates
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Coordinate provenance

A coordinate is a spatial interpretation of locality evidence. It may be
reported directly with a sample, resolved from an explicit named site, or
withheld because the source supports only a region. Bijux Pollenomics records
which of those paths produced—or refused—a point.

This matters because every marker is visually exact. Without provenance, a
regional study extent and a source-published excavation coordinate would look
equally precise on a map.

## Current evidence posture

The cross-species map-readiness review currently reports 234 direct
coordinate-backed entries, two indirectly geocoded entries, 21 unresolved
entries, and seven entries refused from mapping. These are readiness units in
the governed species/site review, not a count of all recovered samples: many
samples can share a reviewed locality, and samples without defensible linkage
must not inherit it.

The asymmetry across species is material. Horse accounts for 207 of the direct
entries, goat for 27, while several other species currently have no direct
coordinate-backed entry. The public collection should expose that unevenness
rather than let the strongest species imply equal spatial resolution for all
animal evidence.

## From locality to mapping posture

```mermaid
flowchart TD
    A[Reviewed sample locality] --> B{Source supplies coordinates?}
    B -->|yes| C[Preserve source pair and locator]
    B -->|no| D{One explicit named site?}
    D -->|yes| E[Named-site resolution with method]
    D -->|no| F{Region, transect, or multiple sites?}
    F -->|yes| G[Refuse point mapping]
    F -->|no| H[Keep geography unresolved]
    C --> I[Coordinate provenance record]
    E --> I
    I --> J{Basis and linkage complete?}
    J -->|yes| K[mappable_point]
    J -->|no| H
    G --> L[Non-point context]
    H --> L
```

A region centroid is not a compromise point. It is a different geographic
claim and remains refused from point publication. Likewise, a source that names
multiple caves or a transregional dispersal route cannot be represented by one
marker until sample-to-site evidence separates the component locations.

Point eligibility is conjunctive: identity, locality linkage, coordinate
basis, mapping posture, and product-specific rules must all pass. Confidence
cannot compensate for a missing link earlier in the chain.

## Confidence is not just decimal precision

| Confidence | Coordinate basis | Public interpretation |
| --- | --- | --- |
| `exact` | direct published coordinates or an explicit archive pair | source-backed point at the reported resolution |
| `approximate` | one explicit named place resolved through a documented method | cautious named-site point; not a source-supplied pair |
| `inferred` | indirect derivation | retained for non-public context, not point publication |
| `withheld` | region-only, aggregate, or unresolved geography | no public point |
| `unknown` | basis has not been normalized | no claim of coordinate precision |

`exact` describes provenance, not archaeological certainty to an arbitrary
number of decimal places. `approximate` is allowed only when the named place is
explicit and the resolution method remains visible. A mapping posture of
`mappable_point` is still required for either confidence class to publish.

The display should preserve that distinction. An approximate named-site
resolution needs a visibly different interpretation from a source-published
pair even if both use the same marker geometry. Decimal formatting must not
suggest more precision than the source or resolution method supports.

## The coordinate record

Each animal coordinate-provenance row preserves:

- project accession, species, and site label;
- original and resolved place text;
- source artifact path and locator;
- coordinate basis and mapping posture;
- latitude and longitude as source-preserving text;
- resolution method and gazetteer or curated anchor;
- confidence class and rationale;
- paper or supplement linkage;
- associated chronology and interpretation notes;
- an explicit support-gap note when point publication is refused.

For samples whose own supplementary rows contain coordinates, the sample
lineage supplies the coordinate basis directly. For broader project leads,
coordinate provenance remains a separate reviewed record so a project-level
anchor cannot silently become sample-level geography.

## Coordinate Reuse Contract

A downstream export that retains latitude and longitude but drops their basis
has converted reviewed evidence into unexplained geometry. Reuse should retain:

| Required field | Question it preserves |
| --- | --- |
| governing sample or site ID | Which observation owns this point? |
| original and resolved place text | What place was reported and what was interpreted? |
| source artifact and locator | Where is the supporting statement or pair? |
| coordinate basis and method | Was the point supplied, curated, or resolved? |
| confidence and mapping posture | May it appear as a point, and with what qualification? |
| spatial precision or caveat | How narrowly may distance or containment be interpreted? |
| product and admission decision | Why is the point visible in this scope? |

Coordinate reference conversion and decimal formatting may change
representation, but they must not change basis, confidence, or supported
precision. A transformed pair remains the same governed spatial claim only
when its lineage to the original pair is retained.

## Why points are withheld

Common refusal conditions include:

- only a country, basin, region, or cultural area is supported;
- one recovered row still aggregates multiple named sites;
- the paper describes a transect or dispersal extent rather than a sample site;
- a site name is present but the sample-to-site linkage is unresolved;
- an apparent coordinate lacks its source locator or resolution rationale.

Withholding does not delete the evidence. The region or named places remain in
the curation and review surfaces, where they can support broader context and
identify the missing source work needed for a future point.

### Spatial representations by support

| Supported claim | Defensible representation |
| --- | --- |
| source-backed sample or site coordinate | point, with basis and confidence available |
| one explicit place resolved approximately | qualified point when product rules allow it |
| region, basin, country, or transect | polygon, aggregate, label, or non-point context |
| multiple unresolved candidate sites | review surface, never one synthesized point |
| no defensible geography | explicit exclusion or unresolved count |

## Read A Distance Carefully

Distance is derived from geometry, so its usefulness is bounded by both
endpoints. An exact lake centroid and an approximate named-site point produce
an approximate distance relation. A region-only sample has no defensible point
distance even if a centroid is technically available. Ranking and proximity
views should carry endpoint identity, basis, precision, distance method, and
the threshold or band used.

## Auditing a mapped sample

The species-owned record is
`data/adna/species/<species-slug>/normalized/coordinate_provenance.json`.
Compare its sample and locality linkage with `sample_sites.json`, then inspect
the cross-species review surfaces:

- `data/adna/governance/coordinate_caveat_surface.json` groups direct,
  place-resolved, and still-weak geography;
- `data/adna/governance/cross_species_map_readiness.json` reports publication
  readiness across animal species;
- `data/adna/governance/unresolved_site_ledger.json` and
  `overbroad_site_ledger.json` expose geography that cannot support a point.

Read [locality evidence](localities.md) when the underlying place claim is in
question, and [point publication rules](../publications/point-rules.md) for the
full admission boundary.

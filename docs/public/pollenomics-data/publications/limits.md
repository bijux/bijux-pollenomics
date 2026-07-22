---
title: Publication Limits
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Publication Limits

The checked-in publications are credible, inspectable evidence surfaces, but
they do not support every possible pollenomics claim. Limits are separated by
cause so missing source material, weak comparability, conservative admission,
and absent runtime capability are not mistaken for one generic disclaimer.

## Current Release Posture

The repository's generated release assessment refuses final-release language.
Its current blocking dimensions are:

- **animal data recovery**: sample extraction is not yet sufficiently complete
  and region-agnostic for the strongest coverage claims;
- **SEAD treatment**: access and temporal comparability remain weaker than the
  mature context surfaces; and
- **geographic extensibility**: the publication lineage and onboarding contract
  exist, but broader geographic proof is not yet established.

The animal publication gate passes its current anti-overclaim checks while
still prohibiting language that implies unrestricted precision. These two
results are compatible: a conservative subset can be safely published before
the underlying recovery program is complete.

## Quantified Boundaries

The current governed state makes several limits measurable:

| Surface | Current signal | Consequence |
| --- | --- | --- |
| Animal sample recovery | 868 recovered rows across 40 projects; only four projects have a trustworthy expected count | recovered rows are auditable, but collection completeness is usually unknown |
| Animal locality | 820 direct sample-site assignments; 32 region-only; 16 unresolved | 48 samples cannot be described as exact sample sites |
| Animal publication points | 234 accepted point-evidence rows; 233 direct supplementary coordinates and one approximate named-site geocode | the point subset is traceable but spatial support is uneven |
| Neotoma time | 175 of 200 sites have numeric BP spans; chronology rows are not captured | site-span comparison requires the Neotoma temporal caveat |
| SEAD time | 2,172 normalized sites and no numeric intervals in the current capture | use as archaeology context, not same-period support |
| RAÄ scope | Sweden-specific density source | do not generalize its coverage to the Nordic region |

These numbers are a snapshot of the governed artifacts, not permanent project
constants. The applicable manifests and review surfaces remain authoritative
when the data state changes.

## Limits By Dimension

| Dimension | Supported use | Unsupported inference |
| --- | --- | --- |
| Coverage | inspect tracked and admitted records | assume absence means no relevant evidence exists |
| Locality | distinguish exact, qualified, broad, and blocked place claims | treat a project or region label as a sample site |
| Chronology | compare records carrying compatible temporal semantics | convert broad or contextual dates into precise numeric overlap |
| Coordinates | inspect direct or explicitly derived mapping posture | read marker precision as source precision |
| Cross-domain maps | explore co-located evidence families | infer causal, biological, or temporal association from proximity |
| Lake ranking | prioritize candidates under declared scoring and sensitivity | replace bathymetry, access, permitting, coring design, or field verification |
| AADR | use versioned public metadata | infer genotype processing or population-genetic analysis |
| Country views | inspect filtered descendants of the shared atlas state | treat a country bundle as an independent complete database |

## Visible Absence

```mermaid
flowchart LR
    Missing["not visible in publication"] --> Cause{"why?"}
    Cause --> NotCaptured["source not captured"]
    Cause --> Deferred["recovery or curation deferred"]
    Cause --> Blocked["known evidence failure"]
    Cause --> Outside["outside selected scope"]
    Cause --> Unsupported["publication type does not support it"]
```

These causes have different meanings. The exclusion and recovery surfaces are
necessary companions to the visible atlas because a clean map alone cannot
distinguish them.

Absence is therefore not one claim. “Not captured,” “captured but unresolved,”
“reviewed and refused,” “outside geographic scope,” and “unsupported by this
publication type” require different language and different next evidence. A
responsible downstream analysis should retain the reason rather than replace
all five with a single missing-value code.

## Map Boundaries

- Basemap tiles may still depend on external providers even though publication
  assets and Leaflet code are bundled locally.
- RAÄ is a Sweden-specific context source.
- Country and regional filters do not repair weak source geography.
- Popups summarize governed fields; they are not complete provenance records.
- Candidate rankings are sensitive to available layers, scoring assumptions,
  geographic scope, and missing evidence.

## Responsible Use

Before relying on a publication:

1. identify the bundle version and geographic scope;
2. determine the source family and its evidence role;
3. inspect point traceability and scientific review for consequential claims;
4. preserve precision and temporal posture when quoting or transforming data;
5. check exclusions and recovery gaps before interpreting absence; and
6. avoid language stronger than the current release posture.

For lake prioritization, treat the ranking as a reproducible screening model,
not a fieldwork decision. A high score identifies a candidate supported by the
available and weighted layers. It does not establish sediment preservation,
basin geometry, access, legal permission, sampling feasibility, or the absence
of uncaptured evidence around lower-ranked lakes.

For cross-domain interpretation, report proximity and temporal compatibility
as separate findings. Co-location is not contemporaneity; contemporaneity is
not causation; contextual archaeology or pollen is not direct evidence about a
particular human or animal sample.

The generated
[`repository_final_release_refusal`](../../../report/repository_final_release_refusal.md)
and [`repository_credibility_dashboard`](../../../report/repository_credibility_dashboard.md)
record the current machine-derived assessment. They should be read with the
specific evidence review relevant to the claim, not as substitutes for it.

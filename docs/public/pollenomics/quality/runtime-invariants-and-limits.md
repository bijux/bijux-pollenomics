---
title: Runtime Invariants and Limits
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Runtime Invariants and Limits

The runtime preserves a small set of observable guarantees across collection,
curation, analysis, and publication. These guarantees make a public record
traceable even when its source family is incomplete or its scientific posture
remains qualified.

## Observable Guarantees

| Guarantee | Observable consequence |
| --- | --- |
| source ownership | every record retains a source-family tree and identity |
| lineage preservation | normalized and published records lead back to governed evidence |
| explicit admission | publication follows review; file presence alone is insufficient |
| semantic stability | narrower geographies preserve feature identity and role |
| precision honesty | locality, chronology, and coordinates do not become more exact downstream |
| accountable absence | blocked and excluded records remain visible in review or refusal surfaces |
| reproducible scope | manifests bind products to inputs, version, geography, and product rules |

```mermaid
flowchart LR
    Source["source identity"] --> Record["stable record identity"]
    Record --> Review["reviewed place, time, and role"]
    Review --> Decision{"admission"}
    Decision -->|yes| Product["manifested public record"]
    Decision -->|no| Refusal["accounted exclusion"]
```

## Where Each Guarantee Is Visible

| Boundary | Evidence of conformance | Evidence of refusal or limit |
| --- | --- | --- |
| collection | source identity, retrieval context, hashes, and family summary | failed capture, missing expected asset, or retained prior family tree |
| normalization | source-linked stable record and declared field semantics | unresolved, conflicting, approximate, or unsupported value |
| curation | governing decision with fact owner and reason | open recovery item, qualification, or explicit non-linkage |
| analysis | named inputs, method, scenario, and sensitivity result | unstable rank, unsupported comparison, or withheld conclusion |
| publication | scope, manifest, member identities, traceability, and warnings | exclusion, empty admitted set, or preserved previous bundle |

The negative column is part of the system contract. A guarantee is credible
only when failure remains observable instead of being converted to a default,
an inferred value, or an unexplained omission.

## Runtime Boundaries

Collection can establish that material was retrieved and normalized. It cannot
establish that every source row was recovered or is scientifically comparable.
Validation can establish structural and relational invariants. It cannot prove
that a historical interpretation is correct. Publication can establish that a
record passed a product contract. It cannot make the underlying evidence more
complete or precise.

Structural validation and scientific review answer different questions.
Schema, type, and referential checks can show that a record is internally
coherent. They cannot show that an unavailable supplement was fully recovered,
that historical sampling was representative, or that two evidence families
measure the same phenomenon.

## Current Scientific Limits

- Animal ancient-DNA recovery remains uneven across projects, supplements,
  species, localities, and chronology.
- Atlas membership is a qualified publication decision, not a census of all
  available or historically present evidence.
- Source families have different observation units and temporal capability;
  spatial co-location does not make them equivalent.
- A broad geographic product may contain more records while providing less
  local specificity than a country surface.
- Rankings depend on declared inputs and models; they are decision support, not
  field confirmation.
- Source access, licensing, and unrecovered supporting material can limit what
  is redistributed or admitted.

## Operational Limits

- Collection depends on upstream availability and may require network access;
  the prior governed family remains the reference when a refresh fails.
- The checked-in OpenAPI v1 files define a compatibility target, not an
  operated public service.
- Local documentation builds and previews under `artifacts/` are not governed
  publications.
- The compatibility package delegates to the canonical runtime; it does not
  offer an independently versioned scientific implementation.
- A successful command establishes completion of its declared operation, not
  correctness for an undeclared downstream use.

## Interpreting A Passing Product

A passing product demonstrates that its declared inputs, identities,
relationships, geography, and publication rules were internally consistent at
the recorded version. Stronger claims—complete recovery, representative
sampling, exact historical abundance, coordinates suitable for unrestricted
reuse, or final scientific consensus—require evidence beyond that software
contract.

The strongest defensible statement is bounded by the weakest link in the
chain. A fully validated bundle containing a region-level locality still
supports only region-level spatial interpretation; perfect rendering cannot
upgrade that precision.

See [operational boundaries](../operations/operational-boundaries.md),
[publication types](../../pollenomics-data/publications/publication-types.md),
and [publication limits](../../pollenomics-data/publications/limits.md).

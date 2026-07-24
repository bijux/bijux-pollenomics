---
title: Chronology
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Chronology Evidence

Chronology records what the source says about a sample's age, how that wording
was interpreted, and how precisely it may be compared with other evidence. A
numeric value is not automatically a precise sample date: it may describe a
project context, a modeled estimate, or a broad interval.

Bijux Pollenomics therefore keeps three questions separate:

1. **What was reported?** The original chronology text and its source locator.
2. **What can be normalized?** A BP point or interval only when the wording and
   dating basis support one.
3. **What comparison is safe?** A precision posture derived from ownership,
   evidence class, and normalization status.

## Current Evidence Posture

The governed chronology audit covers all 868 recovered animal samples:

| Normalization result | Samples | Interpretation |
| --- | ---: | --- |
| numeric point | 469 | one defensible BP value is available |
| numeric interval | 296 | comparison must preserve interval width |
| text only | 87 | wording is useful but is not safely parsed into BP bounds |
| unresolved | 16 | no trustworthy chronology claim has been recovered |

Evidence class and comparison precision cut across those normalization counts.
The collection includes 729 direct radiocarbon-date rows, 30 archaeological
context dates, 93 historical or recent dates, and 16 unresolved rows. Its
precision postures include 461 sample-precise points, 254 sample-precise
intervals, 87 approximate or modeled sample claims, 50 contextual intervals,
and 16 unresolved claims. Ten projects currently require manual chronology
review.

These views are deliberately different. A row may contain numbers and still be
contextual or approximate; numeric normalization does not confer sample-level
precision.

## A Chronology Claim Is Not The Sample's Age

The database records supported statements about time. It does not collapse
them into one timeless `age` field. A chronology claim binds the sample or
contextual object, reported expression, source locator, dating basis, evidence
class, normalized representation, precision, and review posture.

| Source statement | Governed interpretation |
| --- | --- |
| direct sample result | sample-owned claim, subject to its reported basis and precision |
| modeled estimate | sample claim with model dependence retained |
| archaeological layer or context | contextual claim unless evidence assigns it to the sample |
| project-wide range | project context, not a date copied to every member |
| historical label | source-backed temporal description; numeric use depends on the comparison contract |
| conflicting values | separately addressable claims plus a governing decision for each use |

This model allows later calibration, source recovery, or conflict resolution
to revise the chronology descendants without rewriting sample identity or
pretending the previous evidence never existed.

## Sample Evidence Outranks Project Context

```mermaid
flowchart TD
    A[Recovered sample] --> B{Sample-owned chronology text?}
    B -->|yes| C[Normalize sample claim]
    B -->|no| D{Project or site chronology?}
    D -->|yes| E[Normalize as contextual claim]
    D -->|no| F[Unresolved chronology]
    C --> G{Disagrees with project context?}
    G -->|yes| H[Keep sample claim and record conflict]
    G -->|no| I[Classify evidence and precision]
    H --> I
    E --> I
    I --> J{Numeric comparison justified?}
    J -->|precise| K[Point or interval comparison]
    J -->|approximate| L[Caveated numeric comparison]
    J -->|context only| M[Contextual temporal layer]
    J -->|no| N[Textual context or exclusion]
```

When a sample-owned date conflicts with a project-level range, the sample claim
remains attached to that sample and the disagreement is explicit. Falling back
to project context is allowed only when the sample row lacks its own
chronology, and the result stays classified as contextual rather than
sample-precise.

## Evidence Class And Precision

| Precision posture | Typical support | Comparison rule |
| --- | --- | --- |
| `sample_precise_point` | sample-owned numeric point | compare numerically without implying narrower source precision |
| `sample_precise_interval` | sample-owned numeric interval | compare by interval overlap or distance |
| `sample_approximate_or_modeled` | circa wording, model output, or parsed approximate date | numeric comparison requires a visible caveat |
| `contextual_interval` | site- or project-level numeric context | context only; not a sample-owned date |
| `broad_period_only` | textual archaeological or historical period | label-based orientation, not numeric interval comparison |
| `unresolved` | no recovered or trustworthy date claim | no temporal comparison |

The corresponding evidence classes distinguish direct radiocarbon dates,
modeled sample dates, archaeological context dates, broad period labels, and
historical or recent dates. Evidence class describes *what kind of support
exists*; precision posture describes *how that support may be used*.

### Ownership, Dating Basis, And Representation Are Independent

Three axes are required to interpret a numeric chronology. Collapsing them
into a single “dated” flag makes a sample-owned historical year look
equivalent to a calibrated laboratory distribution.

| Axis | Example states | Question answered |
| --- | --- | --- |
| claim ownership | sample, sample group, site context, project context | which governed object does the statement describe? |
| dating basis | direct radiocarbon, modeled estimate, archaeological context, historical record | how was time established? |
| representation | source text, BP point, interval, disjoint ranges, probability distribution | how is the supported time encoded? |

Numeric representation does not upgrade ownership or dating basis. A
project-owned interval remains project context after conversion to BP, and a
sample-owned number remains qualified when its basis is modeled or otherwise
approximate. Comparison rules select compatible states on all three axes.

## The Normalized Chronology Contract

A chronology row preserves:

- stable sample identity and preferred source label;
- original chronology text;
- chronology strength and evidence class;
- precision posture and normalization status;
- provenance artifact, artifact kind, locator, and supporting excerpt;
- `time_start_bp`, `time_end_bp`, and `time_mean_bp` when defensible;
- dating basis, conflict note, and review note.

Normalization status remains `text_only_unparsed` when useful wording cannot
be converted safely, and `unresolved` when no chronology has been recovered.
For numeric values, equal BP bounds represent a point; unequal bounds represent
an interval. Original text remains the authoritative source expression.

`time_mean_bp` is a summary coordinate, not a replacement for the interval.
Range overlap and distance calculations use the bounds when they exist. A map
or chart that displays a mean must retain access to the original bounds,
precision posture, evidence class, and comparison note so that an interval
does not acquire false point precision.

### Several Claims May Belong To One Sample

A sample can retain a direct laboratory result, a modeled estimate, an
archaeological context range, a historical label, and a disputed source
statement at the same time. The chronology database stores these as separate
claim objects and records which one governs a particular comparison.

```mermaid
flowchart LR
    Sample["stable sample"] --> Direct["direct chronology claim"]
    Sample --> Modeled["modeled chronology claim"]
    Sample --> Context["contextual chronology claim"]
    Direct --> Decision["claim-specific chronology decision"]
    Modeled --> Decision
    Context --> Decision
    Decision --> Comparison["admitted comparison posture"]
```

Selecting a governing claim does not erase the alternatives. The decision
retains evidence class, source locator, relation to the sample, conflict
reason, and supersession history. Averaging incompatible claims would create a
new unsupported chronology and is therefore refused.

### Calendar Conversion Contract

Numeric BP values use 1950 CE as the reference year. For chronology text that
matches the supported BCE or CE forms, the current normalization applies:

| Source expression | Numeric conversion |
| --- | --- |
| year BCE | `year + 1949` BP, accounting for the absence of year zero |
| year CE | `max(0, 1950 - year)` BP |
| BCE or CE range | convert both endpoints, then order the BP interval from younger to older |
| explicit BP point or range | retain the BP value or ordered bounds |

For example, `11367-11220 BCE` becomes `13169-13316 BP`: 11220 BCE is the
younger bound and 11367 BCE is the older bound. The source wording remains
stored beside the normalized interval.

Calendar conversion is not radiocarbon calibration. It does not infer a
laboratory uncertainty, choose a calibration curve, reinterpret an
archaeological period, or prove that a source label is sample-owned. Words such
as *calibrated*, *modeled*, *circa*, and *contextual* remain part of the dating
basis and precision posture after numbers are available.

When a calibrated distribution is available, reducing it to one interval or
midpoint is itself a declared transformation. The chosen probability mass,
possible disjoint ranges, calibration curve, and source method must remain
recoverable; otherwise a convenient display range cannot support independent
chronological analysis.

## Interval Comparison Without False Precision

Normalized BP intervals are ordered from the younger, lower BP bound to the
older, higher BP bound. Comparisons use the interval, not only its mean:

| Relationship | Meaning | Safe conclusion |
| --- | --- | --- |
| intervals overlap | at least part of both supported temporal ranges is shared | temporally compatible at the declared precision |
| intervals do not overlap | the declared numeric ranges are separated | non-overlap for those claims, not proof of historical absence |
| one claim is a point inside an interval | the point falls within the other supported range | compatibility without upgrading the interval to a point |
| one claim is contextual | numbers describe a site or project rather than the sample | context only, even when ranges overlap |
| either claim is text-only or unresolved | no defensible numeric relation is available | incomparable, not non-overlapping |

Interval width is evidence, not noise to discard. Two records with the same
mean but very different widths do not have the same temporal precision, and a
ranking that uses means must retain the bounds and disclose that simplification.

## Worked Chronology Trace

The same sample used in the identity and locality guides,
`prjeb22390:cgg_1_017139`, preserves `1979 BP` from the captured supplementary
rows. Its governed chronology currently records:

| Field | Value |
| --- | --- |
| ownership | sample-owned |
| evidence class | `direct_radiocarbon_date` |
| normalization | `normalized_point` |
| precision posture | `sample_precise_point` |
| BP bounds | `1979` to `1979` |
| dating basis | `mixed_radiocarbon_and_archaeological_context` |
| conflict posture | sample claim disagrees with the project-level interval |

The equal normalized bounds mean that the captured claim contributes one BP
value to the current comparison contract. They do not prove zero laboratory,
calibration, or archaeological uncertainty. The original wording, supporting
row, dating basis, and conflict note remain necessary to interpret the value.

The project disagreement is retained rather than averaged away. Sample-owned
evidence governs this sample; project context remains visible as a conflicting
broader claim. If later source recovery provides an interval or calibration
detail, the chronology descendant can change while the stable sample identity
and Haunstetten locality remain intact.

## Chronology Revision Impact

A chronology correction can change several descendants without changing the
sample identity:

```mermaid
flowchart LR
    Source["new or corrected source claim"] --> Reported["reported chronology text"]
    Reported --> Normalize["bounds, basis, and precision"]
    Normalize --> Compare["comparability posture"]
    Compare --> Window["navigation window"]
    Compare --> Overlap["interval overlap and distance"]
    Overlap --> Ranking["time-aware ranking evidence"]
    Compare --> Admission["product qualification"]
```

Review the semantic cause before aggregate effects. A changed midpoint can
move a record between navigation windows while leaving its source interval
unchanged; a corrected interval can change overlap without changing the
window; a reclassified contextual claim can remove a row from numeric scoring
even when its numbers remain present.

Chronology diffs should therefore compare reported text, source locator,
dating basis, bounds, evidence class, precision, and comparability—not only the
final display label or mean.

### Conversion And Comparison Are Separate Decisions

Normalizing an expression into bounds answers how one source claim is
represented. Admitting two claims to a comparison answers whether their
bases, precision, evidence classes, and intended operation are compatible.
Neither decision implies the other.

| State | Allowed conclusion |
| --- | --- |
| source text only | quote and classify the expression; do not invent bounds |
| normalized bounds, comparison not reviewed | display the interval with its basis; do not score overlap |
| comparison admitted | apply only the declared overlap, distance, or window rule |
| comparison refused | retain both chronology claims and the refusal reason |

A change to calibration or conversion logic must re-evaluate comparison
decisions even when the source wording is unchanged. A change to a comparison
threshold need not rewrite the owned chronology claim.

## What Is Never Inferred

The chronology pipeline does not assign conventional numeric bounds to a named
period merely to make it sortable. It does not treat a project's overall age
range as the precise age of every sample. It does not erase qualifiers such as
*circa*, modeled, calibrated, historical, or recent.

Those restraints matter in a cross-domain atlas. Two layers can overlap in
space while lacking comparable time support. A pollen sequence with a numeric
BP interval, a SEAD site-inventory point, and an animal sample with a modeled
date must retain their different temporal semantics.

Cross-source comparison is therefore an admission decision, not a generic
date join. Exact and interval-supported rows may participate in numeric window
tests; approximate rows require a visible caveat; contextual intervals remain
context; and text-only or unresolved rows cannot silently inherit a numeric
window from a neighboring record.

Chronology absence is also claim-specific. `text_only` means a source statement
was recovered but cannot be safely converted; `unresolved` means no trustworthy
claim is available. Neither is numeric non-overlap, and neither should be
counted as evidence that two records belong to different periods.

The same distinction applies to downstream counts. A “dated records” total
must say whether it includes contextual intervals, approximate or modeled
claims, text-only period labels, and historical or recent dates. Otherwise
records with materially different comparison rights appear to form one
uniform temporal population.

## Auditing Chronology Lineage

Chronology evidence remains project-owned under
`data/adna/governance/source_library/projects/<project-accession>/`, including
`sample_chronology.json`, `sample_chronology_evidence.json`, and
`sample_chronology_provenance.json`. Cross-project audits expose coverage,
precision, conflicts, and unrecovered dates:

- `data/adna/governance/source_library/project_sample_chronology_review.json`;
- `data/adna/governance/source_library/sample_chronology_precision_audit.json`;
- `data/adna/governance/source_library/sample_chronology_conflict_ledger.json`;
- `data/adna/governance/source_library/date_evidence_gap_queue.json`.

Continue to [temporal semantics](temporal-semantics.md) for cross-source
comparability and to [point publication rules](../publications/point-rules.md)
for the effect of chronology on map admission. The
[revision and state model](../database/revision-and-state-model.md) defines how
corrected claims and dependent products remain coherent at one revision.

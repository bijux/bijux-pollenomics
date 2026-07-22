---
title: Animal Ancient DNA Evidence
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-07-22
---

# Animal Ancient DNA Evidence

Animal ancient-DNA publication begins with a source-backed sample, not a
project title or species mention. Papers, archive projects, supplements,
sample tables, sites, chronology statements, and coordinates remain distinct
evidence units until their relationships are explicitly curated.

## Evidence Chain

```mermaid
flowchart LR
    Paper["paper DOI"] --> Project["archive project"]
    Supplement["captured supplement"] --> Project
    Project --> Sample["stable sample identity"]
    Sample --> Locality["sample locality evidence"]
    Sample --> Chronology["sample chronology evidence"]
    Locality --> Coordinate["coordinate basis and precision"]
    Sample --> Species["species-normalized view"]
    Chronology --> Decision{"product admission"}
    Coordinate --> Decision
    Species --> Decision
    Decision -->|admit or qualify| Published["atlas and country evidence row"]
    Decision -->|exclude| Accountability["gap, conflict, or refusal surface"]
```

## Evidence Units And Authorities

| Evidence unit | Governing surface | Required distinction |
| --- | --- | --- |
| project | `source_library/project_registry.json` | archive identity is not a sample identity |
| paper | `source_library/paper_registry.json` | publication identity is not project identity |
| captured artifact | project source bundle and supporting-material manifest | discovered URL is not recovered content |
| sample | project `sample_master.json` | source labels and stable repository identity remain linked |
| locality | project `sample_locality_evidence.json` and species `site_evidence.json` | verbatim place, resolved site, and publication precision differ |
| chronology | project `sample_chronology_evidence.json` and chronology review surfaces | source text, normalized interval, basis, and caveat remain linked |
| coordinate | species `coordinate_provenance.json` | supplied, resolved, approximate, substituted, and unresolved differ |
| publication | atlas evidence row and product manifest | visible membership is downstream of admission |

## Recovery States

```mermaid
stateDiagram-v2
    [*] --> Discovered
    Discovered --> Captured: paper and supporting material acquired
    Captured --> Extracted: stable sample rows recovered
    Extracted --> Reviewed: locality, chronology, taxonomy, and coordinates evaluated
    Reviewed --> Admitted: product requirements satisfied
    Reviewed --> Qualified: material precision limit remains visible
    Reviewed --> Excluded: required evidence is absent or conflicting
    Discovered --> Deferred: required source material unavailable
    Captured --> Deferred: sample-bearing content not recoverable
```

Tracked but deferred evidence is not equivalent to a negative scientific
result. It records what is known about the source and what remains unavailable.

## Current Evidence Depth

The generated intake review currently tracks **40 archive projects** and
**868 recovered sample rows**. Those figures describe two different
populations: the project inventory and the extracted sample evidence. Only
four projects have an exact expected-sample denominator, 22 have a defensible
minimum floor, and eight are flagged for implausibly low recovery. The
repository therefore does not present 868 as a complete census of the tracked
projects.

The point-evidence review contains **234 admitted rows**. Of these, 233 retain
supplementary-table coordinates and one uses documented named-site geocoding
at approximate confidence. These are admitted evidence rows, not proof that
every project, species, locality, or chronology has reached the same maturity.

### Evidence Depth Is Dimension-Specific

| Dimension | What the repository can establish | Remaining boundary |
| --- | --- | --- |
| source discovery | which projects, papers, and supplements are tracked | discovery does not prove sample-bearing material was recovered |
| sample recovery | which source rows became stable sample records | most projects do not have an exact expected-row denominator |
| locality | which verbatim localities resolve to sample- or group-owned sites | regional or conflicting assignments remain non-point evidence |
| coordinate | whether a pair is source-supplied or repository-resolved, with confidence | coordinate class does not imply uniform real-world precision |
| chronology | which source statement, interval, and basis belong to a sample | broad or contextual time does not authorize synthetic numeric bounds |
| publication | which rows satisfy a named product contract | admission does not establish collection completeness |

There is therefore no single collection-wide maturity score. A project can be
well documented at the paper and supplement level while its locality recovery
is incomplete; a spatially admitted sample can still have chronology that is
too broad for numeric comparison. The governing files preserve those
different states instead of averaging them into one quality label.

```mermaid
flowchart LR
    Inventory["40 tracked projects"] --> Recovery["868 recovered sample rows"]
    Recovery --> Review["identity, locality, chronology, coordinate review"]
    Review --> Points["234 admitted point-evidence rows"]
    Inventory --> Gaps["blocked, under-recovered, and unresolved projects"]
    Gaps --> Accountability["recovery review and refusal surfaces"]
```

The generated reports make both branches visible. The published branch shows
what satisfies the point contract; the accountability branch prevents the
admitted subset from masquerading as collection completeness.

## Audit A Published Animal Point

1. resolve its feature and evidence-row identifiers in the product traceability
   surface;
2. confirm the species record under
   `data/adna/species/<latin_name>/normalized/sample_records.json`;
3. inspect the species `site_evidence.json`, then follow its project linkage to
   `sample_sites.json` and `sample_locality_evidence.json`;
4. inspect project `sample_chronology_evidence.json` and the cross-project
   chronology review for temporal posture;
5. inspect `coordinate_provenance.json` for basis and precision;
6. follow the sample lineage to the project sample master, source bundle,
   paper, and captured supporting artifact;
7. confirm that the product manifest records the point's admission posture.

## Publication Boundary

A species-level presence, archive project, or paper citation cannot substitute
for a recoverable sample row. A broad locality cannot become an exact point. A
cultural period cannot acquire a synthetic numeric interval. A visible point
cannot outrank its governing evidence.

The point contract is also narrower than “animal evidence available.” A
project can contribute paper, supplement, taxonomy, or broad locality evidence
without contributing an atlas point. Conversely, a point admitted under its
present traceability and precision does not certify complete recovery of its
project. The release posture records the narrower claim that the admitted
subset satisfies its point contract while project-level recovery denominators,
blocked sources, and unresolved evidence remain visible outside that subset.

Continue with [animal source intake](../sources/animal-source-intake.md),
[sample records](../evidence/sample-records.md), [locality evidence](../evidence/localities.md),
[chronology](../evidence/chronology.md), and [point publication rules](../publications/point-rules.md).

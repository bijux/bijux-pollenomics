# Which animal samples reach the map?

We compared the ten normalized species sample tables with the retained
[point candidates](../../../data/adna/final/atlas/animal_atlas_point_candidates.json)
and [map exclusion decisions](../../../docs/report/animal_atlas_exclusion_report.json).
The two existing per-sample sources form an exact, disjoint partition of the
1,464 normalized sample IDs. We keep those original decision rows as the
entity ledger instead of copying them into a second list. The
[reconciliation result](report.json) binds all 13 inputs by size and SHA-256.

| Map decision | Sample IDs | Meaning |
| --- | ---: | --- |
| In 161 point features | 318 | Source-backed map candidate membership; no scientific admission |
| Excluded from point map | 1,146 | 378 unresolved locality, 409 without coordinate provenance, 333 failing the point contract, 26 with unresolved chronology |
| **Normalized foundation** | **1,464** | Every ID has exactly one map decision |

Eight candidate features carry a Nordic inclusion label and refer to 12
distinct sample IDs: Denmark five, Finland two and Sweden five. No Norwegian
animal feature occurs in this retained point surface; that is a product zero,
not evidence that Norway lacks ancient animal remains. Country labels and
map support classes do not establish source-country authority or qualified
biological review. Unresolved paper links and source capability decisions
remain separate; this result admits no ecological, pollen or vegetation analysis.

The [producer](replay.py) checks the normalized IDs against both original
decision sources, refuses overlap, missing IDs, duplicate mappings and broken
sample lineage, then reports the joined counts. Reproduce into a new directory
from the repository root and compare `report.json` byte for byte:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/animal-entity-capability/replay.py \
  --repository . --output artifacts/jobs/animal-entity-capability-replay
```


## Current reconciliation and source epochs

The maintained [reconciliation](report.json) at
`04f1c48579ad39775ac116cee6df1f7a858e74de`, against the installed data working
tree, returned exit zero in **0.12 s**, with **40,386,560 B** peak RSS. Its 13
raw input pins bind the current **1,464 = 318 + 1,146** partition, 161 point
features and unchanged twelve-ID Nordic subset. The 1,146 original exclusion
rows are byte-identical. The four PRJEB90141 comparator keys remain in their
source tables with five accession alternatives, but no longer supply
normalized/map identities. Dates, coordinates and source-taxon fields are
preserved. This metadata reconciliation does not resolve their specimens.

The [owning chronology account](../animal-sample-chronology.md#current-source-and-map-population)
records the qualified source and three-scope map execution. Its separate
1,475-row chronology corpus has 319 admitted temporal nodes and 1,156 refusals;
Europe-plus and Nordic each have thirteen temporal nodes. Those nodes are not
this point-locality denominator: Nordic's temporal-node labels are DK seven /
FI two / SE four, while the twelve mapped IDs above are DK five / FI two /
SE five.

## Historical source and country-record lifecycle verification

The [lifecycle account](../adna-source-lifecycle/report.json) records a **historical 1,468-ID epoch**, before the four goat identities were refused. Its retained execution covers the four actual country animal bundle producers and CSV writers; it was not rerun for the current reconciliation. The full country bundles match the retained summaries as JSON values, including localities, sample provenance, citations, warnings and chronology precision. All 48 sample CSV fields match byte for byte: Denmark five, Finland two, Norway zero and Sweden five. The Norwegian product zero remains a source/publication support limitation.

At that historical epoch, all ten normalized sample JSONs retained the animal-DNA domain and false pollen/pollen-propagation eligibility for 1,468 sample IDs. Their source families were ENA 1,411, BioProject 22, SRA 20 and GenBank 15; modalities were 1,442 archive-read records and 26 mitogenome-only records. Every one of 60 nonempty literal sample-lineage/chronology source pointers resolves to frozen retained bytes or a named ZIP member. Three compressed article/archive transports lack historical metadata digests; current frozen byte correspondence does not authenticate those original source histories.

The [capture](../adna-source-lifecycle/capture.json) records six native-zero stages, eight country CSV comparisons, four complete animal bundles and 26 maintained boundary controls. That historical source-ID partition was 322 mapped + 1,146 excluded = 1,468, in 165 point features. The capture JSON is unchanged and is not evidence for a current 1,468-ID population. This verifies the metadata lifecycle and domain separation. It supplies no accepted empirical classification, new map/browser capture, genotype result, source-rights decision or independent human biological review.



The retained atlas source-view packet authenticates all captured software bodies at its original execution epoch. Six portal-reader modules are historical Git witnesses while their current maintained software is qualified separately. Reading or transporting that fixed packet does not admit fresh source reproduction, rerun its generators or browser, or change the scientific admission of displayed records.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Every normalized animal source ID has one map membership/exclusion; actual non-pollen source flags and full four-country chronology/provenance publication contracts retain source-domain separation.

**Unsupported claim.** Scientific animal/ecological admission or source-country authority.

**Actual verification performed.** The current 13-input entity replay at committed code04f1c4857 with the qualified installed data candidate passed in0.12 s/RSS40386560 B:1464 IDs=318 mapped+1146 excluded,161 features,12 Nordic IDs/eight features. Seven current source/map/evidence regressions pass in38.94 s. The earlier six-stage native-zero lifecycle capture is historical:1468=322+1146,10 domain/refusal JSONs,60 literal source pointers,eight country CSVs,four bundles and26 boundaries. Its capture and source-input records remain unchanged and were not rerun. No human biological review or model fit.

**Remaining input or review.** The 1,464-ID point-map partition is closed, but 1,146 exclusions include unresolved locality, coordinate provenance and chronology; eleven paper links and biological/country authority remain open. Resolver: Animal source custodian and qualified provenance/biological reviewer Reopen when: Source-backed locality, coordinates, chronology, paper links and admission are decided per sample.

**Cause category.** data|qualified review

**Consequence.** Map candidates and product zeros cannot be read as biological distribution or pollen context.

**Precise next acceptance route.** Source-backed locality, coordinates, chronology, paper links and admission are decided per sample. Then update reports/science/source-cohorts.md.

**Negative or refused result.** 1,146 excluded: 378 locality, 409 coordinate provenance, 333 point contract and 26 chronology; 11 paper links unresolved.

**Matched denominator.** 1,464 IDs = 318 mapped sample IDs in 161 point features + 1,146 excluded; separate Nordic subset: 12 mapped IDs in eight features.

Retained evidence: [reports/science/animal-entity-capability/report.json](report.json), [docs/report/animal_atlas_exclusion_report.json](../../../docs/report/animal_atlas_exclusion_report.json), [reports/science/adna-source-lifecycle/report.json](../adna-source-lifecycle/report.json), [reports/science/adna-source-lifecycle/capture.json](../adna-source-lifecycle/capture.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

# Which animal samples reach the map?

We compared the ten normalized species sample tables with the retained
[point candidates](../../../data/adna/final/atlas/animal_atlas_point_candidates.json)
and [map exclusion decisions](../../../docs/report/animal_atlas_exclusion_report.json).
The two existing per-sample sources form an exact, disjoint partition of the
1,468 normalized sample IDs. We keep those original decision rows as the
entity ledger instead of copying them into a second list. The
[reconciliation result](report.json) binds all 13 inputs by size and SHA-256.

| Map decision | Sample IDs | Meaning |
| --- | ---: | --- |
| In 165 point features | 322 | Source-backed map candidate membership; no scientific admission |
| Excluded from point map | 1,146 | 378 unresolved locality, 409 without coordinate provenance, 333 failing the point contract, 26 with unresolved chronology |
| **Normalized foundation** | **1,468** | Every ID has exactly one map decision |

Eight candidate features carry a Nordic inclusion label and refer to 12
distinct sample IDs: Denmark five, Finland two and Sweden five. No Norwegian
animal feature occurs in this retained point surface; that is a product zero,
not evidence that Norway lacks ancient animal remains. Country labels and
map support classes do not establish source-country authority or qualified
biological review. The foundation still has eleven unresolved paper-link
rows, and neither the source capability matrix nor this result admits an
ecological, pollen or vegetation analysis.

The [producer](replay.py) checks the normalized IDs against both original
decision sources, refuses overlap, missing IDs, duplicate mappings and broken
sample lineage, then reports the joined counts. Reproduce into a new directory
from the repository root and compare `report.json` byte for byte:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/animal-entity-capability/replay.py \
  --repository . --output artifacts/jobs/animal-entity-capability-replay
```


## Actual source and country-record lifecycle verification

The [lifecycle account](../adna-source-lifecycle/report.json) adds a fresh execution of the four actual country animal bundle producers and CSV writers. The full country bundles match the retained summaries as JSON values, including localities, sample provenance, citations, warnings and chronology precision. All 48 sample CSV fields match byte for byte: Denmark five, Finland two, Norway zero and Sweden five. The Norwegian product zero remains a source/publication support limitation.

All ten normalized sample JSONs explicitly retain the animal-DNA domain and false pollen/pollen-propagation eligibility for 1,468 sample IDs. Their source families remain ENA 1,411, BioProject 22, SRA 20 and GenBank 15; modalities remain 1,442 archive-read records and 26 mitogenome-only records. Every one of 60 nonempty literal sample-lineage/chronology source pointers resolves to frozen retained bytes or a named ZIP member. Three compressed article/archive transports lack historical metadata digests; current frozen byte correspondence does not authenticate those original source histories.

The [capture](../adna-source-lifecycle/capture.json) records six native-zero stages, eight country CSV comparisons, four complete animal bundles and 26 maintained boundary controls. The source-ID partition stays 322 mapped + 1,146 excluded = 1,468. This verifies the metadata lifecycle and domain separation. It supplies no accepted empirical classification, new map/browser capture, genotype result, source-rights decision or independent human biological review.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Every normalized animal source ID has one map membership/exclusion; actual non-pollen source flags and full four-country chronology/provenance publication contracts retain source-domain separation.

**Unsupported claim.** Scientific animal/ecological admission or source-country authority.

**Actual verification performed.** Actual six-stage replay native0 preserved1468=322+1146source-ID partition, all10animal JSON domain/refusal flags,60literal source pointers,8human/animal CSVs and4complete animal bundles;26maintained boundaries passed. Original 1475row chronology scope remains separate. Three compressed transports have current captured hashes but no historical metadata digests; no new human review or model fit.

**Remaining input or review.** The 1,468-ID point-map partition is closed, but 1,146 exclusions include unresolved locality, coordinate provenance and chronology; eleven paper links and biological/country authority remain open. Resolver: Animal source custodian and qualified provenance/biological reviewer Reopen when: Source-backed locality, coordinates, chronology, paper links and admission are decided per sample.

**Cause category.** data|qualified review

**Consequence.** Map candidates and product zeros cannot be read as biological distribution or pollen context.

**Precise next acceptance route.** Source-backed locality, coordinates, chronology, paper links and admission are decided per sample. Then update reports/science/source-cohorts.md.

**Negative or refused result.** 1,146 excluded: 378 locality, 409 coordinate provenance, 333 point contract and 26 chronology; 11 paper links unresolved.

**Matched denominator.** 1,468 IDs = 322 mapped sample IDs in 165 point features + 1,146 excluded; separate Nordic subset: 12 mapped IDs in eight features.

Retained evidence: [reports/science/animal-entity-capability/report.json](report.json), [docs/report/animal_atlas_exclusion_report.json](../../../docs/report/animal_atlas_exclusion_report.json), [reports/science/adna-source-lifecycle/report.json](../adna-source-lifecycle/report.json), [reports/science/adna-source-lifecycle/capture.json](../adna-source-lifecycle/capture.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: e811bb68bda0cc1e7d34075752c9c8f6f8869136efb48a06a82403d35f595b8d -->
<!-- scientific-authored-source-sha256: d9721df11be77cbc12751642ab6efe5c237df902642c5c17970abf0c5a65a75c -->
<!-- scientific-verification-and-limits:end -->

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


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Every normalized animal sample ID has one point-map membership or exclusion decision.

**Unsupported claim.** Scientific animal/ecological admission or source-country authority.

**Actual verification performed.** Actual current 13-input SHA-bound reconciliation retained the exact disjoint 1,468-ID partition after source-age qualification. All 322 mapped IDs and 1,146 excluded IDs are distinct; source chronology has its separate 1,475-row denominator. This index refresh reruns no source model.

**Remaining input or review.** The 1,468-ID point-map partition is closed, but 1,146 exclusions include unresolved locality, coordinate provenance and chronology; eleven paper links and biological/country authority remain open. Resolver: Animal source custodian and qualified provenance/biological reviewer Reopen when: Source-backed locality, coordinates, chronology, paper links and admission are decided per sample.

**Cause category.** data|qualified review

**Consequence.** Map candidates and product zeros cannot be read as biological distribution or pollen context.

**Precise next acceptance route.** Source-backed locality, coordinates, chronology, paper links and admission are decided per sample. Then update reports/science/source-cohorts.md.

**Negative or refused result.** 1,146 excluded: 378 locality, 409 coordinate provenance, 333 point contract and 26 chronology; 11 paper links unresolved.

**Matched denominator.** 1,468 IDs = 322 mapped sample IDs in 165 point features + 1,146 excluded; separate Nordic subset: 12 mapped IDs in eight features.

Retained evidence: [reports/science/animal-entity-capability/report.json](report.json), [docs/report/animal_atlas_exclusion_report.json](../../../docs/report/animal_atlas_exclusion_report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

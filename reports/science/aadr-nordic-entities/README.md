# Which AADR Nordic IDs reach the country products?

We joined every AADR v66 Genetic ID whose source Political Entity is exactly
Denmark, Finland, Norway or Sweden to the four retained country sample CSVs.
The [decision ledger](decisions.csv) records all 1,325 IDs, the source panel
row numbers, coordinate and chronology review states, and whether the ID
appears in its country product. The [result](report.json) binds the two
annotation panels, release manifest, source-accountability receipt and four
published sample CSVs by byte count and SHA-256.

| Source Political Entity | Source Genetic IDs | In country product | Excluded: no source coordinates |
| --- | ---: | ---: | ---: |
| Denmark | 654 | 653 | 1 |
| Finland | 124 | 32 | 92 |
| Norway | 131 | 130 | 1 |
| Sweden | 416 | 416 | 0 |
| **Total** | **1,325** | **1,231** | **94** |

Every nonpublished ID has a missing coordinate pair in the reconciled source
evidence; every published ID has a parseable pair. This explains the exact
94-ID source-to-product difference. It does not make an absent coordinate a
zero, and it does not establish that the 1,231 country rows have passed
scientific chronology, geography or source-rights review. The retained
[source-accountability receipt](../../../data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json)
still marks country assignment, map admission and scientific admission false.
Its chronology review remains method-specific even for IDs with numeric BP
values. These human metadata rows are not pollen observations, vegetation
measurements or genotype analysis.

The [producer](replay.py) uses the existing source-panel reconciliation and
country publication outputs. It refuses a changed source digest, duplicate
country ID, mismatched country label, published ID without usable coordinates,
or a source ID omitted despite usable coordinates. Reproduce into a new
directory from the repository root, then compare both files byte for byte:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/aadr-nordic-entities/replay.py \
  --repository . --output artifacts/jobs/aadr-nordic-entity-replay
```


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Exact AADR v66 Nordic Genetic-ID to four country-product row membership and coordinate refusal accounting.

**Unsupported claim.** Chronology, source-country authority, map or scientific admission of those IDs.

**Actual verification performed.** Retained decision ledger and report bind two panels, release manifest and four product CSV hashes; index did not rerun producer.

**Remaining input or review.** The 94 absent-coordinate IDs are correctly excluded from country products, but the 1,231 country rows lack scientific chronology, geography, map, country-authority and rights admission. Resolver: AADR source custodian and chronology/geography reviewer Reopen when: Versioned source coordinates and qualified country, chronology, map and rights decisions are bound per ID.

**Cause category.** data|qualified review

**Consequence.** Keep human aDNA rows as context, not pollen, vegetation or admitted spatial events.

**Precise next acceptance route.** Obtain per-ID chronology, political-country authority, map-admission and rights decisions; rerun the AADR decision ledger and only then revise reports/science/source-cohorts.md.

**Negative or refused result.** 94 IDs excluded for missing source coordinates; 1,231 published country rows are not thereby map or scientifically admitted.

**Matched denominator.** 1,325 source IDs = 1,231 country-product rows + 94 coordinate exclusions across DK/FI/NO/SE.

Retained evidence: [reports/science/aadr-nordic-entities/report.json](report.json), [data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json](../../../data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: a02ab5ff2f991e08a5a4f3312db68a754c4a90dc83cc1a9a8ebd6271b2fd6cfd -->
<!-- scientific-authored-source-sha256: def5bebf8c7865a8a905b06aa2d80054e86b8de733dc802a6fe4dbba3ee6737a -->
<!-- scientific-verification-and-limits:end -->

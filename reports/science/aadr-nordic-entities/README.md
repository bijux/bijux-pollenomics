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

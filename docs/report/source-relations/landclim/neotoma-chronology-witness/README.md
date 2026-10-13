# FLINK and STAV chronology witnesses

The [replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/source-relations/landclim/neotoma-chronology-witness/replay.py) pairs two hash-bound private Rootsi workbooks with the
retained Neotoma/EPD source download. The [report](report.json) preserves source
identities, depth joins, age comparisons, and count-cell status without copying
the private workbook cells. The [Rootsi overlap ledger](../../rootsi-landclim-overlap/README.md)
remains a candidate metadata relation; this narrower check adds source-row
evidence. The earlier [workbook audit](../workbook-chronology/README.md) records
the unaltered age cells and their reversals.

| Sequence | Source relation | Chronology finding |
| --- | --- | --- |
| FLINK | All 109 workbook depth numbers match Neotoma dataset 54024 after multiplying by 100; the workbook header does not state a depth unit. All 270 explicit pollen-NISP pairs for the three labeled Betula, Pinus and Populus columns agree; 57 workbook zeros have no matching archive row. | The arithmetic `1950 − Neotoma calibrated BP` agrees with 108 of 109 workbook `cal AD/BC` labels within 0.05 year. At workbook sheet row 56, Neotoma depth 275 cm, the workbook says **+3910.8433**, while Neotoma sample 553036 says **5860.8 BP**, implying **−3910.8** under that arithmetic. The sole mismatch is a source discrepancy; the workbook was not changed. |
| STAV | All 77 workbook depth numbers match those of Neotoma dataset 54003 directly. Of 940 exact-name, explicit pollen-NISP cell pairs, all 940 counts agree. | The workbook has no age column. Neotoma chronology 38423 supplies 77 point ages spanning 70–10585 calibrated BP, with no per-sample older or younger bounds. This is a candidate age vector for the same depth axis, not an authenticated LandClim input chronology. |

STAV's remaining 5,374 workbook count cells have no single exact-name Neotoma
*pollen* NISP row: 4,520 workbook zeros and 854 positives. Some workbook columns
describe other elements or use different names, so those cells cannot be
interpreted as archive zeros or count disagreements. This check does not close
the count denominator or taxon mapping.

The Neotoma record identifies FLINK chronology 38438 as OxCal v3.10/IntCal04
and STAV chronology 38423 as Bacon. These are **shared EPD source-lineage
witnesses**, not independent validations of the authors' historical LandClim
inputs or age uncertainty. The publisher metadata's FLINK bounds of −50 to
12011 BP agree with the Neotoma age extrema after rounding, while the single
workbook sign discrepancy explains the workbook-only impossible −1961 BP
extremum. An authoritative corrected FLINK workbook value still requires a
source-holder record. STAV's historical age-model version and row membership
also remain unconfirmed. Workbook analytical-use rights, time-specific basin
geometry, and complete target denominators are unresolved. **Neither sequence
is admitted to LRA or dated-event claims by this comparison.**

The underlying source archive records are [FLINK](https://doi.org/10.21233/8TSN-1G04)
and [STAV](https://doi.org/10.21233/WC5X-2H35). The report binds the exact
repository Neotoma download SHA-256 and each private workbook SHA-256.

Reproduce from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/source-relations/landclim/neotoma-chronology-witness/replay.py \
  --source-root ../bijux-pollenomics-data/landclim/rootsi-workbooks \
  --output artifacts/jobs/rootsi-neotoma-chronology-witness/report.json
cmp artifacts/jobs/rootsi-neotoma-chronology-witness/report.json \
  docs/report/source-relations/landclim/neotoma-chronology-witness/report.json
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

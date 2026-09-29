# Danish EPD pollen chronology coverage

The retained [Neotoma pollen prerequisite screen](../../../source-relations/neotoma/pollen-screen/README.md) contains **279 Danish pollen-count samples at five sites**. Only 91 samples, all from Lake Solsø, have sample-owned comparable typed ages under that screen's declared rule. The other **188 samples are refused** at this prerequisite: 187 age claims at four sites have no source age type, and one Solsø calibrated claim has a negative BP bound. The [machine-readable report](report.json) retains the site, collection-unit, dataset DOI and claim-class identities.

| Source site | Core or section handles | Count samples | Comparable-age candidates | Refused | Source age-claim issue |
| --- | --- | ---: | ---: | ---: | --- |
| Lake Solsø `3432` | `SOLSOE81`, `SOLSOE83` | 92 | 91 | 1 | One calibrated claim refused for a negative BP bound; 92 separate uncalibrated radiocarbon claims are context only |
| Vejlby `3491` | `VEJLBYE4`, `VEJLBYG5` | 44 | 0 | 44 | 44 age-type-null claims |
| Trelde Klint `14265` | `TRELDKLA` | 39 | 0 | 39 | 39 age-type-null claims |
| Hollerup `23293` | `HOLLERUP` | 66 | 0 | 66 | 66 age-type-null claims |
| Harreskov `27349` | `HARRESK` | 38 | 0 | 38 | 38 age-type-null claims |
| **Total** | | **279** | **91** | **188** | **187 age-type-null claims plus one negative-bound refusal** |

These are counts of physical source sample IDs in the captured EPD/Neotoma snapshot, not five LRA-admitted cohorts. The [country-held-out observed-pollen result](../../../regions/nordic/direct-pollen/RESULTS.md) uses only the 91 selected Solsø samples and therefore scores one Danish site. It does not test transfer among Danish sites. Solsø's separate [core and basin comparison](../solsoe-source-lineage/README.md) retains additional LRA prerequisites; **zero Danish samples are LRA-admitted**.

The source site descriptions identify Hollerup's **66 samples as Eemian** and Harreskov's **38 as Cromer interglacial, middle Pleistocene**. Those 104 samples cannot enter the declared Holocene pollen transfer merely by supplying an age unit. Trelde Klint's 39 samples are described only as an interglacial paleolake, without a bound period; Vejlby's 44 come from an infilled gravel pit, without a stated period. The [2013 published EPD final-age table](../solsoe-source-lineage/pangaea-epd-age-join/README.md) contains neither of these four sites' five core handles, although it exactly corroborates Solsø's calibrated ages. Its absence is limited to that historical table and does not rule out other chronologies.

The four age-type-null groups need a source-backed age type, unit, chronology and sample mapping before any comparable-age selection for a suitable time-period study. The captured null values cannot be converted to BP or silently supplied from another record. The Solsø negative-bound sample needs an explicit chronology or exclusion decision; removing its negative bound would alter source evidence. A broader **Holocene** Danish direct-pollen evaluation must first establish site-period eligibility and source ages beyond Solsø, then predeclare a site-held-out protocol. Rights, count denominator, taxon mapping and historical basin support remain separate review questions for LRA.

The report binds the relational manifest SHA-256 `6f6777a40b67bd0704eb1a982f19e6d451cad0d6e4a41dfebf5e3f28be33105b` and pollen-screen SHA-256 `ffecf23d5f1eb9e7287b418b70a140daa1d30d8c9648672f32b37a47dbbf7b31`. To replay the source rows and exact refusal classes from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/countries/denmark/pollen-chronology-coverage/replay.py \
  --repository . \
  --output artifacts/jobs/denmark-pollen-chronology/coverage.json
cmp artifacts/jobs/denmark-pollen-chronology/coverage.json \
  docs/report/countries/denmark/pollen-chronology-coverage/report.json
```

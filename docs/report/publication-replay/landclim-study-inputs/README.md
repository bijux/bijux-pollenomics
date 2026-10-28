# LandClim II publication study input inventory

The pinned [PANGAEA 937075](https://doi.org/10.1594/PANGAEA.937075)
site-metadata workbook declares **1,128** publication rows. This
[source-bound inventory](manifest.json) retains all 1,128 metadata records,
a [row-level primary-source crosswalk](primary-source-crosswalk.csv), and
4,512 explicit [requirement refusals](refusals.csv), four per row. The
[summary](report.json) records zero authenticated historical primary-count
identities, selected chronology identities, historical-to-current revision
matches, per-sequence rights decisions and reproduction-ready rows in this
declared evidence closure. Its source labels include 84 Swedish, 66 Danish,
42 Norwegian and 31 Finnish rows; these are workbook strings, not admitted
country assignments or independent pollen cohorts.

The [records](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/publication-replay/landclim-study-inputs/records.jsonl) are publication metadata. A locator such as a
workbook row, site name, CSV filename or restriction label does not supply the
historical count table, age-model selection, source revision bridge or legal
permission for that sequence. The crosswalk deliberately leaves the
historical and current identity fields empty with explicit unresolved status.
Do not subtract the 17 author-example sites from the 1,128 rows without an
authenticated historical identity match.

The bounded [Amsoldingersee source review](../landclim-amsoldingersee-source-review/README.md)
inspects one workbook row against three current Neotoma pollen cores using
hash-bound API captures. One core matches the published sample count, but none
has an exact publication-code bridge or the author's historical chronology.
That one-row negative result does not close the full-study input lineage.

The producer is
`bijux_pollenomics_dev.essd_reproduction.study_inputs`. Rebuild from the
pinned raw workbook and receipt into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src:packages/bijux-pollenomics/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.study_inputs \
  --raw-dir data/landclim/raw \
  --output artifacts/landclim-study-inputs/replay
```

`validate_study_input_products` rebuilds the five generated files from those
raw parents and compares their bytes to this retained directory. The source
workbook and acquisition receipt are identified by SHA-256 in the manifest.
This inventory is a source-accounting result. It does not reproduce the
published LRA calculations, establish the historical 1,128 input closures,
clear sequence-specific rights or measure vegetation accuracy.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

**Supported claim.** The pinned publication metadata workbook yields a complete 1,128-row source-requirement inventory and row-level unresolved historical bridge, with four explicit refusals per row.

**Unsupported claim.** Metadata rows, filename/source labels and NR/R markers do not supply historical pollen counts, selected ages, legal permissions, independent cohorts, reproduced LRA results, country admission or measured vegetation accuracy.

**Actual verification performed.** The authored inventory, source manifest, summary and row-level requirement refusals were inspected and exact public bytes bound. Its maintained validator rebuilds five products from pinned workbook/receipt parents; this qualification runs no workbook scan, numerical calculation, historical R or new source recovery.

**Remaining input or review.** Exact historical counts/sample IDs, selected chronologies, historical-to-current revision decisions, per-sequence source-use permissions, original intermediate matrices and qualified PFT/scientific decisions remain missing in this closure.

**Cause category.** data | access/rights | comparability | qualified review

**Consequence.** Keep every row unresolved until its actual historical source closure is authenticated. Do not subtract the 17 released author examples without a historical identity bridge or reinterpret country strings as scientifically admitted cohorts.

**Precise next acceptance route.** For a named publication row, obtain authenticated historical count/chronology/transformation and revision/rights decisions, import their evidence and rerun the exact row admission. Extend only verified membership while retaining all other refusal records.

**Negative or refused result.** Zero historical count identities, chronology selections, revision matches, per-sequence rights decisions and reproduction-ready rows are authenticated. The one-row Amsoldingersee review remains negative and does not close any broader lineage.

**Matched denominator.** 1,128 metadata rows/crosswalk entries;4,512 requirement refusals,four per row. Workbook country strings include 84 Sweden/66 Denmark/42 Norway/31 Finland, not admitted independent cohorts; zero reproduction-ready rows.

- [Retained qualification evidence: docs/report/publication-replay/landclim-study-inputs/report.json](report.json) (SHA-256 `6c6f28f22b3c46d4a9adcd7b8814f07b1db304306ac0cf6c02e85cbd170c2e02`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-study-inputs/manifest.json](manifest.json) (SHA-256 `aaab3414a4168c910210b3e275b759f19fe478501de3ec5656f2e1ddcec58e93`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-study-inputs/primary-source-crosswalk.csv](primary-source-crosswalk.csv) (SHA-256 `7252e1424a072775cbbdd1172d35ab28d9b76f089040164df4bfe940fce61893`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-study-inputs/refusals.csv](refusals.csv) (SHA-256 `055f960736e349a2cd1be12dbfd201fa31040d007342f619a5e98612f2c4655f`).

- [Canonical scientific account: reports/science/publication-correspondence/published-inventory/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence/published-inventory/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

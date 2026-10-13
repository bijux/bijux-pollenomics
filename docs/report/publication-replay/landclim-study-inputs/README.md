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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence/published-inventory/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence/published-inventory/README.md) (source SHA-256 `d3c118abf989e31d5b4d97a93e2619f35e5da898bad8d7dcf4bd194df2bd6796`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

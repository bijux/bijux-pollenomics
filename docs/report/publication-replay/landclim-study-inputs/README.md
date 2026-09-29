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

The [records](records.jsonl) are publication metadata. A locator such as a
workbook row, site name, CSV filename or restriction label does not supply the
historical count table, age-model selection, source revision bridge or legal
permission for that sequence. The crosswalk deliberately leaves the
historical and current identity fields empty with explicit unresolved status.
Do not subtract the 17 author-example sites from the 1,128 rows without an
authenticated historical identity match.

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

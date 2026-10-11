# SEAD numerical analysis value lineage

The [source-bound value export](values.csv) reconciles all **60** captured
`tbl_analysis_numerical_values` rows, keyed by
`analysis_numerical_value_id`, with 60 distinct parent
`tbl_analysis_values.analysis_value_id` rows. Each parent joins through its
analysis entity, physical sample and sample group to SEAD site 6486
(Skänninge Abbey). The rows span five physical samples and ten datasets.
The [report](report.json) binds the exact admitted raw table digests, run,
build, admission and normalized materialization identities.

The typed `value` and parent `analysis_value` text are separate source fields.
They are numerically equal in 43 rows; 17 rows differ in their reported
precision. For example, numerical row 21 reports `3.90122` while its parent
reports `3.9012199999999995`. Both source spellings remain in the export,
alongside each complete raw row, source key, normalized observation ID,
relation keys, null states, qualifier, variant flag and refusal reasons.
All 60 typed and parent values are reported; no source null or parent parse
failure occurs in this capture. The producer retains distinct states for
future source-null or parse-failed rows.

The nine source value classes describe ancient DNA laboratory measurements,
including read length, sequence coverage, endogenous content and read damage.
Their two source value types are `Measurement` and `Percentage`. The export
binds each class and type to its admitted raw row and normalized semantic
relation. Neither type reports a unit ID for these classes. No
physical unit is inferred from a class name. All 60 source observations
remain refused as scientific events; this report does not admit aDNA,
vegetation evidence or a dated event. The atlas currently publishes the
parent analysis text without its typed numerical component; this export
provides a public, keyed review of that source component.

## Reproduce

From the repository root, choose an absent destination under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.sead_analysis_numerical_values \
  --data-root data --output artifacts/sead-analysis-numerical-values/replay
```

The producer verifies admitted raw bytes, normalized part digests, source
rows, parent and entity links, value states and refusals before writing.
It refuses an existing output directory. Compare `values.csv` and
`report.json` byte for byte with this directory after replay.

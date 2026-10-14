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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The 60 numerical components preserve exact typed and parent source spellings and admitted relational links.

**Unsupported claim.** Measurement/Percentage source labels do not supply physical units, accepted assays, vegetation evidence or dated events.

**Actual verification performed.** Read report.json and 60-row values.csv, including 17 precision differences and missing unit links; no source value consumer rerun.

**Remaining input or review.** Source laboratory meaning, unit/entity authority and scientific event qualification remain required.

**Cause category.** Native numerical precision and semantic authority are separate.

**Consequence.** Typed 3.90122 cannot silently overwrite parent 3.9012199999999995.

**Precise next acceptance route.** Return scoped source unit/class/entity decisions before analytical normalization or scientific event use.

**Negative or refused result.** 43 numeric equalities/17 precision differences retained; all 60 observations event-refused.

**Matched denominator.** 60 components/60 parents at 1 site 6486,5 physical samples/10 datasets/9 classes/2 source types; 0 eligible events.

Qualified authored reader SHA-256: `c6134ffcdc332da0151b0f57714226f938446bdd42143f052ee7046f0f5e4e87`.

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-numerical-values/report.json](report.json) (SHA-256 `68005ba9c3e0040e1ba3a3b5dcccf1b0faa3d80e9bbebee26e6cbef0c67f75b3`).

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-numerical-values/values.csv](values.csv) (SHA-256 `f6250fbcb8769e31ac7511a79701a2550b51b66cb63da00523494de983c71110`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

# SEAD integer analysis value lineage

The [source-bound report](report.json) reconciles all **24,701** captured
`tbl_analysis_integer_values` rows with 24,701 distinct parent
`tbl_analysis_values` rows. It verifies each admitted raw integer and parent row
against the normalized parent observation, exact integer component, entity
relation, value class, value type and semantic relation. The report records
the raw and normalized source digests, run and build identities, and class
counts. It covers 394 sites, 4,769 physical samples and 15,429 datasets.

The 16 source value classes include 4,751 tree-ring counts, 4,757 tree-age
bounds and 4,430 inferred growth-year bounds. The remaining 10,763 rows are
other source counts, including radii, sapwood, pith and ancient DNA read
counts. These roles describe source classes; they do not select a chronology
model or turn a count into an accepted scientific event. A direct eligible
chronology claim exists at the same analysis entity for 3,989 rows, a
context-only claim for 64, and no claim for 20,648. Every observation remains
refused for event admission.

All typed integers and parent display values are non-null in this capture.
Of the parent values, 22,933 compare numerically equal to the typed integer.
Another 1,763 do not parse as plain numbers, usually because the source text
includes a qualifier such as `~ 30` or `<5`. Five endogenous raw-read rows have slightly
different floating point spellings in the parent text; their IDs and both
source values are retained in the report. Neither qualified text nor a
precision difference is silently converted to an exact count. The producer
also retains distinct source-null and parse-failed states for a later capture.

The atlas source-native observation table exposes the parent
`analysis_value` text and its null state. Its typed integer component remains
in the governed normalized observation for keyed review. This compact report
summarizes that source-to-consumer relationship without copying 24,701 rows
into another public table. It does not admit pollen, land-use or dated events.

## Reproduce

From the repository root, choose an absent destination under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.sead_analysis_integer_values \
  --data-root data --output artifacts/sead-analysis-integer-values/replay
```

The producer refuses an existing output directory and rejects changed
admission, source bytes, normalized parts, source rows, relation identities or
event refusal. Compare `report.json` byte for byte with this directory after
replay.

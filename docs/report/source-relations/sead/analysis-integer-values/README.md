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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** All 24,701 typed integer components reconcile to exact parent observations and source class/entity/chronology links.

**Unsupported claim.** A typed count or nearby eligible chronology is not a measured ecological event; qualified text is not an exact integer measurement.

**Actual verification performed.** Read the integer report including all 5 precision differences, 1,763 nonnumeric displays and 16 class groups; no normalized-source replay.

**Remaining input or review.** Meaning/unit/entity classification and scientific event eligibility remain unaccepted.

**Cause category.** Typed values and parent display qualifiers carry distinct information.

**Consequence.** Tree-age/growth-year bounds are not selected ages, and laboratory read counts are not pollen NISP.

**Precise next acceptance route.** Qualify source class, count unit, entity and date roles before interpreting or aggregating these components scientifically.

**Negative or refused result.** 22,933 parent displays agree numerically, 1,763 fail plain numeric parse, 5 differ; all observations remain event-refused.

**Matched denominator.** 24,701 integer parents across 394 sites/4,769 samples/15,429 datasets; 3,989 eligible-claim links, 64 context links, 20,648 absent links; 0 events.

- [Retained qualification evidence: docs/report/source-relations/sead/analysis-integer-values/report.json](report.json) (SHA-256 `04ff5aac5ea51873b8483ebaebc9aa30a0628fab8ae913a02806f3d243a4b132`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

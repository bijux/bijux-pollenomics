# Neotoma compact sample summary derivation

The retained [report](report.json) checks one displayed field in the governed
compact site layer: the `Samples` popup value for Ageröds Mosse (Neotoma site
12). The compact layer displays `135`. The replay counts 135 distinct sample
identities with `site_id = neotoma:site:12` in the pinned relational sample
surface. It also resolves the existing lineage locators for sample 355236 and
one of its observations, verifies their site, dataset and collection-unit parent
identities, and records the path back to the compact feature.

The relational sample rows supply the count. The compact value is a derived
display to compare against that count, not an input to the count or a substitute
for sample and observation surfaces. The replay validates the relational
materialization, checks its identity against the compact lineage, and rejects a
changed compact layer, stale locator, duplicate sample identity or count drift.
The sample-ID set digest in the report binds the complete 135-ID cohort without
copying those rows into the summary.

From the repository root, replay with the configured environment:

```sh
mkdir -p artifacts/jobs/neotoma-compact-summary
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src \
.venv/bin/python docs/report/source-relations/neotoma/compact-summary/replay.py \
  > artifacts/jobs/neotoma-compact-summary/report-replay.json
cmp docs/report/source-relations/neotoma/compact-summary/report.json \
  artifacts/jobs/neotoma-compact-summary/report-replay.json
```

This bounded replay proves the site-12 `Samples` display and representative
sample-to-observation reverse trace for the pinned snapshot. It does not derive
every compact field or establish chronology selection, taxon denominators,
rights, original acquisition receipts or scientific admission.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** One Ageröds Mosse compact popup Samples value is derived from 135 distinct relational sample identities.

**Unsupported claim.** One checked popup field and reverse trace do not derive every compact attribute or qualify chronology, taxa, rights or denominator.

**Actual verification performed.** Read the compact derivation report, its source/materialization identity and representative sample/observation locators; no relational reader replay.

**Remaining input or review.** Other compact fields and source scientific prerequisites retain their independent acceptance requirements.

**Cause category.** A bounded display derivation has one-field scope.

**Consequence.** 135 is a source-sample count, not an accepted dated/pollen cohort count.

**Precise next acceptance route.** Replay the same relational-sample consumer on changed inputs and qualify each additional claimed field separately.

**Negative or refused result.** No chronology selection, taxon denominator, original acquisition authority or scientific admission is supplied.

**Matched denominator.** 1 site/1 Samples popup field; 135 distinct samples and 1 representative sample-to-observation reverse trace.

- [Retained qualification evidence: docs/report/source-relations/neotoma/compact-summary/report.json](report.json) (SHA-256 `0bb4bc99626e03dd80607fe9791ce5063777d5b2746b8035834cf81e2daa8909`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

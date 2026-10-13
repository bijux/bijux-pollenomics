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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

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

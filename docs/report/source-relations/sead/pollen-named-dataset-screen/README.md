# SEAD pollen-named dataset screen

The [source-bound screen](report.json) finds 95 dataset identities whose source
name contains “pollen.” They contain 2,063 source-native abundance observations
from 534 physical samples at 45 Swedish sites. The [sample-level export](sample-observations.csv)
retains each observation's source value, taxon relation, dataset, analysis entity,
physical sample, site, and chronology-link status. It does not label the values
as pollen grain counts or assign a date to a sample.

All 2,063 candidate observations lack an eligible chronology claim at their
analysis entity and a source unit in the admitted relation. Source
classification is unaccepted for all 2,063. A dataset name mentioning pollen
does not establish a pollen proxy. The screen therefore admits **zero pollen
time series and zero LRA samples**. These overlapping refusal reasons count
observations, not distinct samples or sites. No site chronology envelope is
used to fill the missing sample dates.

The report binds the full-evidence source run, build, raw-parent admission and
materialization manifest. The producer checks each consumed source part against
the governed manifest, reconciles all 177,763 source observations, and joins
candidate rows to their exact analysis entities. This is a negative eligibility
result for the captured snapshot, not a claim that SEAD lacks pollen elsewhere.

## Reproduce

From the repository root, choose an absent destination below `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.sead_pollen_screen \
  --data-root data --output artifacts/sead-pollen-screen/replay
```

The [producer](../../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead_pollen_screen.py)
refuses an existing output directory or changed consumed source bytes. A new
source capture or qualified proxy and chronology decisions require a fresh
screen before any eligibility claim changes.

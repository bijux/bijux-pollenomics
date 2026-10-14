# SEAD pollen-named dataset screen

The [source-bound screen](report.json) finds 95 dataset identities whose source
name contains “pollen.” They contain 2,063 source-native abundance observations
from 534 physical samples at 45 Swedish sites. The [sample-level export](sample-observations.csv)
retains each observation's source value, taxon relation, dataset, analysis entity,
physical sample, site, and chronology-link status. It also names the raw
`abundance` field and checks every candidate's source key, complete source row,
value, and null state against the admitted `tbl_abundances` payload. The
[report](report.json) records that payload's SHA-256. It does not label the values
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

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead_pollen_screen.py)
refuses an existing output directory or changed consumed source bytes. A new
source capture or qualified proxy and chronology decisions require a fresh
screen before any eligibility claim changes.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The captured pollen-name screen retains 2,063 abundance observations and their exact source-parent links with negative eligibility results.

**Unsupported claim.** A dataset name containing pollen does not establish pollen proxy, grain count unit, taxon acceptance or sample-owned date.

**Actual verification performed.** Read the screen and sample-observation export, including source abundance/null posture and all overlapping refusal reasons; no count/date imputation or source replay.

**Remaining input or review.** Qualified proxy/unit/classification and sample-owned chronology/use evidence remain missing.

**Cause category.** Dataset labels cannot replace source measurement and chronology authority.

**Consequence.** No site envelope may fill the absent analysis-entity sample dates.

**Precise next acceptance route.** Obtain exact observation-unit/proxy and chronology decisions, then rerun the same screen before admitting a time series.

**Negative or refused result.** All 2,063 lack eligible entity chronology/source units and classification; 0 admitted pollen time series or LRA samples.

**Matched denominator.** 95 pollen-named datasets/534 physical samples/45 Swedish sites/2,063 observations out of 177,763; reason counts overlap, not additional observations.

Qualified authored reader SHA-256: `54044baf50b32c33e841b68e3f0f95d5f61b0b1445b6f84b1bed1fc8b37450d6`.

- [Retained qualification evidence: docs/report/source-relations/sead/pollen-named-dataset-screen/report.json](report.json) (SHA-256 `de8d71fc02496b9766ca6b9a3c262fea206bcfcb8cdcfeb0413428ca2665e546`).

- [Retained qualification evidence: docs/report/source-relations/sead/pollen-named-dataset-screen/sample-observations.csv](sample-observations.csv) (SHA-256 `39c516f0d2c92e3c479500d332126ed34ae99e52c6df9cb7e3c3425db8baf02c`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

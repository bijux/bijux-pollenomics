# How we selected Nordic observed-pollen predictors

We asked which predictor the available training countries would select
without using their excluded target-country pollen. In our
[source-bound report](../../docs/report/regions/nordic/pollen-development/report.json),
we compared twelve fixed choices inside each
[country-held-out direct-pollen study](../../docs/report/regions/nordic/direct-pollen/RESULTS.md).
We removed the complete outer target-country pollen profile from the
training input. Three deterministic country-stratified inner folds then
withheld entire physical training sites and used only other sites in the same
500-year bin. We used the same closed 16-label Neotoma pollen subcomposition
as the published fixed comparison. We had inspected all target-country
outcomes in earlier work, so this is **development evidence**, not a fresh
confirmatory test.

We declared training mean, nearest site, inverse-distance-squared, and
CLR/WGS84 RBF-ridge at 0.25/0.50/0.75 quantiles of positive *training-site
pairwise* distances crossed with ridge 0.001/0.01/0.1. We applied half-count
smoothing only to each inner CLR training cell and scored target observed
counts without smoothing. We allowed selection only when a candidate scored
every eligible positive-count site-bin. Among complete candidates, we chose
lowest equal-site macro MAE, then Hellinger and candidate ID for ties. We
retained all **40,932** candidate attempts, including refusals, in the
compressed [trial score ledger](../../docs/report/regions/nordic/pollen-development/trial-scores.csv.gz).
Every candidate scored every eligible site-bin in this run; we attempted
**2,439** RBF fits.

| Outer country excluded | Training sites | Positive inner site-bins | Eligible inner site-bins | Selected candidate | Selected site-macro MAE | IDW site-macro MAE |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| Denmark | 83 | 1,666 | 1,656 | inverse-distance-squared | 0.028038 | 0.028038 |
| Finland | 56 | 1,255 | 1,245 | CLR RBF q75, ridge 0.1 | 0.028745 | 0.029132 |
| Norway | 32 | 513 | 510 | CLR RBF q50, ridge 0.1 | 0.029178 | 0.029840 |

We scored sites *within the outer training countries* in this table. These
are not held-out Denmark, Finland or Norway scores. The Finnish and Norwegian
development gains over IDW are small absolute fraction differences (about
0.000387 and 0.000662). We grouped by physical site rather than a buffered
spatial block; all target sites belonged to source families we had inspected
earlier. We then applied the selected settings to country-excluded training
data. The [frozen paired transfer result](nordic-observed-pollen-transfer.md)
shows that our selected Finnish and Norwegian RBF settings did not beat IDW
on matched, previously exposed target-country support.

To reproduce our result, use the current relational Neotoma snapshot and
retained Swedish training records. From the repository root, prepare exact
inputs under `artifacts/` and run the search:

For the checked-in report's exact source hashes, use product revision
`6cf0e1134193174f214cd280a96e60b08fadf22f`. The current direct-pollen
manifest has a later runner identity after source-row validation; its cohort
and numeric outputs did not change, but a fresh run has a new source lineage.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_direct_pollen prepare \
  --relational-root data/neotoma/relational \
  --raw-root data/neotoma/raw/neotoma_pollen_dataset_downloads \
  --workdir artifacts/jobs/nordic-development-inputs
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_pollen_development \
  --repository . --inputs artifacts/jobs/nordic-development-inputs \
  --output artifacts/jobs/nordic-pollen-development
```

We require the prepared input manifest to match the published direct-pollen
manifest byte identities, and we verify each country-excluded training file.
We apply [Neotoma source terms and attribution](../../docs/public/pollenomics-data/sources/neotoma.md)
to the source counts. We used no basin dimensions, PPE, LRA vegetation
estimates, HYDE or independent measured vegetation truth in this search.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Training-only inner-fold search chose one direct-pollen predictor per excluded country.

**Unsupported claim.** Untouched target-country confirmation or spatially independent generalization.

**Actual verification performed.** Retained 40,932-attempt score ledger and report are cited; index did not rerun search.

**Remaining input or review.** Training-only inner-fold selection is exact but target-country outcomes were previously inspected; physical-site folds are not spatial blocks or untouched confirmation. Resolver: Independent cohort owner and spatial/pollen reviewer Reopen when: A new spatially qualified cohort and protocol are frozen before its target pollen is opened.

**Cause category.** comparability|qualified review

**Consequence.** Inner-fold improvements are development scores, not held-out country outcomes.

**Precise next acceptance route.** A new spatially qualified cohort and protocol are frozen before its target pollen is opened. Then update reports/science/nordic-observed-pollen-transfer.md.

**Negative or refused result.** No candidate failure on eligible inner bins; earlier target-outcome exposure remains.

**Matched denominator.** DK 83 training sites/1,656 eligible inner bins; FI 56/1,245; NO 32/510; 12 fixed choices in each search.

Retained evidence: [docs/report/regions/nordic/pollen-development/report.json](../../docs/report/regions/nordic/pollen-development/report.json), [docs/report/regions/nordic/pollen-development/trial-scores.csv.gz](../../docs/report/regions/nordic/pollen-development/trial-scores.csv.gz).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 986229ecb409cb0409e52ccc8285d9b7faf907640c6ad846f50573952f525092 -->
<!-- scientific-authored-source-sha256: 9ea2ea231ecc32a218f76c5221bdae4017daf4f03c5735dc1476568ed0cadc60 -->
<!-- scientific-verification-and-limits:end -->

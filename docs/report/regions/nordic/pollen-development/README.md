# Nordic observed-pollen development search

The [source-bound report](report.json) compares twelve fixed predictor choices
inside the training set of each
[country-held-out direct-pollen study](../direct-pollen/RESULTS.md). For each
outer country, its complete country pollen profile is absent from the training
input file. Three deterministic country-stratified folds then withhold entire
physical training sites, using only other sites in the same 500-year bin. The
response is the same closed 16-label Neotoma pollen subcomposition as the
published fixed comparison. All country outcomes had already been inspected in
prior work, so this is **development evidence**, not a fresh confirmatory test.

The candidate set is training mean, nearest site, inverse-distance-squared, and
CLR/WGS84 RBF-ridge at the 0.25/0.50/0.75 quantiles of positive *training-site
pairwise* distances crossed with ridge penalties 0.001/0.01/0.1. Each inner
training cell receives half-count smoothing for CLR; target observed counts are
scored without smoothing. A candidate can be selected only if it scores every
eligible positive-count site-bin. Among complete candidates, lowest equal-site
macro MAE wins, followed by Hellinger and candidate ID for ties. The compressed
[trial score ledger](trial-scores.csv.gz) retains all **40,932** candidate
attempts, including site, bin, fold, score and refusal status. Every candidate
scored every eligible site-bin in this run; **2,439** RBF fits were attempted.

| Outer country excluded | Training sites | Positive inner site-bins | Eligible inner site-bins | Selected candidate | Selected site-macro MAE | IDW site-macro MAE |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| Denmark | 83 | 1,666 | 1,656 | inverse-distance-squared | 0.028038 | 0.028038 |
| Finland | 56 | 1,255 | 1,245 | CLR RBF q75, ridge 0.1 | 0.028745 | 0.029132 |
| Norway | 32 | 513 | 510 | CLR RBF q50, ridge 0.1 | 0.029178 | 0.029840 |

These numbers score sites *within the outer training countries*. They are not
the held-out Denmark, Finland or Norway scores and do not establish that a tuned
RBF model improves transfer. The gains over IDW in the Finnish and Norwegian
development sets are small absolute fraction differences (about 0.000387 and
0.000662). All target sites were already part of source families under prior
inspection; spatial grouping here is by physical site, not a buffered spatial
block. The selected settings were subsequently applied to country-excluded
training data. The [frozen paired transfer result](../selected-pollen-transfer/README.md)
shows that the tuned Finnish and Norwegian RBF settings did not beat IDW on
their matched, previously exposed target-country support.

Reproduction requires the current relational Neotoma snapshot and the retained
Swedish training records. From the repository root, prepare exact input files
under `artifacts/` and run the search:

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

The producer requires the prepared input manifest to match the published
direct-pollen manifest byte identities and verifies each country-excluded
training file. [Neotoma source terms and attribution](../../../../public/pollenomics-data/sources/neotoma.md)
apply to the source counts. This search uses neither basin dimensions nor PPE,
LRA vegetation estimates, HYDE or independent measured vegetation truth.

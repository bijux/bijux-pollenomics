# Swedish whole-site pollen prediction by training scope

The [governed report](report.json) compares three fixed observed-pollen
predictors on the same three Swedish physical sites and 31 LandClim author
target taxa. Each target site's entire profile is absent from its predictor
input. `sweden_only` trains on the other two Swedish sites; `four_country`
adds 81 Denmark/Finland/Norway sites to those same two. Every target uses the
same source age-bin ID and target count denominator in both scopes. This is
**previously exposed development evidence**, not a fresh confirmation, an
LRA reconstruction or measured vegetation accuracy.

The [prepared fold inputs](prepared/prepare.json) bind retained Nordic and
Swedish manifests, six whole-site folds and sealed outcome identity. The
[prediction freeze](frozen/freeze.json), SHA-256
`8ff7979c370465762b0903ed1551f1b78161dade7fda60e2ed5f2ceea3182f8b`,
contains all six source-excluded prediction products before the scorer reads
the retained target outcome file. [Coverage](coverage.csv), [all scores]
(scores.csv) and [paired scores](paired-scores.csv) retain every scope, site,
bin and method. The `sweden_only` scope predicts 39 of 54 candidate site-bins
and refuses 15 for insufficient contemporaneous training sites. The
`four_country` scope predicts all 54. Exactly **39 site-bins** across three
sites have paired scores for every fixed method (117 paired rows).

| Method | Sweden-only site-macro MAE | Four-country site-macro MAE | Difference |
| --- | ---: | ---: | ---: |
| Training mean | 0.035844 | 0.032935 | −0.002909 |
| Nearest site | 0.032289 | 0.026716 | −0.005573 |
| Inverse-distance-squared | 0.032846 | 0.023226 | −0.009620 |

These MAE values are fractions of the closed 31-target pollen composition,
averaged equally over each site's **shared** scored bins and then over the
three sites. Negative differences favor four-country training on this metric.
For inverse-distance-squared, the four-country scope has lower site-average
MAE at all three sites, but most of its average gain comes from Abborrtjärnen
(about −0.027879 versus −0.000226 and −0.000754 at the other sites). The
training mean loses at two of three sites despite its lower overall mean;
nearest-site predictions tie on two sites. The matching [Hellinger distances]
(report.json) have the same mean direction, but neither metric estimates
vegetation skill. The additional Nordic sites change both spatial support
and training density, so this comparison does not identify a causal country
effect or a universally best model.

The producer is
`bijux_pollenomics_dev.source_completion.swedish_training_scope`. From the
repository root, use **absent** destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_training_scope prepare \
  --repository . --output artifacts/jobs/swedish-training-scope-inputs-replay
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_training_scope predict \
  --prepared artifacts/jobs/swedish-training-scope-inputs-replay \
  --output artifacts/jobs/swedish-training-scope-predictions-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_training_scope score \
  --repository . --prepared artifacts/jobs/swedish-training-scope-inputs-replay \
  --frozen artifacts/jobs/swedish-training-scope-predictions-replay \
  --freeze-sha256 8ff7979c370465762b0903ed1551f1b78161dade7fda60e2ed5f2ceea3182f8b \
  --output artifacts/jobs/swedish-training-scope-scores-replay
```

For a changed source or producer, replace the literal freeze digest with the
new digest only after reviewing and retaining the prediction file. Compare
replayed result bytes to this directory. This study fixes an age-bin match;
explicit time displacement, uneven spatial sampling sensitivity beyond the
three-site macro score, real Nordic LRA and independent vegetation pairing
remain separate work.

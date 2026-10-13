# What we learned from two Swedish training scopes

We asked whether adding eligible pollen sites from Denmark, Finland and
Norway changed predictions for three Swedish physical sites. In our
[governed report](../../docs/report/regions/nordic/swedish-training-scope/report.json),
we compared three fixed observed-pollen predictors on the same 31 LandClim
author target taxa. We removed each target site's entire profile from both
predictor inputs. `sweden_only` trains on the other two Swedish sites;
`four_country` adds 81 Denmark/Finland/Norway sites. We used the same source
age-bin ID and target count denominator in both scopes. We treat the result
as **previously exposed development evidence**, not fresh confirmation,
LRA reconstruction or measured vegetation accuracy.

Our [prepared fold inputs](../../docs/report/regions/nordic/swedish-training-scope/prepared/prepare.json)
bind retained Nordic and Swedish manifests, six whole-site folds and sealed
outcome identity. The
[prediction freeze](../../docs/report/regions/nordic/swedish-training-scope/frozen/freeze.json), SHA-256
`8ff7979c370465762b0903ed1551f1b78161dade7fda60e2ed5f2ceea3182f8b`,
contains all six source-excluded prediction products. We opened the target
outcome file only after that freeze. We retained every scope, site, bin and
method in [coverage](../../docs/report/regions/nordic/swedish-training-scope/coverage.csv),
[all scores](../../docs/report/regions/nordic/swedish-training-scope/scores.csv)
and [paired scores](../../docs/report/regions/nordic/swedish-training-scope/paired-scores.csv).
`sweden_only` predicted 39 of 54 candidate site-bins and refused 15 for
insufficient contemporaneous training sites. `four_country` predicted all
54. Exactly **39 site-bins** across three sites have paired scores for every
fixed method (117 paired rows).

| Method | Sweden-only site-macro MAE | Four-country site-macro MAE | Difference |
| --- | ---: | ---: | ---: |
| Training mean | 0.035844 | 0.032935 | −0.002909 |
| Nearest site | 0.032289 | 0.026716 | −0.005573 |
| Inverse-distance-squared | 0.032846 | 0.023226 | −0.009620 |

We calculated these MAEs as fractions of the closed 31-target pollen
composition, averaging equally over each site's **shared** scored bins and
then over the three sites. Negative differences favor four-country training
on this metric. For inverse-distance-squared, four-country training has lower
site-average MAE at all three sites, but most of its average gain comes from
Abborrtjärnen (about −0.027879 versus −0.000226 and −0.000754 at the other
sites). The
training mean loses at two of three sites despite its lower overall mean;
nearest-site predictions tie on two sites. The matching
[Hellinger distances](../../docs/report/regions/nordic/swedish-training-scope/report.json)
have the same mean direction. We do not use either metric to estimate
vegetation skill. The additional Nordic sites change spatial support and
training density together, so we cannot isolate a causal country effect or
declare one universally best model.

We produced this result with
`bijux_pollenomics_dev.source_completion.swedish_training_scope`. To
reproduce it from the repository root, use **absent** destinations under
`artifacts/`:

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

For a changed source or producer, we replace the literal freeze digest only
after reviewing and retaining the new prediction file. We compare replayed
result bytes with this directory. We fixed an age-bin match in this study;
our separate [age and distance sensitivity](sweden-spatiotemporal-sensitivity.md)
probes adjacent nominal bins and near-site removal on the same exposed cohort.
Real Nordic LRA and independent vegetation pairing remain separate work.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Matched Swedish-only versus four-country training comparison on closed author-target pollen.

**Unsupported claim.** Causal country effect or population-wide Swedish skill.

**Actual verification performed.** Retained prepared/frozen/coverage/paired-score receipts are cited; index did not rerun.

**Remaining input or review.** Adding Nordic sites changes training density and geography together on three prior-exposed Swedish sites, so the matched pollen gain cannot isolate a causal country effect or population skill. Resolver: Independent Swedish cohort and spatial-design reviewer Reopen when: A fresh grouped matched-support design separates site density from geography before stronger transfer claims.

**Cause category.** comparability|qualified review

**Consequence.** Training geography and density change together; report matched pollen, not vegetation.

**Precise next acceptance route.** A fresh grouped matched-support design separates site density from geography before stronger transfer claims. Then update reports/science/pollen-prediction.md.

**Negative or refused result.** Sweden-only refuses 15/54 bins; four-country predicts 54/54.

**Matched denominator.** Three exposed sites; 39 shared bins ×three methods =117 paired rows; IDW 0.032846 vs 0.023226 equal-site MAE.

Retained evidence: [docs/report/regions/nordic/swedish-training-scope/report.json](../../docs/report/regions/nordic/swedish-training-scope/report.json), [docs/report/regions/nordic/swedish-training-scope/paired-scores.csv](../../docs/report/regions/nordic/swedish-training-scope/paired-scores.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 971e7d70bd2ebef212c71ab1540e9f38470bf6cda948402b8a80485328fa38ee -->
<!-- scientific-authored-source-sha256: f314ad31c3ce166f7c8ea2aa2b03ed82c097c8026bb969008711c33e11f39246 -->
<!-- scientific-verification-and-limits:end -->

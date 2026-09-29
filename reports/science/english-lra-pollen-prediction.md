# Constrained LOVE on author source pollen

This exploratory English author example uses 15 eligible sites in the source
window 1250–1750 BP. The 31-target author pollen counts total 20,732 NISP.
The prepared input excludes `Filipendula` (159 NISP, 0.767%) because its
published fall speed of 0.006 m/s is outside the selected optimized LOVE
transport contract. The resulting **30-target closed composition** is not a
whole-pollen or whole-vegetation estimate. The producer keeps the original
count denominator and excluded mass alongside every exact source hash.

The model uses the published remaining PPE and fall-speed values, the existing
homogeneous author-example basin/ring assumptions, deterministic REVEALS and
ring-taxon-preserving LOVE. A single uniform-start SLSQP search constrains
each local cover to nonnegative fractions summing to one. Its declared limits
are 300 iterations, 16,000 objective evaluations and a `1e-8` objective
tolerance, with no convergence waiver. The initial 120-iteration full-fold
run produced 149 of 195 training products but zero fold predictions because
46 training fits refused. The revised limit was selected from those training
failures before any target pollen was opened. This is a development comparison with
the prior analytical and differential-evolution attempts. The original R
source does not use this optimizer.

The held-out workflow selects one physical site per outer fold. It recomputes
regional REVEALS and training-site LOVE from training pollen; the target
site's pollen is opened only after its prediction product is published and
authenticated. Predicted vegetation is LRA-derived; no independent measured
vegetation is available for an accuracy score. These sites are English author
examples, so this experiment does not admit Swedish or four-country LRA input.

## Source-bound result

The [retained report](../../docs/report/pollen-reconstruction/author-lra-constrained/report.json) binds source, prediction and score manifests.
All 15 sites rotated as targets. Fourteen folds published three predictions
each; the BECKHAM fold refused because training LOVE fits for CUTHILL2,
HANGINGS and LONGBREACH did not converge. Of 195 training items, 192
completed and three refused. Those three source requests still refused in a
separate bounded 600-iteration check. The new solver preserves full-precision
closed cover fractions; applying the legacy four-decimal source rounding had
caused a `1.0002` fraction sum and was correctly rejected by the consumer.

The 42 published predictions were frozen before the 14 target pollen rows
were opened. The report verifies that no target record occurs in its prediction
input closure. The [fold table](../../docs/report/pollen-reconstruction/author-lra-constrained/folds.csv), [30-taxon vegetation and forward-pollen
predictions](../../docs/report/pollen-reconstruction/author-lra-constrained/predictions.csv) and [held-out scores](../../docs/report/pollen-reconstruction/author-lra-constrained/scores.csv) retain all method
rows and the BECKHAM refusal. Site-mean pollen MAE on the 14 scored sites is
0.026273 for the LRA training mean, 0.021132 for nearest training site and
0.021088 for inverse-distance-squared interpolation (fractions of the closed
30-target pollen composition). These are development scores on previously
exposed author examples, with overlapping outer training sets. No vegetation
accuracy, uncertainty interval or broader spatial generalization is claimed.

The [matched direct-pollen comparison](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/comparison.json) applies
the same three fixed spatial methods to observed training pollen on these
exact 14 sites and 30 taxa. Its prediction manifest and all 45 unscored
site-method [prediction rows](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/predictions.json) were retained
before the direct target outcomes were opened; the [paired scores](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/matched-scores.csv)
exclude BECKHAM to match the LRA support. Direct-pollen MAE is 0.020496
versus LRA 0.026273 for training mean, 0.019552 versus 0.021132 for nearest
site, and 0.018579 versus 0.021088 for inverse-distance-squared. All three
fixed direct-pollen baselines are lower on this matched development support.
This compares pollen prediction under the declared center-distance geometry;
the direct method uses all 14 training pollen sites, while the LRA route uses
one as its regional anchor and 13 as local reconstruction predictors. It does
not measure vegetation accuracy or establish an independent final test.

The [paired site sensitivity](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/site-sensitivity.json) binds the
published comparison and 42 score rows by SHA-256. Direct pollen has lower MAE
at 13/14 sites for training mean, 7/14 for nearest site, and 10/14 for
inverse-distance-squared interpolation. The nearest-site median paired
direct-minus-LRA difference is **+0.000244**, despite its negative mean of
**−0.001580**; the mean advantage is concentrated in sites with larger direct
gains. Omitting any one scored site leaves all three mean differences negative,
but these correlated English sites and overlapping training folds do not
support a sampling confidence interval or spatial-transfer claim. BECKHAM
remains excluded from every matched comparison because its LRA fold refused.

The [matched Hellinger result](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger.json) reopens the
same 14 raw target rows after both prediction sets were frozen. It binds the
source experiment, direct prediction manifest, LRA prediction identities and
LRA score table. The distance uses the original observed 30-taxon composition,
without smoothing target counts. Site-macro distances are:

| Fixed method | Direct pollen | LRA forward pollen | Sites favoring direct |
| --- | ---: | ---: | ---: |
| Training mean | 0.282082 | 0.360671 | 14/14 |
| Nearest site | 0.255767 | 0.286001 | 7/14 |
| Inverse-distance-squared | 0.243673 | 0.285415 | 11/14 |

These are descriptive distances on the same prior-exposed English support. The
14 sites do not provide a sampling interval or independent vegetation truth.

The [site influence result](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger-sensitivity.json)
pins that Hellinger report and omits each site in turn. Every omitted-site
mean direct-minus-LRA difference remains negative: training mean
`[-0.082443, -0.070006]`, nearest site `[-0.035318, -0.018215]`, and
inverse-distance-squared `[-0.046139, -0.034002]`. Nearest site still favors
direct at only 7/14 individual sites, so the negative average alone does not
say every site agrees. This is influence accounting, not an independent
confidence interval or a vegetation score.

## Basin radius in the forward consumer

We tested the effect of the declared author-example lake radius on the
forward-pollen calculation. We kept all 42 published LRA vegetation estimates,
regional cover values, PPE, fall speeds and training fits fixed, and changed
each target's circular radius to 80% or 120% of its declared value. The
[prediction freeze](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/frozen/predictions.json)
contains 126 projections for the 14 scored sites and three fixed methods.
At the original radius, all 42 pollen fractions reproduce exactly. We then
opened the observed target counts and retained the
[126 paired scores](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/scored/scores.csv)
and [method summaries](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/scored/report.json).

For inverse-distance-squared vegetation, site-macro MAE is 0.021032 at 80%,
0.021088 at the declared radius and 0.021457 at 120%; Hellinger is 0.283976,
0.285415 and 0.289825. The nearest-site method follows the same aggregate
direction, while training-mean MAE changes in the opposite direction and its
Hellinger result is mixed. Individual site directions also differ. We treat
this as a forward-transport sensitivity on already exposed English outcomes,
not radius selection or a refitted LRA score. The original basin circles are
model assumptions; the diagnostic cannot transfer a radius to a Swedish core
or establish age-specific basin geometry. The
[governed method account](../../docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/README.md)
gives all method values and reproduction commands.
From the repository root, with a private author source capsule and an absent
output destination:

```sh
source_root=/path/to/private/landclim/author-reference
job=artifacts/jobs/author-lra-constrained-reproduction
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.essd_reproduction.author_lra_development \
  --author-source-root "$source_root" --output "$job/source-inputs"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/prepare.py \
  --source "$job/source-inputs" --destination "$job/constrained-inputs"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_run \
  --inputs "$job/constrained-inputs" --cache-root "$job/cache" \
  --output "$job/predictions"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/score.py \
  --inputs "$job/constrained-inputs" --predictions "$job/predictions" \
  --destination "$job/scores" \
  --prediction-manifest-sha256 "$published_prediction_sha256"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/report.py \
  --inputs "$job/constrained-inputs" --predictions "$job/predictions" \
  --scores "$job/scores" --destination "$job/report" \
  --prediction-manifest-sha256 "$published_prediction_sha256" \
  --score-manifest-sha256 "$published_score_sha256"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py predict \
  --inputs "$job/constrained-inputs" --destination "$job/direct-predictions"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py compare \
  --inputs "$job/constrained-inputs" --direct-predictions "$job/direct-predictions" \
  --lra-scores "$job/report/scores.csv" --destination "$job/direct-comparison" \
  --prediction-manifest-sha256 "$published_direct_sha256"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py site-sensitivity \
  --matched-scores "$job/direct-comparison/matched-scores.csv" \
  --comparison "$job/direct-comparison/comparison.json" \
  --output "$job/site-sensitivity.json"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py hellinger \
  --inputs "$job/constrained-inputs" \
  --direct-predictions "$job/direct-predictions" \
  --lra-predictions "$job/report/predictions.csv" \
  --lra-scores "$job/report/scores.csv" \
  --lra-report "$job/report/report.json" \
  --comparison "$job/direct-comparison/comparison.json" \
  --output "$job/paired-hellinger.json"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/direct_comparison.py hellinger-sensitivity \
  --hellinger "$job/paired-hellinger.json" \
  --output "$job/paired-hellinger-sensitivity.json"
```

Set `published_prediction_sha256` to the digest printed by the prediction
command, and `published_score_sha256` to the digest printed by the score
command. Set `published_direct_sha256` to the digest printed by the direct
prediction command. Retain each before invoking its consumer.

The execution command requires the repository's installed package environment;
the local package source roots can be supplied through `PYTHONPATH` when using
an editable source checkout.

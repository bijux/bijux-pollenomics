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

The [retained report](report.json) binds source, prediction and score manifests.
All 15 sites rotated as targets. Fourteen folds published three predictions
each; the BECKHAM fold refused because training LOVE fits for CUTHILL2,
HANGINGS and LONGBREACH did not converge. Of 195 training items, 192
completed and three refused. Those three source requests still refused in a
separate bounded 600-iteration check. The new solver preserves full-precision
closed cover fractions; applying the legacy four-decimal source rounding had
caused a `1.0002` fraction sum and was correctly rejected by the consumer.

The 42 published predictions were frozen before the 14 target pollen rows
were opened. The report verifies that no target record occurs in its prediction
input closure. The [fold table](folds.csv), [30-taxon vegetation and forward-pollen
predictions](predictions.csv) and [held-out scores](scores.csv) retain all method
rows and the BECKHAM refusal. Site-mean pollen MAE on the 14 scored sites is
0.026273 for the LRA training mean, 0.021132 for nearest training site and
0.021088 for inverse-distance-squared interpolation (fractions of the closed
30-target pollen composition). These are development scores on previously
exposed author examples, with overlapping outer training sets. No vegetation
accuracy, uncertainty interval or broader spatial generalization is claimed.

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
```

Set `published_prediction_sha256` to the digest printed by the prediction
command, and `published_score_sha256` to the digest printed by the score
command. Retain each before invoking its consumer.

The execution command requires the repository's installed package environment;
the local package source roots can be supplied through `PYTHONPATH` when using
an editable source checkout.

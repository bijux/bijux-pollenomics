# Analytic gradient diagnostic for constrained LOVE

The governed [English constrained LOVE study](../README.md) refused the BECKHAM
held-out fold because its CUTHILL2, HANGINGS and LONGBREACH training LOVE fits
did not converge. This source-bound development diagnostic asks whether an exact
derivative of the **same** log-Euclidean LOVE objective resolves those three
SLSQP line-search failures. The 30-taxon closed subcomposition, regional
handoff, uniform start, nonnegative simplex, two local rings, one repeat,
300-iteration limit, 16,000-objective-evaluation limit and `ftol=1e-8` remain
fixed. No held-out target pollen is opened or scored.

[baseline.json](baseline.json) freezes the original request SHA-256 and both
ring diagnostics for each training item, plus the governed source experiment
and private-source manifest identities. [replay.py](replay.py) checks those
identities against fresh prepared inputs, rebuilds each training-only request,
and requires the original finite-difference SLSQP to reproduce its stop
message, iteration count, evaluation count and objective within `1e-10`. It
checks the analytic derivative against tangent and off-simplex finite
differences at positive cover points before running the six bounded fits. The
gradient differentiates LOVE's internal `cover / cover.sum()` normalization,
which matters for the off-simplex values SLSQP may evaluate.

| BECKHAM-fold training site | Original SLSQP, each ring | Analytic gradient SLSQP, each ring |
| --- | --- | --- |
| CUTHILL2 | refused; 147 iterations, 4,898 evaluations, objective 0.823088680 | refused; 120 iterations, 402 evaluations, objective 0.823088682 |
| HANGINGS | refused; 129 iterations, 4,210 evaluations, objective 1.116182207 | converged; 110 iterations, 313 evaluations, objective 1.116182165 |
| LONGBREACH | refused; 156 iterations, 5,123 evaluations, objective 0.587411646 | refused; 154 iterations, 540 evaluations, objective 0.587410833 |

All six original fits reproduced their frozen diagnostics exactly. The largest
scaled finite-difference discrepancy was `2.79e-8` in tangent directions and
`7.42e-9` in ambient coordinates. The full-precision results are in
[report.json](report.json). Exact derivatives reduce objective evaluations and
recover HANGINGS, but two training sites still refuse. **BECKHAM remains an
incomplete fold with no LRA prediction or score.** A smaller objective at a
refused fit does not waive convergence. This prior-exposed English development
result supplies neither measured vegetation accuracy nor Nordic LRA admission.

Recreate the prepared inputs from the private author source capsule and write a
new report under `artifacts/`:

```sh
job=artifacts/jobs/author-love-gradient-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.essd_reproduction.author_lra_development \
  --author-source-root /path/to/private/landclim/author-reference \
  --output "$job/source-inputs"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/prepare.py \
  --source "$job/source-inputs" --destination "$job/prepared"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py \
  --prepared "$job/prepared" --output "$job/report.json"
cmp "$job/report.json" \
  docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json
```

Use an absent job directory. The replay deliberately publishes no LRA product
and does not run the complete 15-fold consumer.

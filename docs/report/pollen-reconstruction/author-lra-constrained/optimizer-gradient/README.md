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
and private-source manifest identities. [replay.py](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/replay.py) checks those
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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** An exact derivative of the same normalized log-Euclidean LOVE objective reduces SLSQP evaluation counts and recovers HANGINGS under fixed source inputs, objective, constraints, start and budgets; the BECKHAM outer fold remains incomplete.

**Unsupported claim.** A completed BECKHAM held-out prediction/score, permission to score nonconverged fits, measured vegetation accuracy or Nordic LRA source admission.

**Actual verification performed.** The reader, frozen original diagnostics and retained derivative report were inspected. The retained replay reproduces all six original ring-fit stop/iteration/evaluation/objective diagnostics and checks tangent/off-simplex finite differences before analytic-gradient fitting. This qualification executes none of those fits or numerical derivative checks.

**Remaining input or review.** CUTHILL2 and LONGBREACH still refuse under the unchanged analytic-gradient request. Exact derivatives cannot supply source-compatible valid convergence, missing physical basin interpretation, independent vegetation truth or qualified ecological review.

**Cause category.** algorithm/numerical | assumption | comparability | qualified review

**Consequence.** Retain convergence as an acceptance requirement. Lower evaluation counts or a slightly lower refused objective do not turn the incomplete outer fold into a scored prediction.

**Precise next acceptance route.** Diagnose the remaining source-bound convergence failures under a separately declared development protocol, preserve fixed objective/constraint checks and all refused outcomes, then run only a newly justified evaluation. Independent ecological claims require their own admitted cohort and vegetation measurements.

**Negative or refused result.** HANGINGS converges in both rings; CUTHILL2 and LONGBREACH still refuse in both. BECKHAM receives no LRA prediction or score. Largest scaled derivative differences are 2.79e-8 tangent and 7.42e-9 ambient; these checks do not waive fit convergence.

**Matched denominator.** 3 failed training sites ×2 local rings =6 original diagnostics and 6 analytic-gradient ring fits, on a closed 30-taxon axis. Uniform start, one repeat,300 iterations,16,000 objective evaluations and ftol 1e-8 are fixed caps/settings; no held-out target pollen is opened or scored.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/baseline.json](baseline.json) (SHA-256 `68afb09419754130f482783397f58b12c7c06ee041430b24d264dc7f9c30e009`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-lra-constrained/optimizer-gradient/report.json](report.json) (SHA-256 `8ce87d7083b0dde01d9030bb82bbd6ea9d3193dc4c52fc0ad7c9346894d8774d`).

- [Canonical scientific account: reports/science/english-lra-pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/english-lra-pollen-prediction.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

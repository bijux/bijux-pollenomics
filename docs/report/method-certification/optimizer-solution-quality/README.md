# LOVE optimizer solution quality on shared objectives

The [three declared objectives](cases.json) are direct numerical calls to the
DISQOVER 0.9.14 `tf` LOVE objective. The [R solver](solver.R) uses the actual
source-installed `RcppDE::DEoptim`; the [Python replay](replay.py) uses the
engine's bounded `optimize_box`. Both receive identical deposition, regional
background, pollen, PPE, box bounds and iteration cap. Each side also evaluates
the other side's selected candidate. The retained [summary](summary.csv),
[R fits](r-fits.csv), [Python fits](python-fits.csv), [R session](r-session.txt)
and [source identity report](report.json) preserve the results and runtime.

All three objective values are within the declared `1e-4` gap of independently
derived optima, and every cross-engine evaluation differs from the producing
engine's objective by less than the declared `1e-10` absolute tolerance.
The symmetric, constrained-boundary and composition-ambiguous examples probe
different optimizer geometry. The ambiguous objective has multiple equally
good cover vectors, so vector equality would be a false solution-quality
criterion. Python reported success after 29–40 iterations and 600–1,230
evaluations. R used the complete 400-iteration cap (8,020 or 12,030
evaluations) in each case; its attained objective is accurate on these
examples, while the cap alone does not establish an R convergence event.

The same integer seed does not pair R and Python random streams. This study
compares achieved objective quality and common-candidate function values,
not identical search trajectories or stochastic full-wrapper draws. The
[original R oracle](../original-r-reference/README.md) separately pairs the
LOVE objective and wrapper on supplied candidates, and pairs regional REVEALS
count/PPE draws. Paired **local stochastic LOVE** draws remain an open
comparison. Neither result establishes ecological prediction skill or a global
guarantee for arbitrary LOVE landscapes.

Replay with the exact installed DISQOVER 0.9.14 source library and Rscript,
using a new absent output directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/method-certification/optimizer-solution-quality/replay.py \
  --repository . \
  --library artifacts/jobs/live-original-r-certified/library \
  --rscript /usr/local/bin/Rscript \
  --output artifacts/jobs/optimizer-solution-quality/reproduction
```

The private library path is a local custody example, not a portable
dependency. A different machine must provision the locked source archive and
dependencies before replay. The producer refuses an archive/installed-source
marker mismatch and checks numerical gaps before writing its passed report.

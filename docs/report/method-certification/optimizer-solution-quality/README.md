# LOVE optimizer solution quality on shared objectives

The [three declared objectives](cases.json) are direct numerical calls to the
DISQOVER 0.9.14 `tf` LOVE objective. The [R solver](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/method-certification/optimizer-solution-quality/solver.R) uses the actual
source-installed `RcppDE::DEoptim`; the [Python replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/method-certification/optimizer-solution-quality/replay.py) uses the
engine's bounded `optimize_box`. Both receive identical deposition, regional
background, pollen, PPE, box bounds and iteration cap. Each side also evaluates
the other side's selected candidate. The retained [summary](summary.csv),
[R fits](r-fits.csv), [Python fits](python-fits.csv), [R session](r-session.txt)
and [source identity report](report.json) preserve the results and runtime.

All three objective values are within the declared `1e-4` gap of independently
derived optima, and every cross-engine evaluation differs from the producing
engine's objective by less than the declared `1e-10` absolute tolerance.
The symmetric, constrained-boundary and composition-ambiguous examples probe
different optimizer geometry. The case arrays, seed and iteration cap are
authored study choices retained as configuration. Their custody does not
reproduce an optimizer run or establish independent scientific approval.
The ambiguous objective has multiple equally
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
count/PPE draws. The separate [local stochastic LOVE comparison](../paired-love-draws/README.md)
pairs explicit local count/PPE draws. None of these results establishes
ecological prediction skill or a global guarantee for arbitrary LOVE
landscapes.

First build the source-locked R library with the [current R reference
producer](../current-r-oracle/README.md#reproduction). Replay with that
library and Rscript, using a new absent output directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python docs/report/method-certification/optimizer-solution-quality/replay.py \
  --repository . \
  --library artifacts/jobs/native-r-reproduction/library \
  --rscript /usr/local/bin/Rscript \
  --output artifacts/jobs/optimizer-solution-quality/reproduction
```

The generated library path is a local run product, not a portable dependency.
A different machine must provision the locked source archive and dependencies
before replay. The producer refuses an archive/installed-source
marker mismatch and checks numerical gaps before writing its passed report.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** Three declared objective surfaces compare retained RcppDE and bounded Python candidates by actual objective and cross-evaluation gaps, with separate handling of nonunique minimizing vectors.

**Unsupported claim.** Small objective gaps do not prove parameter identifiability, unique vector recovery, calibrated confidence, convergence of the R run, paper reproduction or ecological accuracy.

**Actual verification performed.** Reviewed the three-case objective contract, retained candidate/evaluation summaries and exact report/case JSON bytes. No optimizer, RcppDE process or independent objective computation was executed in this reader qualification.

**Remaining input or review.** The configured current-source owner must replay exact cases and candidate cross-evaluation; an applied scientific objective additionally needs identifiable parameters and justified observation/model assumptions.

**Cause category.** Bounded numerical objective correspondence with nonunique solutions and iteration limits.

**Consequence.** Objective agreement can support the named mathematical comparison even when coordinates differ; reaching a fixed iteration cap supplies no convergence certificate.

**Precise next acceptance route.** Replay the three declared symmetric, boundary and ambiguous cases under frozen budgets and compare both candidates in both objectives before interpreting any fitted physical parameter.

**Negative or refused result.** The R comparator reaches its 400-iteration cap. Ambiguous/nonunique vectors remain acceptable only under the stated objective-gap criterion, not as evidence of unique recovered parameters.

**Matched denominator.** Three objective cases; Python 29–40 iterations and 600–1230 evaluations, R 400-iteration caps and 8020 or 12030 evaluations; declared objective gap below 1e-4 and cross-evaluation gap below 1e-10.

- [Retained qualification evidence: docs/report/method-certification/optimizer-solution-quality/report.json](report.json) (SHA-256 `62da8c5e4af32da8feeb297c1fc63d1a02e1c19c5d765cd8fab5ccbd71584aba`).

- [Retained qualification evidence: docs/report/method-certification/optimizer-solution-quality/cases.json](cases.json) (SHA-256 `747c5f5535c0a6dedfc93723b13383312a4204e11332f56e3f4c641f619d2af7`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

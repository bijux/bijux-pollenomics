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

The retained [current-source execution capsule](https://github.com/bijux/bijux-pollenomics/blob/main/data/method-certification/controlled-lra-numerical-source-capture/capture.json) records a separate genuine three-stage certification at source commit `60bf419979bdc682ef227fb01e42a4f5ed6e2722`, followed by metadata retention at `d027effd6c0ac91512cd586c3a51db987ea46d54`. Both maintained numerical replays and the independent observer returned zero. The capsule retains all eleven raw products, complete original first-party source and controls, both same-process namespace/DLL observations and every original input identity. The original source functions, case arrays and prospective tolerances were unchanged. Nine published products are byte-identical to their earlier accounts; the two report JSON products differ only in independently enumerated executed input-path identities. The older missing execution proofs are not recovered or relabelled. Runtime binaries are not redistributed; executing again requires a separately qualified runtime.

The fresh controlled certification evaluated all three objectives and both cross-candidates. The declared `1e-4` objective-gap and `1e-10` cross-evaluation criteria passed. The R 400-iteration cap remains an attained-objective observation and supplies no convergence certificate; ambiguous fitted coordinates are not uniquely identified.



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** Three declared objective surfaces compare retained RcppDE and bounded Python candidates by actual objective and cross-evaluation gaps, with separate handling of nonunique minimizing vectors.

**Unsupported claim.** Small objective gaps do not prove parameter identifiability, unique vector recovery, calibrated confidence, convergence of the R run, paper reproduction or ecological accuracy.

**Actual verification performed.** A separately retained current-source certification executed the unchanged three-case Python and native-R replays plus an independent observer at source commit 60bf419979bdc682ef227fb01e42a4f5ed6e2722. All three native stages returned zero; exact objectives, common-candidate evaluations, prospective thresholds, original inputs and same-process namespace/DLL observations were retained. This reading qualification does not establish ecological or human scientific acceptance.

**Remaining input or review.** The named current-source numerical replay is retained separately from absent historical execution proofs. An applied scientific objective still needs identifiable parameters, justified observation/model assumptions and independent scientific review. Re-execution requires newly qualified runtime bytes rather than inferred availability.

**Cause category.** Bounded numerical objective correspondence with nonunique solutions and iteration limits.

**Consequence.** Objective agreement can support the named mathematical comparison even when coordinates differ; reaching a fixed iteration cap supplies no convergence certificate.

**Precise next acceptance route.** Use the retained three-case certification within its exact source/input/runtime epoch; require a justified applied case and independent review before interpreting fitted physical parameters. Preserve the nonunique-vector and R iteration-cap limitations.

**Negative or refused result.** The R comparator reaches its 400-iteration cap. Ambiguous/nonunique vectors remain acceptable only under the stated objective-gap criterion, not as evidence of unique recovered parameters.

**Matched denominator.** Three objective cases; Python 29–40 iterations and 600–1230 evaluations, R 400-iteration caps and 8020 or 12030 evaluations; declared objective gap below 1e-4 and cross-evaluation gap below 1e-10.

Qualified authored reader SHA-256: `87e35292891330c5d3a9ca40d5402ab6c17c403ab32579748998e9c0f9726200`.

- [Retained qualification evidence: docs/report/method-certification/optimizer-solution-quality/report.json](report.json) (SHA-256 `eb473519e413849339ae4080cb2346f66426d5d7823ae67399778fbb5883a0f1`).

- [Retained qualification evidence: docs/report/method-certification/optimizer-solution-quality/cases.json](cases.json) (SHA-256 `747c5f5535c0a6dedfc93723b13383312a4204e11332f56e3f4c641f619d2af7`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

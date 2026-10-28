# Why our analytical LOVE folds refused prediction

We asked whether the author-prepared English pollen cohort could support a
whole-site held-out LRA prediction under a source-bound analytical profile. We
selected the 1250–1750 cal BP window, 31 prepared taxa and 15 positive-count
sites: 20,732 pollen counts. EXEBRID and WHH11 had zero counts in this window
and did not enter the folds. The private author-source capsule is authenticated
by its 193-file manifest. The author-prepared lake radii, PPE means, diagonal
PPE variances and fall speeds supplied the numeric inputs. We declared circular
basins and homogeneous terrestrial annuli as modeling assumptions; they are
not verified historical landscapes. The host does not consume off-diagonal
PPE covariance for this request.

We ran 15 whole-site folds, requesting three fixed pollen baselines per fold.
All 195 training items completed, with 168 cache hits and 27 unique numerical
products. **All 15 folds refused `invalid_composition`**, so we published no
held-out prediction or score. Each of the 54 local-cover ring rows had at
least one negative taxon fraction; 19 also had a value above one. The range
was -5.06615 to 7.11987. Although the fractions sum to one numerically, they
are not valid vegetation compositions. We retained the raw results rather
than clipping or renormalizing them.

We independently replayed the analytical LOVE local equation from each saved
product's pollen counts, PPE, regional cover and kernel tables. All 54 rows
agree within 2.67e-15 absolute difference. In 42 rows, 134 taxon cells have
zero local pollen and a positive regional correction; subtracting that
correction necessarily makes their analytical estimate negative. The other
12 rows also contain negative estimates under the same equation. This checks
the saved arithmetic. It does not validate the historical basin assumptions
or every upstream kernel against original R. Our [bounded original-R
reference](../../../docs/report/method-certification/original-r-reference/README.md)
checks the analytical implementation separately.

The source's `Filipendula` fall speed is 0.006 m/s, below the optimized
LOVE route's 0.01 m/s minimum. We kept this 31-taxon result intact. A
[separate 30-taxon optimized pilot](../../../docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md)
excluded 159 of the 20,732 source counts and refused convergence for one
selected regional/local pair. Our later [constrained 30-taxon
study](../english-lra-pollen-prediction.md) produced forward-pollen predictions
for 14 of 15 folds. The axes, method and attempted support differ, so these
runs do not rank solvers on a common target response.

The [report](report.json) binds the source, experiment and prediction
identities and records every denominator. The [fold ledger](folds.csv)
retains each refusal; the [cover diagnostic](cover-diagnostics.csv) retains
the 27 unique products' two local ring summaries and equation residuals.
The governed report, fold ledger and cover diagnostic own the result; the
older run products are not needed to interpret its refusal.

We can reproduce this outcome from the private source capsule into a fresh
`artifacts/` directory with the existing source preparation, runner and
reader:

```sh
author_source_root=/path/to/private/source/store/landclim/author-reference
job=artifacts/jobs/author-lra-development-reproduction
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_development \
  --author-source-root "$author_source_root" --output "$job/inputs"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_run \
  --inputs "$job/inputs" --cache-root "$job/cache" --output "$job/predictions"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_report \
  --inputs "$job/inputs" --predictions "$job/predictions" \
  --cache-root "$job/cache" --output "$job/summary"
```

We treat the result as a negative numerical development finding on previously
exposed English source. It supplies no vegetation accuracy, Swedish or Nordic
LRA admission, or general spatial-transfer estimate.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Analytical LOVE on the declared English author profile returns an explicit all-fold invalid-composition refusal.

**Unsupported claim.** A held-out prediction, local vegetation score or valid local cover from this analytical route.

**Actual verification performed.** Retained 15-fold products and independent equation replay are reported; index did not rerun.

**Remaining input or review.** All 15 analytical LOVE folds return invalid negative local-cover compositions; valid local cover requires an admitted constraint, basin profile and refusal-aware solver rather than clipping. Resolver: LOVE method/solver owner and qualified physical-basin reviewer Reopen when: A declared source-compatible constrained method yields valid cover on authenticated fold inputs and retains failures.

**Cause category.** algorithm/numerical|assumption

**Consequence.** Do not clip invalid fractions or convert all-fold refusal into zero error.

**Precise next acceptance route.** A declared source-compatible constrained method yields valid cover on authenticated fold inputs and retains failures. Then update reports/science/english-lra-pollen-prediction.md.

**Negative or refused result.** 15/15 folds refused invalid_composition; 54/54 local ring rows contain negative cover and 19 exceed one.

**Matched denominator.** 15 sites, 31 taxa, 20,732 counts; 195 training items completed, 168 cache hits and 27 unique products.

Retained evidence: [reports/science/english-analytical-love/report.json](report.json), [docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md](../../../docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

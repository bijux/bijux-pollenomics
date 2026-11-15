# Nonnegative analytical LOVE cover

Analytical regional subtraction can produce signed local cover. The maintained
`run_love`, `run_love_from_regional_draws`, `run_lra` and `run_lra_series`
workflows default to the explicit modeling assumption `clip-and-renormalize`:

1. Replace each negative taxon cover with zero, retaining its taxon position.
2. Divide the remaining covers by their positive sum.
3. Multiply by 100 when presenting percentages.

For example, `[70, 35, -5]` becomes `[70/105, 35/105, 0]`, or approximately
`[66.6667, 33.3333, 0]` percent. `[80, 35, -10, -5]` becomes
`[80/115, 35/115, 0, 0]`, or approximately
`[69.5652, 30.4348, 0, 0]` percent. Surviving taxa retain their relative ratios.
Values above 100 are not capped before closure.

Apply the rule separately to each replicate and supported ring before computing
means, marginal quantiles and sample standard deviations. The mean composition
therefore totals one. Marginal quantiles and standard deviations are summaries
of those adjusted draws; they are not themselves compositions and are not
renormalized. Unsupported rings remain missing. A supported nonfinite draw or
zero surviving positive mass raises an explicit numerical refusal; neither
becomes an invented composition.

The assumption is a pragmatic interpretation of otherwise impossible cover,
not a new physical equation or evidence of ecological accuracy. It changes the
estimand and uncertainty summaries. Negative raw values still identify tension
between the observations, regional correction and assumed parameters; clipping
does not establish that the affected taxon was truly absent.

`LoveResult.cover` contains adjusted fractions. `auxiliary` retains
`raw_cover_mean`, `raw_cover_q10`, `raw_cover_q90` and `raw_cover_sd` without
clipping. Outlier counts and quantile diagnostics always describe the raw
equation. With `retain_samples=True`, `samples['cover']` contains adjusted draws
and `samples['raw_cover']` contains raw draws. The writer exports these through
the existing auxiliary tables and sample archive. Manifests identify
`analytical_cover_policy`, algorithm `LOVE-analytical-clip-and-renormalize` and
compatibility mode `analytical-love-clip-and-renormalize`; result contracts
identify the same assumption and diagnostic basis.

For explicit historical source replay, set
`analytical_cover_policy='source-raw'` on `LoveConfig` or
`RegionalDrawLoveConfig`. The low-level `lov` and `LOVEr` functions always
retain source arithmetic and signed outputs. Source-compatible equations and
geometry do not imply literal source parity for adjusted cover. Historical
saved results keep the assumptions under which they were produced.

Optimized LOVE retains its existing nonnegative constrained estimator. This
cover assumption does not alter counts, PPE draws, kernels, variances, physical
source admission, historical sample identity or held-out validation criteria.

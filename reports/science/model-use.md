# How we choose and use a pollen or LRA model

We choose a method only after naming its target, cohort, taxon denominator,
score and source admission. We have a bounded English LRA development run and
four-country observed-pollen transfer studies. We have no independent
measured-vegetation accuracy result or admitted Swedish/Nordic fossil core
for LRA. We therefore do not claim a universally ideal LRA parameter set.

## Start with the scientific target

| Target question | Supported current route | What its score means |
| --- | --- | --- |
| Can another site's pollen predict target pollen? | Fixed site mean, nearest or inverse-distance-squared on a declared closed taxon axis; compare a bounded tuned candidate only within training folds. | Observed-pollen composition error on eligible withheld sites/bins. |
| Can source pollen yield a reconstructed vegetation vector? | REVEALS/LOVE only after site, chronology, basin geometry, taxon denominator, PPE and fall speeds are jointly qualified. | A numerical reconstruction with source assumptions; no accuracy score without independent vegetation. |
| Can LRA-derived vegetation predict target pollen? | Freeze an LRA-based withheld-site vegetation prediction and forward pollen before opening target counts. | Forward-pollen error on matched support, distinct from vegetation accuracy. |
| How accurate is reconstructed vegetation? | Match independent measured vegetation with site/time/taxon/spatial support. | No admitted repository score yet; the open reference need remains. |

We list current Nordic count mass and LRA source gates in our
[source/cohort account](source-cohorts.md). We kept the engine separate for the reasons in our
[distribution decision](../architecture/lra-distribution.md); installing it
alone does not admit a scientific input.

## Bounded observed-pollen model choices

In the [17-site author development search](nordic-pollen-study.md), we
selected a centered-log-ratio RBF with WGS84 distances, scale at the 0.25
positive training-distance quantile, ridge 0.1 and training-only half-count
smoothing. On 174 common scored bins its equal-site MAE is 0.017774 versus
0.018948 for inverse-distance-squared and 0.019621 for the training mean.
Its own coverage is 174/184 attempted bins versus 178/184 for inverse
distance. We treat these previously exposed English outcomes as development
evidence, not a parameter recommendation for new Nordic sites.

In our [Nordic inner-fold search](nordic-observed-pollen-selection.md), we
tested three fixed baselines and nine CLR-RBF combinations for each excluded
country. We used training-site distance quantiles 0.25, 0.50 or 0.75 and
ridge 0.001, 0.01 or 0.1. We selected by complete eligible coverage,
equal-site MAE, then Hellinger and candidate ID. We retained 40,932
candidate-bin trials and 2,439 RBF fits. Training selected IDW for Denmark,
RBF q75/ridge 0.1 for Finland and RBF q50/ridge 0.1 for Norway.

Our [frozen matched country transfer](nordic-observed-pollen-transfer.md)
shows why we do not call inner-fold selection a general improvement:

| Excluded country | Selected method | Scored sites/bins | Selected MAE | IDW MAE |
| --- | --- | ---: | ---: | ---: |
| Denmark | IDW | 1/24 | 0.033022 | 0.033022 |
| Finland | RBF q75/ridge 0.1 | 28/435 | 0.034871 | 0.034375 |
| Norway | RBF q50/ridge 0.1 | 52/1,084 | 0.033942 | 0.027012 |

Our selected Finnish and Norwegian RBF models did not beat fixed IDW on
matched target support. We keep this 16-label country response separate from
the 31-author-target [DK/FI/NO](denmark-finland-norway-author-pollen.md)
and [Swedish](sweden-author-pollen.md) fixed studies because their denominators
differ. Denmark has one physical target site. We treat all these comparisons
as development evidence because target outcomes were previously exposed.

In our [Swedish training-scope study](sweden-training-scope.md), we held out
each of three Swedish sites and compared the other two Swedish sites with those
same two plus 81 DK/FI/NO sites. On 39 bins shared by both scopes, IDW
equal-site observed-pollen MAE is 0.032846 versus 0.023226, respectively.
Sweden-only training refused 15 of 54 candidate bins; four-country training
predicted all 54. Most of the gain comes from one site and the outcomes were
previously exposed. We do not use this comparison to select LRA parameters
or claim independent spatial skill.

In our [Swedish support sensitivity](sweden-spatiotemporal-sensitivity.md),
removing source centers within 100 km raised IDW equal-site pollen
MAE from 0.023151 to 0.029171 on 52 matched site-bins. One-bin nominal age
shifts and a nearest-five cap had smaller, site-dependent effects. We treat
these as development probes on three exposed sites, not LRA transport or
age-model parameter estimates.

Two separately scored Swedish lakes reuse the same frozen 84-site training
profile and exact 16-label response. At [Sämbosjön](sambosjon-direct-pollen.md),
the fixed inverse-distance-squared method has the lowest equal-bin MAE
(0.022991). At [Lilla Gloppsjön](lilla-gloppsjon-direct-pollen.md), the
training mean has lower MAE (0.016272) than the prespecified
inverse-distance-squared method (0.017295), while nearest site has the lowest
Hellinger distance (0.228724). The closed labels cover different shares of
each lake's native pollen counts, and earlier source-validation exposure
limits independence. We retain the fixed methods and report all three;
these two sites do not justify retuning or a universal preferred method.

## The real English LRA profile

In our [constrained LOVE study](english-lra-pollen-prediction.md), we used the
1250–1750 BP author window, published PPE and fall speeds, declared
homogeneous author-example basin/ring assumptions and a 30-target closed
pollen composition. We excluded 159 of 20,732 source NISP assigned to
`Filipendula` because its published fall speed lies outside the selected
optimized transport contract. Those counts are retained as excluded mass.

We used one uniform-start SLSQP local LOVE search with nonnegative cover
fractions summing to one. We set limits of 300 iterations, 16,000 objective
evaluations and objective tolerance `1e-8`, with no convergence waiver. After
an initial 120-iteration development failure, this profile completed 192/195
training items. Three still refused at 300 iterations and in a bounded
600-iteration check. We published 42 forward-pollen predictions from 14 of
15 outer folds; BECKHAM refused. The original author-R optimizer differs,
and our [differential-evolution source diagnostic](../../docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md)
also refused its selected pair. We do not turn an unconverged finite
candidate into a successful product.

On the 14 paired English sites and 30 taxa, we found lower site-macro MAE
and Hellinger distance for all three fixed **direct pollen** methods than
their LRA forward-pollen counterparts. Our [matched result and omitted-site
sensitivity](pollen-prediction.md) retain the numbers. Direct prediction used
all 14 training pollen sites; LRA used one regional anchor and 13 local
reconstruction predictors. We retain simple direct baselines whenever we
evaluate forward-pollen skill. This result does not rank the methods by
vegetation reconstruction accuracy.

We also varied each English author lake's assumed radius by 20% in the
actual forward consumer while keeping LRA vegetation and regional cover
fixed. On the 14 scored sites, inverse-distance-squared pollen MAE was
0.021032, 0.021088 and 0.021457 at 80%, 100% and 120% of the assumed
radius. We use this [source-bound sensitivity](english-lra-pollen-prediction.md#basin-radius-in-the-forward-consumer)
to expose geometry dependence. It does not calibrate a physical radius,
refit LOVE or provide a Swedish basin input.

We retained a [two-case synthetic parameter sweep](synthetic-model-selection/README.md)
in which one altered PPE/transport combination ranked first across 12
completed development trials. Its independent truth generator and installed
REVEALS use different transport laws. We therefore treat that ranking as a
model-mismatch diagnostic, not an ideal PPE or transport choice for real
cores. The preceding [host-interface challenge](synthetic-host-challenge/README.md)
also retained an evidence-tamper refusal and source-reader checks, alongside
the transport-mismatched vegetation residual. No final test or independent
vegetation measurements were used.

We checked the [Hellman et al. southern Sweden parameter study](https://portal.research.lu.se/en/publications/effects-of-the-sampling-design-and-selection-of-parameter-values-/)
before naming any real-core PPE preference. Its published comparison found
that Danish PPEs brought REVEALS estimates closer to its compiled vegetation
than Swedish PPEs for Cereals, *Rumex acetosa/acetosella*, *Plantago
lanceolata* and *Calluna*. It also found larger error estimates with
outliers and very large estimates when only four pollen samples were used.
We will compare source-qualified PPE sets on a matched vegetation cohort when
those inputs are available. These published findings do not select a PPE for
our English author example or an unadmitted Nordic core, and they do not
turn our synthetic winner into an empirical parameter estimate.

## Conditional common cover at Bökesjön and Bussjösjön

We fitted one relative **Betula/Ulmus** composition to both cores in each of
13 matched CalBP windows, using the distinct saved response of each basin.
The [complete numerical result](pollen-reconstruction/common-cover/report.json)
retains all counts, denominators, source identities, solver diagnostics and
six later unmatched BUS windows. This is a new conditional reconstruction;
both cores enter each fit, so its likelihood describes the fitted inputs.
It supplies no withheld-site or measured-vegetation accuracy result.

For site s and taxon i, the model is
`p_si = a_si * v_i / sum_j(a_sj * v_j)`, with `a_si = PPE_i * K_si` fixed.
Integer projected grain totals weight the multinomial likelihood. The
comparison baseline is `close(sum_s count_si / a_si)`; this differs from the
previous forward study's equal-place mean of independently closed inverses.
PPE is fixed at 5.106 for Betula and 1.27 for Ulmus. Saved basin radii are
80 m and 69 m; their receiver factors, 3 m/s wind and homogeneous-annulus
scenario remain assumptions rather than qualified historical geometry.

Of 121 native samples, the original admission retains 110: BOKE excludes two
point ages; BUS excludes three point ages and six missing-panel samples.
Exactly 93 retained samples enter matched windows: 50 BOKE and 43 BUS.
The other 17 BUS samples occupy six unmatched windows and are not fitted.
The matched BOKE panel contains 11,295 original grains; excluding 1,367
Fraxinus leaves 9,928 Betula/Ulmus grains. BUS contributes 3,699 matched
panel grains. Their native all-pollen totals are 40,999 and 50,675.
Across all 19 retained BUS windows the panel total is 6,848 and native
all-pollen total 63,678. BUS Fraxinus remains unmeasured. Projection retains
original full-panel sample exclusions; it cannot admit a missing observation.

| CalBP window, older bound excluded | BOKE N | BUS N | Fitted Betula fraction | Baseline minus fitted NLL | Fitted deviance |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0–100 | 366 | 60 | 0.810568 | 0.000547 | 9.381 |
| 100–350 | 642 | 118 | 0.829380 | 0.000489 | 8.331 |
| 350–700 | 536 | 350 | 0.896471 | 0.000174 | 1.973 |
| 700–1200 | 1367 | 396 | 0.807836 | 0.000459 | 6.751 |
| 1200–1700 | 935 | 485 | 0.644580 | 0.000289 | 3.833 |
| 1700–2200 | 1288 | 352 | 0.507910 | 0.000622 | 11.855 |
| 2200–2700 | 409 | 182 | 0.579006 | 0.001049 | 16.655 |
| 2700–3200 | 675 | 241 | 0.574760 | 0.001093 | 19.197 |
| 3200–3700 | 100 | 192 | 0.504398 | 0.000764 | 11.013 |
| 3700–4200 | 241 | 261 | 0.256952 | 0.005878 | 76.537 |
| 4200–4700 | 801 | 297 | 0.407800 | 0.012296 | 170.977 |
| 4700–5200 | 1290 | 258 | 0.454898 | 0.015331 | 268.599 |
| 5200–5700 | 1278 | 507 | 0.686978 | 0.000233 | 3.165 |

All 13 fits converged under the declared score/count-balance policies.
Their NLL advantage over the pooling baseline is only 0.000174–0.015331;
the largest cover difference is 0.00280017, or 0.280017 percentage points on
this two-taxon axis. Deviance against separate saturated site proportions
ranges from 1.973 to 268.599. We retain the large discrepancies rather than
interpreting successful optimization as support for common field cover.
These descriptive deviances have no reported chi-square p-value.

The actual consumer completed at `025fe2da34ec6426c075767be512943fd1afb6d3`
with exit zero in 1.33 seconds and 67,677 output bytes. Reproduce from the
repository root with a fresh output path:

```sh
mkdir -p artifacts/science/common-cover
.venv/bin/python -B -m bijux_pollenomics_dev.essd_reproduction.common_cover.producer \
  --repository "$PWD" --output "$PWD/artifacts/science/common-cover/report.json"
```

Twenty-one focused consumer tests, configured lint/types and independent
review pass. An independent standard-library join checks all 121 native
samples, the 11 exclusions and 110 retained samples across 32 site-windows.
A 60-digit Decimal quadratic solution, independent of the Newton solver,
confirms all 13 fits and both estimators' probabilities and likelihoods.
Maximum absolute residuals are 2.89e-13 for cover, 1.13e-13 for probabilities,
1.38e-16 for per-grain NLL and 2.87e-13 for deviance, below the predeclared
1e-9, 1e-9, 1e-12 and 1e-8 bounds respectively. Raw inputs and consumed code
were stable; kernels were not recomputed.

The 93 matched samples lack raw age bounds. BUS borrows chronology controls
from other named cores; CalBP retains AD1950 as reference. Repeated windows
reuse the same two places, and pooling different samples does not establish
homogeneous binomial or multinomial trials. PPE, geometry, chronology and
count uncertainty are fixed or omitted in this point comparison. Source-use
permissions, taxonomic review, common-cover applicability and ecological
confirmation remain open. Historical REVEALS aggregation and whole vegetation
have separate contracts.

### Count-only compatibility of the two cores

The separate [count-set calculation](pollen-reconstruction/common-cover/counting-sets.json)
reuses the committed point study's counts and already-rounded responses.
It performs **zero new fits or kernel evaluations**. Each site receives a
nominal 97.5% equal-tail Clopper–Pearson pollen interval. We transform its
endpoints by `v = a_2*p / (a_1*(1-p) + a_2*p)` and intersect the two resulting
cover intervals in exact rational arithmetic. The Bonferroni union bound gives
nominal 95% two-site coverage **within each declared window**, conditional on
both binomial marginals, common cover and the fixed responses. Independence
across the two sites is not required. The exact binary64 confidence budget
and directed tail certificates remain in the result.

**Seven windows have empty intersections:** 1700–2200, 2200–2700,
2700–3200, 3200–3700, 3700–4200, 4200–4700 and 4700–5200 CalBP.
Their exact inverted limits remain recorded; physical cover bounds are null.
The other six are below, rounded to six decimals for reading. The numerical
result retains exact fractions and outward machine bounds.

| CalBP window, older bound excluded | Betula lower | Betula upper | Contains joint point estimate |
| --- | ---: | ---: | --- |
| 0–100 | 0.768394 | 0.784443 | no |
| 100–350 | 0.797179 | 0.817926 | no |
| 350–700 | 0.850147 | 0.933004 | yes |
| 700–1200 | 0.786788 | 0.810670 | yes |
| 1200–1700 | 0.618439 | 0.673423 | yes |
| 5200–5700 | 0.657591 | 0.713859 | yes |

The first two nonempty sets exclude the joint MLE. This intersection of
marginal count constraints does not require MLE containment. Neither empty
sets nor excluded estimates are clipped, shifted or replaced with a midpoint.
The results expose conditional incompatibility; they do not identify whether
chronology, geometry, shared-cover assumptions or sampling caused it.

The count consumer completed at `d6c7b9de1` with exit zero in 1.72 seconds,
retaining 13 computed sets and all six unmatched windows in 108,286 bytes.
Its point inputs executed at `025fe2da3` and were published at `9f63efe47`;
these revisions remain separate in the result. Reproduce with a fresh output:

```sh
mkdir -p artifacts/science/common-cover-counting
.venv/bin/python -B -m bijux_pollenomics_dev.essd_reproduction.common_cover.counting \
  --repository "$PWD" --output "$PWD/artifacts/science/common-cover-counting/report.json"
```

The mathematical contract passes 42 focused tests, including exact small-count
coverage over 45 independent example scenarios and 405 count allocations.
The consumer passes 19 focused tests; both pass configured lint/types and
independent review. A separate standard-library check confirms all 26 exact
site inverses, 13 intersections, outward bounds and endpoint-attaining sites.
Independent 110-digit positive-term binomial summation confirms all 52 stored
tail inequalities; the smallest target-minus-tail margin is 5.74e-18. Source
inputs and consumed code remained stable, and the point fits were not repeated.

These are thirteen separate conditional confidence sets, not a simultaneous
95% band across the study, posterior or predictive intervals. Pooling the
native samples does not establish binomial sampling calibration. PPE,
chronology, geometry, within-bin variation, between-site heterogeneity and
model uncertainty remain omitted. The seven empty sets do not qualify a field
rejection, and the six nonempty sets do not admit common historical cover,
source rights or ecological accuracy.

## Uncertainty and refusal rules

In our [fixed-site covariance example](../../docs/report/method-certification/fixed-site-covariance/README.md),
we propagated conditional counting and full shared-PPE covariance in a
synthetic two-basin profile. We added site resampling in
[2,048 joint draws](../../docs/report/method-certification/joint-site-draws/README.md).
We do not call this a Nordic population interval: the example has only two
sites and fixes chronology, basin geometry and transport. We retain separate
method names for historical source-R parity and corrected conditional
uncertainty.

For a new real request, we use the host's
[`validate-lra-input` and `run-lra` contract](../../docs/public/pollenomics/interfaces/cli-surface.md)
only after recording the source release and actual physical core, selected
age model, bin/window, geometry and measurement units, taxon mask, count
denominator, PPE/fall-speed version, rights and target-exclusion rule. We
install the separate engine through the optional package extra described in
our [distribution decision](../architecture/lra-distribution.md). We keep
no-support bins, missing measurement masks and nonconvergent optimizations
as explicit refusals. We freeze predictions before outcome access, score
every eligible or refused fold, and report site/country/taxon support beside
the metric. For the Swedish ABB candidate, our research-needs
register names the fields still preventing LRA use.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Current method-use rules distinguish observed pollen, modeled cover and independent vegetation targets. A separate fixed-response common-cover comparison accounts for 13 fitted BOKE/BUS windows and six unmatched windows on an explicitly projected Betula/Ulmus axis. A distinct per-window conditional count calculation retains six nonempty and seven empty two-site common-cover sets.

**Unsupported claim.** A universal LRA parameter winner or Nordic measured-vegetation accuracy.

**Actual verification performed.** Retained studies are synthesized. The distinct common-cover consumer ran at 025fe2da3 with exit 0 in 1.33 s; all 13 fits converged. Twenty-one focused tests, lint/types and independent review pass. Independent native joins confirm 121 samples, 11 exclusions and 110 retained samples; 60-digit quadratic arithmetic confirms cover, probabilities, per-grain NLL and deviance with maximum residuals 2.89e-13, 1.13e-13, 1.38e-16 and 2.87e-13 at frozen 1e-9, 1e-9, 1e-12 and 1e-8 bounds. The count-only consumer ran at d6c7b9de1 with exit 0 in 1.72 s, without refitting. Its mathematical contract passes 42 cases and its consumer 19; lint/types and independent review pass. Independent rational arithmetic confirms 26 site inverses and 13 intersections; 110-digit positive-term sums confirm all 52 binomial tail inequalities, with minimum target margin 5.74e-18.

**Remaining input or review.** No admitted Nordic LRA core or measured-cover pair supports ecological ranking; available scores use different pollen axes, exposed cohorts and conditional basin/transport assumptions. Resolver: Core/reference owners and qualified landscape/palynology reviewer Reopen when: A same-site/time/taxon LRA input and independent reference plus a newly frozen cohort support declared model comparison.

**Cause category.** data|assumption|comparability|qualified review

**Consequence.** Keep direct-pollen and LRA-forward baselines, refusals and source assumptions visible in any new comparison.

**Precise next acceptance route.** A same-site/time/taxon LRA input and independent reference plus a newly frozen cohort support declared model comparison. Record the accepted evidence in this scientific account.

**Negative or refused result.** Zero admitted Nordic LRA cores and zero independent Nordic measured-cover pairs in current scope. Six unmatched BUS windows remain. Conditional fitted deviance reaches 268.599; the objective gain over geometry-correct-then-pool is only 0.000174–0.015331, without out-of-sample interpretation. Seven count-set intersections are empty. The first two nonempty sets exclude the joint MLE; both outcomes remain explicit.

**Matched denominator.** English 15 outer source sites versus Nordic country/lake pollen cohorts on separate 30, 31 and 16-taxon axes. Separate common-cover study: 13 windows, two distinct places, 93 matched samples and 13,627 projected grains; 17 other retained BUS samples in six unmatched windows. Original full-panel exclusions and 1,367 discarded Fraxinus grains remain explicit. Count sets use the same 13 windows and 26 site count rows; nominal 95% coverage applies per window under the declared binomial marginals, without a simultaneous 13-window claim.

Retained evidence: [reports/science/pollen-prediction.md](pollen-prediction.md), [reports/science/vegetation-reference.md](vegetation-reference.md), [reports/science/pollen-reconstruction/common-cover/report.json](pollen-reconstruction/common-cover/report.json), [reports/science/pollen-reconstruction/common-cover/counting-sets.json](pollen-reconstruction/common-cover/counting-sets.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

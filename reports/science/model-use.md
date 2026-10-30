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

## Retaining measured Fraxinus with different site panels

A separate [analytical three-/two-taxon result](pollen-reconstruction/common-cover/measured-panels.json)
retains BOKE's measured **Betula/Fraxinus/Ulmus** panel while conditioning BUS
on its measured **Betula/Ulmus** panel. BUS Fraxinus remains unmeasured and its
predicted cell is null. We retain 1,367 BOKE Fraxinus grains in this new
estimand: 14,994 measured grains instead of the projected 13,627, from the same
93 matched samples and 13 windows. The original two-taxon result is unchanged.

Let `r` be the existing fitted Betula share of Betula plus Ulmus cover and
`A = a_B*r + a_U*(1-r)` for BOKE. With its measured Fraxinus count `n_F` and
Betula/Ulmus total `n_BU`, set `s = (n_F/n_BU)*A/a_F`. The relative cover on
Betula/Fraxinus/Ulmus is `(r, s, 1-r)/(1+s)`. The original saved Fraxinus
response is `a_F = 1.044 * 0.3099666306428735 = 0.32360516239115994`.
Its literal fall speed is 0.022 m/s and PPE SD is 0.048; those source values
are retained, and their uncertainty is not propagated. No new kernel is run.

The BOKE likelihood factors into its conditional Betula/Ulmus term and a
Fraxinus-versus-remainder binomial. The free Fraxinus coordinate maximizes the
second term at its empirical proportion for every `r`. Consequently the
profiled ratio and deviance remain the existing two-taxon result. Adding the
grains does not improve that cross-site fit or provide independent Fraxinus
confirmation: BOKE is the only measured Fraxinus source. Its conditional
three-taxon cover ranges from 0.089022 to 0.441264 across these windows.
Full raw NLL and its per-grain mean use the larger denominator; comparing them
with the projected NLL as an improvement would compare different outcomes.

The actual consumer completed at `1749da7f8` with exit zero in 1.55 seconds
and 63,011 bytes: 13 analytical coordinate estimates reusing the original
13 Betula/Ulmus fits, with zero new optimizer, kernel or count-tail runs.
Reproduce with a fresh output path:

```sh
mkdir -p artifacts/science/common-cover-measured-panels
.venv/bin/python -B -m bijux_pollenomics_dev.essd_reproduction.common_cover.measured_panels \
  --repository "$PWD" --output "$PWD/artifacts/science/common-cover-measured-panels/report.json"
```

Forty-four focused source, domain, mathematical and CLI tests pass, with
configured lint/types. Independent 70-digit Decimal arithmetic solves the
original Betula/Ulmus quadratic, derives all three coordinates and evaluates
both measured panels' full multinomial likelihoods. Maximum cover,
probability, per-grain NLL and deviance differences are 2.15e-13, 1.13e-13,
1.13e-16 and 7.01e-13, below the predeclared 1e-9, 1e-9, 1e-12 and 1e-8
bounds. The full likelihood factorization agrees within 2.28e-13; raw deviance
agrees with the earlier result within 6.83e-13. Native support, original
source pins and missing BUS Fraxinus remain unchanged.

Conditioning on the measured panels assumes a suitable count/reporting model;
selective reporting or heterogeneous pooled samples are not validated here.
That analytical point calculation supplies no joint three-taxon interval;
the separate count procedure below uses newly budgeted marginals and does
not select on point-fit success or positive projected effort. Chronology,
static basins, common field cover, source rights, historical reproduction
and ecological review remain unqualified.

### Joint count regions for the measured panels

The [joint three-coordinate result](pollen-reconstruction/common-cover/measured-panel-counting-regions.json)
retains the same 93 matched samples and 14,994 measured grains, including
1,367 BOKE Fraxinus grains. BUS Fraxinus remains unmeasured, not zero.
It evaluates the original full-panel cohort directly, with **zero new fits
or kernels** and no selection on a successful point fit or positive
Betula/Ulmus subtotal. All six unmatched windows retain their 17 BUS samples.

Three equal-tail Clopper–Pearson marginals constrain each composition:
BOKE Betula conditional on Betula+Ulmus, BOKE Fraxinus versus its measured
remainder, and BUS Betula conditional on Betula+Ulmus. For desired per-window
coverage `C`, upward binary64 rounding chooses `m >= (2+C)/3`, so the
Bonferroni lower guarantee is `3*m-2 >= C`. Here each marginal uses
`0.9833333333333334`, rather than the earlier two-marginal `0.975`.
The marginals need not be independent. Conditional BOKE coverage holds for
each random Betula+Ulmus subtotal; averaging over that subtotal preserves
the marginal guarantee. A zero subtotal contributes an uninformative
`[0,1]` conditional constraint and is retained; it is not missing data or
grounds to drop a window.

The exact joint region lies in the Betula/Fraxinus/Ulmus simplex and satisfies
all three constraints under the fixed responses. Its coordinate minima and
maxima below summarize projections of that region: **their Cartesian box is
not the joint region**. The model fixes positive Betula+Ulmus cover before
observing counts, including zero-effort or all-zero designs. Pure Fraxinus
is outside that declared nested-panel domain because BUS's conditional
probability would be undefined. A limiting coordinate bound can therefore
be unattained; all bounds in these seven actual nonempty regions are attained.
The numerical result retains exact rational corners, endpoint attainment,
outward machine bounds and all marginal tail certificates. The table is
rounded to six decimals for reading.

| CalBP window, older bound excluded | Betula coordinate range | Fraxinus coordinate range | Ulmus coordinate range |
| --- | --- | --- | --- |
| 0–100 | 0.634421–0.769137 | 0.033751–0.171940 | 0.168147–0.230238 |
| 100–350 | 0.632686–0.754541 | 0.084861–0.206764 | 0.137366–0.190064 |
| 350–700 | 0.698388–0.883475 | 0.052629–0.185382 | 0.051595–0.146802 |
| 700–1200 | 0.532716–0.621817 | 0.232328–0.326845 | 0.123923–0.166197 |
| 1200–1700 | 0.375597–0.469916 | 0.291019–0.404427 | 0.192276–0.274388 |
| 3200–3700 | 0.297554–0.459891 | 0.141827–0.433407 | 0.261977–0.411844 |
| 5200–5700 | 0.430146–0.524211 | 0.257344–0.358213 | 0.180433–0.256811 |

**Six regions remain empty:** 1700–2200, 2200–2700, 2700–3200,
3700–4200, 4200–4700 and 4700–5200 CalBP. Their physical coordinate bounds
remain null. The 3200–3700 window was empty under the earlier projected
two-marginal procedure and is now nonempty because the three-way confidence
budget widens its Betula/Ulmus marginal constraints. All 26 new shared-panel
pollen intervals enclose their earlier counterparts. No input or support
changed. This extra nonempty window is not evidence of independent Fraxinus
confirmation, model success or a precision gain. Neither empty regions nor
point estimates are repaired to force containment.

The consumer completed at `84154c94c7c1c1842c7a9b5a7b6ed5eccaebf458`
with exit zero in 1.694 seconds and 163,181 output bytes: 13 computed regions,
seven nonempty and six empty, reusing nine original scientific input pins.
Reproduce from the repository root with a fresh output path:

```sh
mkdir -p artifacts/science/measured-panel-counting
.venv/bin/python -B -m bijux_pollenomics_dev.essd_reproduction.common_cover.measured_panel_counting \
  --repository "$PWD" --output "$PWD/artifacts/science/measured-panel-counting/report.json"
```

The mathematical contract passes 37 focused checks; the consumer and its
dependencies pass 115 checks, comprising 24 new and 91 existing cases, with
configured lint/types. Independent 110-digit Decimal sums confirm all 78
binomial tail inequalities; the smallest target-minus-tail margin is
3.7120e-19. Independent exact arithmetic confirms 26 shared-panel inverses,
13 intersections and all 28 nonempty-region corners, half-spaces and extrema,
alongside native counts, ages, units, masks and literal PPE values.

These are conditional per-window count regions, not a simultaneous
13-window band, posterior, predictive interval or guarantee after model
selection. The sources remain exposed development evidence; pooling does
not establish homogeneous multinomial sampling or validate selective
reporting. PPE, saved quadrature, geometry and chronology remain fixed;
between-site heterogeneity and model uncertainty are not propagated. Empty
regions do not establish field rejection, and nonempty regions do not admit
common historical cover, whole vegetation, ecological accuracy or rights.

## Conditional common-cover count-model check

This calculation asks whether the two measured Betula/Ulmus count
panels are compatible with one common cover under their **fixed** basin
responses. It uses all 13 previously declared matched windows and retains
the six unmatched BUS windows without a two-site test. This is an exposed
development diagnostic, with no new fit, kernel, sample selection or PPE
choice. It does not replace the confidence regions above.

For site `i`, let `n_i` be the measured Betula/Ulmus subtotal, `Y_i` the
Betula count and `a_iB`, `a_iU` the original positive binary64 response
coefficients. Under independent site-binomial counts and a shared relative
cover `v`, the pollen odds are `(a_iB/a_iU) v/(1-v)`. Conditional on
`M = Y_1 + Y_2`, the unknown cover cancels. The conditional weight of
`Y_1 = k` is proportional to
`choose(n_1,k) choose(n_2,M-k) omega^k`, where
`omega = (a_1B a_2U)/(a_1U a_2B)` and
`max(0,M-n_2) <= k <= min(n_1,M)`. Binary64 coefficients are interpreted as
their exact supplied rational values; the calculation uses positive integer
weights and inclusive lower and upper tails. Its two-sided probability is
`min(1, 2 min(P(Y_1<=observed), P(Y_1>=observed)))`.

Before running the diagnostic, we fixed the descriptive thresholds at `1/20`
per window and `1/260` for a conservative 13-window Bonferroni comparison.
Exact rational comparisons determine the decisions; directed decimal bounds
serve only as readable probability displays. The second threshold controls
the probability of any rejection under the joint null without requiring
independence across windows. A singleton conditional support is uninformative.
Zero effort is retained explicitly; no missing count becomes zero. The
consumer refuses inputs outside its declared count and integer-work bounds.

This conditional law additionally assumes independence **between** sites,
unlike the earlier Bonferroni confidence-region construction. Pooled samples
are not established homogeneous independent binomial trials, and the same
cores and previous outcomes have already been inspected. A small probability
would therefore identify tension in this conditional model, not prove that
historical field cover differs. A large probability cannot validate the
model. BOKE Fraxinus remains outside this two-taxon diagnostic; BUS Fraxinus
remains unmeasured. Geometry, chronology, PPE, within-window heterogeneity,
and sampling calibration remain unresolved or fixed. No vegetation accuracy,
historical reproduction, source permission or untouched confirmation follows.

The [complete 19-row result](pollen-reconstruction/common-cover/conditional-adequacy.csv)
retains 13 computed comparisons and six unmatched BUS windows. The matched
sample and grain population is unchanged: 93 samples and 13,627 measured
Betula/Ulmus grains; the 1,367 BOKE Fraxinus grains remain listed separately.
All probabilities below refer to the conditional model just defined.

| CalBP window, older bound excluded | Two-sided probability, rounded | At or below `1/260` |
| --- | ---: | --- |
| 0–100 | 0.00432432 | no |
| 100–350 | 0.00657239 | no |
| 350–700 | 0.234707 | no |
| 700–1200 | 0.0126899 | no |
| 1200–1700 | 0.0640615 | no |
| 1700–2200 | 0.000832144 | yes |
| 2200–2700 | 0.0000950597 | yes |
| 2700–3200 | 0.0000233560 | yes |
| 3200–3700 | 0.00187546 | yes |
| 3700–4200 | 5.26836e-18 | yes |
| 4200–4700 | 1.19468e-38 | yes |
| 4700–5200 | 7.16784e-60 | yes |
| 5200–5700 | 0.0895485 | no |

Ten conditional probabilities are at or below the per-window `1/20`
threshold; seven are also at or below the conservative `1/260` threshold.
The other three probabilities are not evidence
that the model is valid. These comparisons qualify the large descriptive
deviances above under a specified sampling law, while leaving its field
applicability unresolved. No empty confidence region, point estimate or
previous refusal was replaced.

The consumer completed at `0ddc47d1cf59576b3c7c65976c71e5f3053751be`
with exit zero in 1.915 seconds and 7,435 output bytes. Source and input
checks passed; the worktree and HEAD stayed unchanged. Forty-one focused
tests, configured lint/types and independent mathematical review passed
before the calculation. No point fits or kernels were evaluated.

A separate standard-library calculation formed all 1,648 combinatorial
weights directly, without the production recurrence. It confirmed all 39
probabilities inside their 78 directed bounds and all 26 exact threshold
decisions, alongside the 19 source-row joins, response values, counts,
denominators and missingness. The observer completed in 0.407 seconds. This
checks arithmetic against the same published inputs, rather than supplying
independent field observations or validating their sampling design.

The maintained [conditional-count consumer](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/common_cover/conditional_adequacy.py)
reads the existing authenticated count cohort and writes one bounded CSV.
Run it from the repository root with an absent output path:

```sh
mkdir -p artifacts/science/common-cover-conditional-adequacy
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m \
  bijux_pollenomics_dev.essd_reproduction.common_cover.conditional_adequacy \
  --repository "$PWD" \
  --output "$PWD/artifacts/science/common-cover-conditional-adequacy/result.csv"
```

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


## Within-site pooling: conditional diagnostic

The predeclared diagnostic examined whether the **original samples within each
site/window** were compatible with one pollen-probability vector before pooling.
It addressed within-site sample variation, separately from the between-site
fixed-response test above. The fixed frame retained all 32 original site/windows
and 110 samples: 13 BOKE windows and 19 BUS windows, including the six BUS
windows without a BOKE counterpart.
Original chronology selection, native sample order, support, exclusions and
window boundaries remain unchanged. This is exposed scientific development,
not untouched field confirmation.

The input is each sample's full measured native NISP panel: Betula, Fraxinus and
Ulmus at BOKE; Betula and Ulmus at BUS. BUS Fraxinus remains **unmeasured**, not
zero. Source-null, missing or malformed counts refuse; explicit zeros remain
zeros. No point-fit success, positive projected Betula/Ulmus subtotal, response
parameter, PPE, kernel or reconstruction selects a sample or window.

**Twelve windows met the prespecified 32-window family threshold**, six at each
core. Sixteen Monte Carlo rank p-values were at or below 1/20; twelve were at or
below 1/640. All 32 windows remained in the family, including the six unmatched
BUS windows. The [complete numerical CSV](pollen-reconstruction/common-cover/within-site-homogeneity.csv)
retains all results, sample counts, exact statistics, simulation counts and
simulation-tail intervals.

| Core | Native samples | Measured panel grains | Windows at or below 1/640 |
| --- | ---: | ---: | ---: |
| BOKE | 50 | 11,295 | 6 of 13 |
| BUS | 60 | 6,848 | 6 of 19 |
| Total | 110 | 18,143 | 12 of 32 |

Thirty windows were computed; two had only one positive-effort sample and
remained **uninformative**, with p=1 and no simulation: BOKE 3200–3700 and BUS
8200–8700 CalBP, older endpoints excluded. These are not confirmations of
homogeneity. No window was refused. BOKE's panel retained all 1,367 Fraxinus
grains; BUS Fraxinus remained missing rather than being assigned zero.

The results challenge the joint independent, homogeneous multinomial model for
pooling these samples. They cannot isolate changing composition from clustered
grains, preparation effects, chronology or time averaging. Nonrejection does not
certify pooling, independent trials or calibrated field uncertainty. The earlier
pooled confidence regions remain conditional results; this diagnostic does not
repair or replace them, select a chronology, or establish vegetation accuracy.

The null assumes independent multinomial sample rows with a common
within-window pollen-probability vector. Conditioning on sample efforts and
taxon totals removes that vector. Feasible tables have probabilities
proportional to the reciprocal product of cell factorials; they are not sampled
uniformly. The sampler draws successive rows without replacement using
NumPy's [multivariate hypergeometric `marginals` method](https://numpy.org/doc/2.4/reference/random/generated/numpy.random.Generator.multivariate_hypergeometric.html),
with the final row fixed by the remaining margins.

Pearson's statistic is ordered using integers. For positive row totals `r_i`
and column totals `c_j`, let `D = lcm(r_i*c_j)` and
`T = sum(n_ij**2 * D/(r_i*c_j))`. For `N` grains, Pearson's value is
`N*T/D - N`; comparisons of `T` are exact, including ties. Zero rows and columns
remain in the source accounting and contribute no arithmetic term. Zero total
effort, one positive sample or one positive taxon is uninformative, with p=1
and no simulation; these outcomes are retained.

For every informative table, the pre-outcome protocol fixed **9,999 draws**,
PCG64, and seed `846291731 + index`, with index starting at zero in
core-name/window order.
The shared environment used NumPy 2.4.6; the result records its actual version
and seed. There was no outcome-based seed choice, extra simulation or retry.
The inclusive extreme count `b` gives the plus-one Monte Carlo rank p-value
`(1+b)/10000`, whose smallest positive value is 0.0001. An extreme count of zero
was reported as p=0.0001, never as zero. This is a
[Monte Carlo test](https://docs.scipy.org/doc/scipy-1.16.2/reference/generated/scipy.stats.monte_carlo_test.html),
not enumeration of the exact conditional tail. Decisions use the exact rank
fraction at 1/20 and the prespecified 32-window Bonferroni threshold 1/640.
Bonferroni needs no independence between windows.

A separate per-window 99% Clopper-Pearson interval, computed with the existing
tail-certified binomial helper from `b` successes in 9,999 simulations, describes
**simulation uncertainty in the conditional tail probability**. It is not an
interval for the plus-one rank, a joint 32-window band, field pollen uncertainty
or vegetation accuracy. The model's independent grains/sample rows and common
probabilities are assumptions, not established sampling facts. Rejection can
expose a pooling limitation; nonrejection cannot establish independence,
homogeneity, chronological comparability or calibrated pooled confidence sets.

Before simulation, the consumer bounds counts at 10,000 per cell, one million
grains per table, 128 sample rows, two or three measured taxa, a 4,096-bit integer
denominator and four million simulated cell visits over the full cohort. One
shared 50-second deadline was checked during simulation and after each numerical
certificate; the run finished within its planned 60 seconds. A numerical
certificate or runtime refusal retains real completed work and withholds
p-values. The sole numerical CSV is bounded below one MiB;
no simulated tables or duplicated source matrices are retained.

The maintained consumer is
[within_site_homogeneity.py](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/common_cover/within_site_homogeneity.py).
The code and protocol were committed before outcome calculation at
`9d39f76d41cffdfb700760d0b816ec3520915df7`. The recorded invocation, expressed
from the repository root, was:

```sh
mkdir -p artifacts/science/within-site-homogeneity
.venv/bin/python -B -m bijux_pollenomics_dev.essd_reproduction.common_cover.within_site_homogeneity \
  --repository "$PWD" --output "$PWD/artifacts/science/within-site-homogeneity/comparison.csv"
```

The consumer exited zero in 6.106 seconds, producing 6,222 bytes with no new
fits or kernel evaluations. That sole CSV was moved to the maintained location
linked above; the recorded command retains its original output path. Sixty-four
focused checks, configured static checks
and independent mathematical review passed. A separate observer exited zero in
5.912 seconds: it independently rejoined all 32 windows and 110 native samples,
recomputed rational Pearson statistics, and reproduced all 299,970 draws and
threshold decisions using the **same prescribed NumPy sampler**. It also checked
the simulation-tail bounds with independent numerical calculations; the maximum
endpoint gap was about 2.22e-16 and the smallest outward tail margin was about
2.35e-19.
Source, raw inputs and Git state stayed unchanged during both runs. This is
independent join/statistic/tail verification on the same source intake, not an
independent sampler implementation or new field evidence.

## Sample-unit precision allowing dependence within samples

This calculation asks how much counting precision the original samples can
support if grains **inside a sample may be arbitrarily dependent**. It allows
different sample expectations and does not fit dispersion to the homogeneity
results above. The fixed family contains all 32 original site/windows, 110
samples and 77 measured taxon coordinates: 13 BOKE panels with three taxa and
19 BUS panels with two. All six unmatched BUS windows remain. BUS Fraxinus is
unmeasured, not zero. The cohort and its previous outcomes are development
exposed; this is neither untouched confirmation nor a correction of earlier
pooled confidence regions.

Condition on the recorded sample efforts and original windows. For taxon `j`
and positive-effort samples, let `X_ij` be its measured-panel fraction and let
`w_i = N_i / sum(N_i)`. The target is
`mu_j = sum(w_i E[X_ij | fixed efforts and window])`.
The observed estimate `sum(w_i X_ij)` equals the exact pooled count fraction,
but it is an observation rather than that expectation. Neither quantity is
vegetation cover or a common probability across samples. The assumption is
independence of sample vectors **within each window**; grain and taxon
dependence inside a sample is unrestricted. Independence between windows is
not required. Serial dependence of adjacent-depth samples remains unresolved.

The independent bounded-summand setting is described by
[Hoeffding (1963)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1963.10500830).
The weighted calculation used here has a self-contained argument. For a random
variable in `[0,1]`, the second derivative of its log moment-generating function
is the variance under an exponential tilt, at most `1/4`. Integrating twice
bounds the centered log moment by `t^2/8`. Independence of sample vectors then
gives `log E exp(t sum(w_i (X_ij - E X_ij))) <= t^2 S/8`, where
`S = sum(w_i^2)`. Optimizing the upper and lower Chernoff bounds gives
`P(abs(observed_j - mu_j) > epsilon) <= 2 exp(-2 epsilon^2 / S)`.

Before computing the new intervals, the protocol fixed `epsilon^2 >= (9/2) S` for every
coordinate. The 77-coordinate union failure bound is at most
`154 exp(-9) < 1/20`: the exact positive Taylor sum
`sum(9^k/k!, k=0..8) > 3080` proves the strict inequality. No independence
between taxa or windows is needed for this union bound. Thus the one declared
family has at least 95% conditional coverage under the sample assumptions;
there is no separate per-window tuning or outcome-selected family.

All means and weights use rational arithmetic. The radius is the smallest
multiple of `10^-12` whose square is at least `(9/2) S`, constructed using integer
square roots and checked exactly. Lower and upper coordinates are the observed
fraction minus/plus that outward radius, intersected with `[0,1]`. This clipping
uses the mathematical probability domain; it does not alter an estimate.
The full radius is retained even when it exceeds one, and full-domain bounds
are labelled explicitly. Zero-effort rows remain with zero weight; no `0/0`
fraction is invented. An all-zero-effort table refuses because its target is
undefined. Original count, mask, sample/support and work guards remain active.

The maintained consumer is
[sample_dependence_bounds.py](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/common_cover/sample_dependence_bounds.py).
The code and protocol were committed before outcome calculation at
`b39868064c2e30d869d4067e093483416a84466b`. The actual invocation was:

```sh
mkdir -p artifacts/science/sample-dependence-bounds
.venv/bin/python -B -m bijux_pollenomics_dev.essd_reproduction.common_cover.sample_dependence_bounds \
  --repository "$PWD" --output "$PWD/artifacts/science/sample-dependence-bounds/bounds.csv"
```

The [complete numerical CSV](pollen-reconstruction/common-cover/sample-dependence-bounds.csv)
retains every window, source and positive sample counts, native panel
effort, exact squared weights, full outward radius and each measured coordinate's
observed fraction and bounds. BUS Fraxinus fields stay blank. There are no fits,
kernels, simulations, new taxon decisions or duplicated source matrices. The
result is a conditional sample-unit precision sensitivity, not evidence that
samples are independent, a calibrated field interval, a postselection guarantee,
a repaired common-cover model or independent vegetation accuracy.

All **32 windows computed**, with no refusals: 110 positive-effort samples and
18,143 measured-panel counts. The simultaneous bound is very wide: **73 of 77
coordinates are `[0,1]`**, and 30 windows have full-domain bounds for every
measured coordinate. Every lower bound is zero. Only the Fraxinus and Ulmus
upper bounds in BOKE 100–350 and 700–1200 CalBP fall below one. All six unmatched
BUS windows remain, with Fraxinus blank rather than zero.

The full outward radii range from `0.892573817839` to `2.12132034356`. The inverse
effort concentration `1/S` ranges from one to about 5.6484; this describes the
recorded weights, not an estimated number of independent observations. Multiplying
the grain counts in each sample would not create additional sample units or
shrink these radii if the weights stayed unchanged. A full-domain bound means
this conservative construction supplies no restriction on that coordinate.
It does not establish that the underlying record contains no information or
variation, nor that sharper justified bounds are impossible.

The consumer exited zero in 1.558 seconds and produced the sole 5,266-byte CSV,
which was moved to the maintained location above. The recorded command retains
its original output path. There were no fits, kernel evaluations or simulations.
Twenty-seven new mathematical and consumer controls plus nine existing intake
controls passed, together with configured lint, formatting, strict typing and
independent mathematical review. A separate observer exited zero in 0.325
seconds. Using the **same shared native intake**, it independently checked all
32 joins, 110 samples, nine raw input identities, exact rational means and
weights, minimal outward grid radii and all 77 clipped coordinate bounds, with
80-digit decimal square-root checks. Source and inputs stayed unchanged during
both runs. This verifies arithmetic on the same source records; it supplies no
new field evidence or validation of sample independence.

The result is weak conditional precision under a deliberately conservative
whole-cohort bound. It does not calibrate or repair the earlier grain-based
intervals, and its heterogeneous effort-weighted expectation is a different
target from a common multinomial probability. Dependence between adjacent-depth
samples, source selection and chronological comparability remain unresolved.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Current method-use rules distinguish observed pollen, modeled cover and independent vegetation targets. A separate fixed-response common-cover comparison accounts for 13 fitted BOKE/BUS windows and six unmatched windows on an explicitly projected Betula/Ulmus axis. A distinct per-window conditional count calculation retains six nonempty and seven empty two-site common-cover sets. A declared BOKE3/BUS2 analytical profile retains all 1367 measured Fraxinus grains with BUS Fraxinus null; its profiled B/U fit and deviance remain unchanged. A separate count-only BOKE3/BUS2 procedure retains seven nonempty and six empty exact joint regions with nominal 95% conditional coverage per window, using three newly budgeted marginals and no point-fit or positive-projected-effort selection. Coordinate ranges summarize the region rather than define an independent box. An exact conditional two-site Betula/Ulmus count-model diagnostic retains all 13 matched windows and six unmatched BUS windows. Ten probabilities are at or below 1/20 and seven at or below 1/260 under the explicitly stronger independent homogeneous site-binomial model. A separate prespecified within-site conditional Monte Carlo diagnostic retains all 32 original site/windows and 110 native samples on their full measured panels. Thirty tables are informative; two one-sample windows are uninformative. Sixteen Monte Carlo rank probabilities meet 1/20 and twelve meet the fixed 32-window threshold 1/640 under the joint independent homogeneous-multinomial model. A distinct predeclared simultaneous sample-unit bound covers the fixed 77 measured coordinates across all 32 windows, conditionally on independent bounded sample vectors within each window. It allows heterogeneous sample expectations and arbitrary grain dependence within samples; 73 coordinates retain the full [0,1] domain.

**Unsupported claim.** A universal LRA parameter winner or Nordic measured-vegetation accuracy.

**Actual verification performed.** Retained studies are synthesized. The distinct common-cover consumer ran at 025fe2da3 with exit 0 in 1.33 s; all 13 fits converged. Twenty-one focused tests, lint/types and independent review pass. Independent native joins confirm 121 samples, 11 exclusions and 110 retained samples; 60-digit quadratic arithmetic confirms cover, probabilities, per-grain NLL and deviance with maximum residuals 2.89e-13, 1.13e-13, 1.38e-16 and 2.87e-13 at frozen 1e-9, 1e-9, 1e-12 and 1e-8 bounds. The count-only consumer ran at d6c7b9de1 with exit 0 in 1.72 s, without refitting. Its mathematical contract passes 42 cases and its consumer 19; lint/types and independent review pass. Independent rational arithmetic confirms 26 site inverses and 13 intersections; 110-digit positive-term sums confirm all 52 binomial tail inequalities, with minimum target margin 5.74e-18. The measured-panel consumer ran at 1749da7f8 with exit 0 in 1.55 s, 63011 bytes and 13 analytic coordinate estimates. Forty-four focused tests and configured lint/types pass. Independent Decimal70 quadratic/full likelihood checks confirm all 13 compositions, masks, count totals and deviance at the predeclared bounds; maximum cover/probability/mean-NLL/deviance gaps 2.15e-13/1.13e-13/1.13e-16/7.01e-13. The joint measured-panel count consumer ran at 84154c94c with exit 0 in 1.694 s and 163181 bytes, with zero fits or kernels. The mathematical contract passes 37 checks and the consumer/dependencies 115 (24 new, 91 existing), with configured lint/types. Independent Decimal110 sums confirm all 78 tails (minimum target margin 3.7120e-19); exact arithmetic confirms 26 inverses, 13 intersections, all 28 nonempty-region corners, half-spaces and coordinate extrema, plus native counts, ages, units, masks and literal PPE. The conditional adequacy consumer ran at 0ddc47d1c with exit 0 in 1.915357875 s, 7,435 bytes and zero fits or kernels, after 41 focused checks, static validation and independent mathematical review. A separate standard-library direct combinatorial integer observer confirms 1,648 support weights, 39 probabilities in 78 directed 40-digit bounds and 26 exact threshold decisions on all 19 joined rows; exit 0 in 0.407008 s. This is independent arithmetic on the same published input, not independent field data. The within-site diagnostic ran at committed 9d39f76d4 with exit 0 in 6.106408834 s, retaining one 6,222-byte CSV, after 64 focused mathematical/source checks, static validation and independent protocol review. An independent observer exited 0 in 5.911574458 s: manual 110-sample/32-window joins, direct Fraction Pearson statistics, all 299,970 prescribed draws and margins, exact exceedance counts/rank probabilities and 64 threshold flags agree. Independent Decimal110 positive sums and literal 0/1 boundary checks verify all 60 outward simulation-tail interval endpoints; the maximum SciPy endpoint gap is 2.22e-16 within a predeclared 5e-13 bound, minimum outward tail margin 2.3498641e-19. The source intake and NumPy PCG64/marginals stream are shared; independent checks concern joins, arithmetic and interval numerics, not new data or an independent random engine. The sample-unit consumer ran at committed b39868064 with exit 0 in 1.558369333 s, producing one 5266-byte CSV with no fits, kernels or simulations. Twenty-seven new mathematical/consumer controls and nine existing intake controls, configured static checks and independent mathematical review pass. A separate observer exited 0 in 0.3254485 s, confirming all 32 windows, 110 samples, nine raw input identities, exact rational pooled fractions and squared weights, minimal outward grid radii and all 77 coordinate bounds, with Decimal80 square-root checks. The observer shares the native intake; it verifies joins and arithmetic rather than independent data or sample independence.

**Remaining input or review.** No admitted Nordic LRA core or measured-cover pair supports ecological ranking; available scores use different pollen axes, exposed cohorts and conditional basin/transport assumptions. Resolver: Core/reference owners and qualified landscape/palynology reviewer Reopen when: A same-site/time/taxon LRA input and independent reference plus a newly frozen cohort support declared model comparison.

**Cause category.** data|assumption|comparability|qualified review

**Consequence.** Keep direct-pollen and LRA-forward baselines, refusals and source assumptions visible in any new comparison.

**Precise next acceptance route.** A same-site/time/taxon LRA input and independent reference plus a newly frozen cohort support declared model comparison. Record the accepted evidence in this scientific account.

**Negative or refused result.** Zero admitted Nordic LRA cores and zero independent Nordic measured-cover pairs in current scope. Six unmatched BUS windows remain. Conditional fitted deviance reaches 268.599; the objective gain over geometry-correct-then-pool is only 0.000174–0.015331, without out-of-sample interpretation. Seven count-set intersections are empty. The first two nonempty sets exclude the joint MLE; both outcomes remain explicit. The analytical measured-panel point profile alone adds no cross-site Fraxinus confirmation, independent accuracy or joint three-taxon uncertainty. The separate joint count calculation retains six empty regions. The 3200-3700 CalBP region becomes nonempty solely because the three-marginal budget (0.9833333333333334 rather than 0.975) widens the shared-panel constraints; all 26 new pollen intervals enclose the old ones. This is not evidence of model success, precision gain or independent Fraxinus confirmation; per-window coverage does not imply a 13-window, postselection or calibrated field guarantee. Seven conditional probabilities remain below the 13-window threshold, including 3200–3700 despite its nonempty three-marginal region. The procedures use different assumptions and error budgets; neither outcome replaces the other. No sampling calibration or physical common-cover admission follows. Twelve of 32 prespecified within-site windows cross 1/640: six BOKE and six BUS. This is tension with the joint independent homogeneous sampling model, not a diagnosis of changing composition, clustered grains, preparation effects or chronology. BOKE 3200-3700 and BUS 8200-8700 have one positive sample and remain uninformative at p=1. No table is refused or omitted. Nonrejection cannot establish homogeneity or validate pooled confidence sets. Monte Carlo ranks have minimum 0.0001; none is an enumerated zero probability. The per-window 99% intervals quantify simulation-tail uncertainty only, not field uncertainty or joint 32-window coverage. The simultaneous sample-unit bound is full-domain for 73 of 77 coordinates and all coordinates in 30 of 32 windows; every lower bound is zero. Only BOKE 100-350 and 700-1200 CalBP Fraxinus/Ulmus upper bounds are below one. All 32 windows compute without refusals. Weak precision under this conservative construction does not prove absence of information or variation, validate sample independence, calibrate field uncertainty or repair earlier pooled intervals.

**Matched denominator.** English 15 outer source sites versus Nordic country/lake pollen cohorts on separate 30, 31 and 16-taxon axes. Separate common-cover study: 13 windows, two distinct places, 93 matched samples and 13,627 projected grains; 17 other retained BUS samples in six unmatched windows. Original full-panel exclusions and 1,367 discarded Fraxinus grains remain explicit. Count sets use the same 13 windows and 26 site count rows; nominal 95% coverage applies per window under the declared binomial marginals, without a simultaneous 13-window claim. The separate BOKE3/BUS2 profile uses the same 93 matched samples and 13 windows, retaining 14994 measured grains including 1367 BOKE Fraxinus; BUS Fraxinus stays unmeasured. The joint count result reuses those 93 samples, 14994 measured grains, nine original scientific pins and all six unmatched windows/17 BUS samples. Three CP marginals use upward-rounded m with 3*m-2 >= 0.95. The positive B+U model domain is fixed even for zero-effort designs; BUS Fraxinus remains null, zero projected B+U gives an uninformative constraint, and pure Fraxinus is outside the declared domain. Conditional adequacy uses the same 93 matched samples and 13,627 Betula/Ulmus grains, retains 1,367 BOKE Fraxinus outside its tested axis and all six unmatched BUS windows with 17 samples. Original full-panel exclusions remain unchanged. Within-site testing includes all 32 original site/windows and 110 samples: BOKE 13 windows/50 samples/11,295 selected-panel grains; BUS 19 windows/60 samples/6,848 selected-panel grains. Total measured-panel N=18,143, including all 1,367 BOKE Fraxinus grains; BUS Fraxinus remains unmeasured. All six unmatched BUS windows and 17 samples remain. Thirty informative windows each use 9,999 prescribed draws; two single-sample windows receive p=1 without simulation. Repeated windows and draws are not independent field places. The sample-unit calculation retains the same 32 windows, 110 positive-effort samples and 18143 measured-panel counts: 13 BOKE three-taxon and 19 BUS two-taxon panels, including six unmatched BUS windows. One fixed 77-coordinate family uses radius squared at least (9/2) times the exact sum of squared effort weights; no independence between taxa or windows is needed. Its target is the effort-weighted expectation of measured sample fractions, allowing different sample expectations. BUS Fraxinus stays unmeasured. Full outward radii range from 0.892573817839 to 2.12132034356; inverse effort concentration ranges from 1 to about 5.6484, not an estimated independent sample size.

Retained evidence: [reports/science/pollen-prediction.md](pollen-prediction.md), [reports/science/vegetation-reference.md](vegetation-reference.md), [reports/science/pollen-reconstruction/common-cover/report.json](pollen-reconstruction/common-cover/report.json), [reports/science/pollen-reconstruction/common-cover/counting-sets.json](pollen-reconstruction/common-cover/counting-sets.json), [reports/science/pollen-reconstruction/common-cover/measured-panels.json](pollen-reconstruction/common-cover/measured-panels.json), [reports/science/pollen-reconstruction/common-cover/measured-panel-counting-regions.json](pollen-reconstruction/common-cover/measured-panel-counting-regions.json), [reports/science/pollen-reconstruction/common-cover/conditional-adequacy.csv](pollen-reconstruction/common-cover/conditional-adequacy.csv), [reports/science/pollen-reconstruction/common-cover/within-site-homogeneity.csv](pollen-reconstruction/common-cover/within-site-homogeneity.csv), [reports/science/pollen-reconstruction/common-cover/sample-dependence-bounds.csv](pollen-reconstruction/common-cover/sample-dependence-bounds.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

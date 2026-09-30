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
| How accurate is reconstructed vegetation? | Match independent measured vegetation with site/time/taxon/spatial support. | No admitted repository score yet; the [open reference need](../needed/README.md) remains. |

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
the metric. For the Swedish ABB candidate, our [research-needs
register](../needed/README.md) names the fields still preventing LRA use.

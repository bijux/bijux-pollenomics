# Choosing and using a pollen or LRA model

**Scope:** the best supported choice depends on the target, cohort, taxon
denominator, score and source admission. The current repository has a bounded
English LRA development run and four-country observed-pollen transfer studies.
It has no independent measured-vegetation accuracy result and no admitted
Swedish/Nordic fossil core for LRA. There is consequently no evidence for one
universally ideal LRA parameter set.

## Start with the scientific target

| Target question | Supported current route | What its score means |
| --- | --- | --- |
| Can another site's pollen predict target pollen? | Fixed site mean, nearest or inverse-distance-squared on a declared closed taxon axis; compare a bounded tuned candidate only within training folds. | Observed-pollen composition error on eligible withheld sites/bins. |
| Can source pollen yield a reconstructed vegetation vector? | REVEALS/LOVE only after site, chronology, basin geometry, taxon denominator, PPE and fall speeds are jointly qualified. | A numerical reconstruction with source assumptions; no accuracy score without independent vegetation. |
| Can LRA-derived vegetation predict target pollen? | Freeze an LRA-based withheld-site vegetation prediction and forward pollen before opening target counts. | Forward-pollen error on matched support, distinct from vegetation accuracy. |
| How accurate is reconstructed vegetation? | Match independent measured vegetation with site/time/taxon/spatial support. | No admitted repository score yet; the [open reference need](../needed/README.md) remains. |

The [source/cohort account](source-cohorts.md) lists current Nordic count mass
and LRA source gates. The [installed engine route](../engineering/lra-installation.md)
describes the optional package boundary; installation alone does not admit a
scientific input.

## Bounded observed-pollen model choices

The [17-site author development search](nordic-pollen-study.md)
selected a centered-log-ratio RBF with WGS84 distances, scale at the 0.25
positive training-distance quantile, ridge 0.1 and training-only half-count
smoothing. On 174 common scored bins its equal-site MAE is 0.017774 versus
0.018948 for inverse-distance-squared and 0.019621 for the training mean.
Its own coverage is 174/184 attempted bins versus 178/184 for inverse
distance. These are previously exposed English outcomes, not a parameter
recommendation for new Nordic sites.

The [Nordic inner-fold search](../../docs/report/regions/nordic/pollen-development/README.md)
tested three fixed baselines and nine CLR-RBF combinations for each excluded
country. The candidates used training-site distance quantiles 0.25, 0.50 or
0.75 and ridge 0.001, 0.01 or 0.1. They were selected by complete eligible
coverage, equal-site MAE, then Hellinger and candidate ID. It retained 40,932
candidate-bin trials and 2,439 RBF fits. Training selected IDW for Denmark,
RBF q75/ridge 0.1 for Finland and RBF q50/ridge 0.1 for Norway.

The [frozen matched country transfer](../../docs/report/regions/nordic/selected-pollen-transfer/README.md)
shows why inner-fold selection is not a general improvement claim:

| Excluded country | Selected method | Scored sites/bins | Selected MAE | IDW MAE |
| --- | --- | ---: | ---: | ---: |
| Denmark | IDW | 1/24 | 0.033022 | 0.033022 |
| Finland | RBF q75/ridge 0.1 | 28/435 | 0.034871 | 0.034375 |
| Norway | RBF q50/ridge 0.1 | 52/1,084 | 0.033942 | 0.027012 |

The Finnish and Norwegian selected RBF models did not beat the fixed IDW
baseline on matched target support. The 16-label country response in this
search differs from the separate 31-author-target [four-country fixed study](four-country-author-pollen.md);
their MAEs should not be compared as if the denominators were equal. Denmark
has one physical target site. Prior outcome exposure limits all these
comparisons to development evidence.

## The real English LRA profile

The [constrained LOVE study](../../docs/report/pollen-reconstruction/author-lra-constrained/README.md)
uses the 1250–1750 BP author window, published PPE and fall speeds, declared
homogeneous author-example basin/ring assumptions and a 30-target closed
pollen composition. It excludes 159 of 20,732 source NISP assigned to
`Filipendula` because its published fall speed lies outside the selected
optimized transport contract. Those counts are retained as excluded mass.

One uniform-start SLSQP local LOVE search enforces nonnegative cover summing
to one. The declared limits are 300 iterations, 16,000 objective evaluations
and objective tolerance `1e-8`, with no convergence waiver. After an initial
120-iteration development failure, this declared profile completed 192/195
training items. Three still refused at 300 iterations and again under a
bounded 600-iteration check. Fourteen of 15 outer folds published 42
forward-pollen predictions; the BECKHAM fold refused. The original author-R
optimizer is different, and the [separate differential-evolution source
diagnostic](../../docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md)
also refused its selected pair. Neither optimizer failure may be converted
into a successful product by taking an unconverged finite candidate.

On the 14 paired English sites and 30 taxa, all three fixed **direct pollen**
methods have lower site-macro MAE and Hellinger distance than their LRA
forward-pollen counterparts. The [matched result and omitted-site
sensitivity](pollen-prediction.md) record the numbers. The direct route uses
all 14 training pollen sites; the LRA route uses one regional anchor and 13
local reconstruction predictors. This does not establish that direct pollen
is better at reconstructing vegetation. It tells us to retain simple direct
baselines whenever forward-pollen skill is evaluated.

## Uncertainty and refusal rules

The [fixed-site covariance example](../../docs/report/method-certification/fixed-site-covariance/README.md)
propagates conditional counting and full shared-PPE covariance in a synthetic
two-basin profile. The [2,048 joint draws](../../docs/report/method-certification/joint-site-draws/README.md)
add explicit site resampling in that synthetic example. They do not certify a
Nordic population interval; chronology, basin geometry and transport remain
fixed, and the example has only two sites. Historical source-R parity and
corrected conditional uncertainty must retain separate method names.

For a new real request, use the host's
[`validate-lra-input` and `run-lra` contract](../../docs/public/pollenomics/interfaces/cli-surface.md)
only after recording the source release and actual physical core, selected
age model, bin/window, geometry and measurement units, taxon mask, count
denominator, PPE/fall-speed version, rights and target-exclusion rule. Use the
optional engine installation described above. Keep no-support bins, missing
measurement masks and nonconvergent optimizations as explicit refusals.
Freeze predictions before outcome access, score every eligible or refused
fold, and report site/country/taxon support alongside the metric. For the
Swedish ABB candidate, the [research-needs register](../needed/README.md)
shows which source fields still prevent this sequence from entering LRA.

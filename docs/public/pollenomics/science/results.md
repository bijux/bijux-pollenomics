---
title: Scientific Results and Model Use
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-10-01
---

# Results and model use

## Implementation correspondence and archive differences

The installed Python publication profile matches the independent author-R
example on [14,074 supported mean and standard-error values](../../../report/publication-replay/landclim-author-example-correspondence/README.md)
within predeclared tolerances. Maximum residuals are about 1.84e-13 for means
and 7.16e-14 for standard errors in fraction units. The [raw-to-prepared
replay](../../../report/source-relations/landclim/author-example-taxon-support/README.md)
also reproduces the 17 released example files byte for byte.

We separately ran the 2016 author REVEALS function and a pinned later
Petr Kuneš LRA source on one author 225 BP window in four site
configurations. The [source comparison](../../../report/method-certification/petrkunes-r-comparison/README.md)
retains 124 paired cover values and 124 paired standard errors that agree
at CSV precision, plus identical 1,000-draw full-grid bootstrap indices.
Our historical native profile matches the tagged R full-grid result within
declared tolerances when given those indices. This is conditional numerical
correspondence within a shared code lineage; it does not certify corrected
uncertainty or Nordic ecological accuracy.

We separately compared RcppDE and Python LOVE optimization on
[three declared shared objectives](../../../report/method-certification/optimizer-solution-quality/README.md).
Both attained objective gaps below `1e-4` from independent optima, and each
selected candidate evaluated in the other implementation within `1e-10`.
The [result rows](../../../report/method-certification/optimizer-solution-quality/summary.csv)
include a case with equally good but different vegetation vectors. This
checks bounded objective quality and arithmetic; it does not show identical
random searches, global convergence on other inputs or ecological accuracy.

For the nominated [2024 LOVEr/LOVEoptim paper](../../../report/method-certification/love-paper-correspondence/README.md),
all 30 printed fall-speed, pollen-productivity and productivity-error values
match the later packaged DISQOVER example by row position. Nine of ten taxon
labels match exactly; the paper uses `Grasses` and the package uses `Gras`.
The example does not contain the eight-site landscape, pollen and random
draws needed to rerun the paper's Figure 2 RMSE. Its reported preferred ring
range is therefore a result of that simulation, not a selected setting for
Nordic lakes. The [paper-result matrix](../../../report/pollen-reconstruction/paper-correspondence.csv)
records the input match and the unavailable output separately.

The [paper/archive comparison](../../../report/pollen-reconstruction/paper-correspondence.md)
finds a genuine difference on the one exact shared 100–350 BP window:
archived means differ from the author replay by up to 9.20 percentage points
in grid 512 and 10.55 in grid 562. Only one of 25 intervals matches exactly.
The [PFT mean-arithmetic replay](../../../report/publication-replay/landclim-pft-crosswalk/README.md)
closes the archived ISTS/TBS means but does not identify their biological
definition or standard-error aggregation. The source revision and archive
transformation remain open; the differences are not ecological accuracy
estimates.

Across all 10,500 archived grid/window mean rows, `ISTS` equals the sum of
`Corylus.avellana`, `Fraxinus` and `Quercus.deciduous` within numerical
tolerance. The paper assigns deciduous Quercus type to TBS, while this
archived output places its mean in `ISTS`. All checked aggregate standard
errors satisfy necessary component-error bounds, but the archive does not
expose the covariance needed to reproduce its aggregation. We keep the
paper/archive classification difference and the unresolved `ISTS` meaning
visible; numerical agreement does not authorize a taxon relabeling.

## HYDE as modeled context

The retained [HYDE country table](../../../report/regions/nordic/hyde-country-cropland/country-years.csv)
has 84 source-reported cropland areas for Denmark, Finland, Norway and
Sweden at seven native CE labels and three source scenarios. Selected native
ASCII grids reproduce those country totals within the declared area
tolerance. This checks internal modeled-source accounting. HYDE cropland is
neither measured vegetation nor cereal pollen, and the scenarios are not
confidence bounds. Release-specific rights, formal CRS, calendar support
and comparable class/footprint rules are still unresolved, so we have not
run or scored a no-HYDE/HYDE pollen-model comparison. The
[source review](../../pollenomics-data/sources/hyde.md) records those exact
limits.

## Direct pollen and LRA forward pollen

The [English constrained LOVE study](../../../report/pollen-reconstruction/author-lra-constrained/README.md)
uses 15 author sites in 1250–1750 BP and 30 source-bound pollen targets. It
publishes three forward-pollen predictions for each of 14 held-out sites;
one fold refuses after three training optimizations fail. The 42 predictions
were frozen before target pollen was opened. On those same 14 sites and 30
taxa, fixed direct-pollen methods have lower mean error:

| Fixed method | Direct pollen MAE | LRA forward-pollen MAE | Direct Hellinger | LRA Hellinger |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.020496 | 0.026273 | 0.282082 | 0.360671 |
| Nearest site | 0.019552 | 0.021132 | 0.255767 | 0.286001 |
| Inverse distance squared | 0.018579 | 0.021088 | 0.243673 | 0.285415 |

MAE averages fraction errors over the named taxa; Hellinger compares closed
compositions. Both are first averaged within each scored site. The
[paired MAE rows](../../../report/pollen-reconstruction/author-lra-constrained/direct-pollen/matched-scores.csv)
and [Hellinger result](../../../report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger.json)
retain the precise result identity. The direct route uses all 14 training
pollen sites; the LRA route uses one regional anchor and 13 local
reconstruction predictors. The sites and outcomes were previously explored.
This result does not compare vegetation accuracy or establish the best method
for new Nordic cores.
The [site-influence result](../../../report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger-sensitivity.json)
finds the lower direct mean Hellinger distance persists after any one scored
site is omitted. Individual sites still disagree, especially for nearest
site, where only seven of 14 favor direct. This is a descriptive sensitivity
check on previously explored examples, not a confidence interval.

We also varied the declared English author lake radii by 20% in the actual
LRA forward-pollen consumer, keeping fitted vegetation and regional cover
fixed. The [governed prediction freeze and scores](../../../report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/README.md)
cover 126 projections on the same 14 scored sites. For inverse-distance-squared
vegetation, site-macro pollen MAE is 0.021032, 0.021088 and 0.021457 at
80%, 100% and 120% of the assumed radius. This diagnoses forward transport
sensitivity on prior-exposed English examples; it neither calibrates a lake
radius nor admits Swedish basins to LRA.
On the same matched sites, our [paired direct-pollen comparison](../../../report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/paired/report.json)
finds lower aggregate direct-pollen MAE and Hellinger at all three radius
factors for each fixed method. Individual sites disagree, and direct and LRA
used different training information.

## Additional Swedish lake transfer

Three further Swedish EPD lakes were selected from site and age metadata
before their pollen counts were read. The [three-lake transfer](../../../report/regions/nordic/swedish-lake-transfer/README.md)
withheld Gilltjärnen, Lake Avegöl and Flinkasjön from the 81-site
Denmark/Finland/Norway training set. All 63 site by 500 BP bins received
three fixed 31-target pollen predictions, giving 189 matched score rows.
Inverse distance squared had the lowest three-site mean absolute fraction
error (0.017334), compared with nearest site (0.017932) and training mean
(0.020682); nearest site performed better at Lake Avegöl. These are
previously exposed development outcomes for observed pollen. They do not
admit these lakes to LRA or measure vegetation accuracy.

## Swedish training scope on matched pollen targets

The [whole-site comparison](../../../report/regions/nordic/swedish-training-scope/README.md)
holds out each of three Swedish sites. It compares the other two Swedish
sites with those same two plus 81 Denmark, Finland and Norway sites. On the
39 bins shared by both scopes, inverse-distance-squared equal-site
observed-pollen MAE is 0.032846 with Sweden-only training and 0.023226 with
four-country training. Sweden-only training refuses 15 of 54 candidate
bins; four-country training predicts all 54. The
[paired rows](../../../report/regions/nordic/swedish-training-scope/paired-scores.csv)
retain the exact common support. These three Swedish sites and their outcomes
were previously explored, and most of the mean improvement comes from one
site. The comparison does not establish independent prediction skill or LRA
vegetation accuracy.

## Swedish age and distance sensitivity

We used the same three whole-site Swedish targets to ask how observed-pollen
predictions change when training pollen comes from an adjacent nominal
500-year bin, only the nearest five source sites, or source sites at least
100 km from the target center. The
[source-bound sensitivity](../../../report/regions/nordic/swedish-support-sensitivity/README.md)
retains 486 attempted site-bin/policy queries, 473 supported predictions and
13 refusals. On 52 bins shared with the unshifted all-site reference, excluding
sites within 100 km raises inverse-distance-squared equal-site pollen MAE
from 0.023151 to 0.029171. The
[paired score rows](../../../report/regions/nordic/swedish-support-sensitivity/paired-scores.csv)
show the site and bin effects. Three previously explored sites and nominal
source-bin shifts cannot establish independent spatial skill, chronology
uncertainty, LRA accuracy or vegetation accuracy.

## Swedish chronology-block development result

We also withheld each Swedish target site and predicted its 500 BP pollen bin
using training pollen exactly 1,000 nominal BP older, excluding the target
and adjacent source bins. All 54 target bins received three frozen predictions
and matched same-bin scores, with no refusals. Inverse-distance-squared
equal-site pollen MAE changed from 0.023647 to 0.024023; nearest-site and
training-mean changes were small and in the opposite direction. The
[chronology-block report](../../../report/regions/nordic/swedish-chronology-block/README.md)
keeps the 162 paired rows and count denominators. These source-assigned bins
do not establish nonoverlap of the cores' true age distributions. This is a
prior-exposed observed-pollen development comparison, not a test of LRA or
measured vegetation.

## Abborrtjärnen with an alternative chronology

The [LegacyAge source join](../../../report/source-relations/neotoma/legacyage-chronology/README.md)
matches published age estimates to all 107 Abborrtjärnen pollen sample depths
and 71 of 72 Dalmutladdo depths. These are alternative ages; they are not the
historical LandClim age vector. In a separate
[three-site development sensitivity](../../../report/pollen-reconstruction/age-interval-sensitivity/README.md),
we admitted a sample to a 500-year bin only when its entire reported LegacyAge
95% interval fit inside that bin. Only eight Abborrtjärnen samples qualified
for four shared bins. Four fixed pollen predictors scored the same 12
site-bin targets each; inverse-distance-squared site-macro MAE changed from
0.060058 to 0.059762 on that matched subset.

The other two sites retain point ages, and the intervals do not provide a
joint age posterior. This sparse, previously exposed 16-label pollen study
does not establish a better chronology, independent accuracy or LRA inputs.

For the Norwegian Dalmutladdo core, a separate
[age-interval support check](../../../report/regions/nordic/dalmutladdo-age-interval-sensitivity/README.md)
keeps only two of 72 pollen samples: their full reported LegacyAge 95%
intervals stay inside their original 500-year bins. Four previously frozen
Norway-excluded methods provide eight predictions across those two bins;
20 previously scored bins have no eligible sample. The two samples do not
change bins, so the paired same-sample scores are identical under the
nominal and strict rules. Differences from the original full-bin scores
reflect fewer counted samples, not a new model result or LRA validation.
The separate [31-author-target analysis]
(../../../report/regions/nordic/dalmutladdo-author-target-age-interval/README.md)
reuses six frozen predictions on those two bins. Its inverse-distance-squared
two-bin MAE is 0.006445, compared with 0.006341 for the parent's full
compositions on the same bins. Those scores have a different taxon axis and
denominator from the 16-label result; the two studies cannot be pooled.

At Danish Solsø, a [primary LegacyAge depth join]
(../../../report/countries/denmark/solsoe-source-lineage/legacyage-chronology/README.md)
matches all 92 Neotoma samples across two cores. The 1981 and 1983 core
chronologies have different agreement with these alternative age intervals.
The join does not recover LandClim II's published selection of 79 samples or
its historical basin inputs.
A separate [Denmark-held-out pollen sensitivity]
(../../../report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/README.md)
retains 15 of 91 comparable samples whose full age intervals fit their
original bins. Eight of 24 scored bins and 32 frozen four-method predictions
remain supported. This is a previously exposed direct-pollen result on one
physical lake, with no new LRA or vegetation validation claim.
The distinct [31-author-target Solsø sensitivity]
(../../../report/countries/denmark/solsoe-source-lineage/author-target-age-interval/README.md)
uses author-assigned pollen counts and 24 frozen three-method predictions on
the same 15 supported samples and eight bins. Its nearest-site eight-bin MAE
is 0.025673, compared with 0.025513 on the parent's complete counts in those
bins. We do not pool that score with the 16-label result or infer independent
temporal skill from this one previously exposed lake.

## A newly scored Swedish lake

We applied three fixed observed-pollen predictors to Lake Sämbosjön, a
physical site absent from the earlier target studies. All 22 candidate
500-year bins were predicted and scored. Inverse-distance-squared equal-bin
MAE was 0.022991 on a closed 16-label pollen response containing 224,291 of
393,822 native counts (56.95%). The [governed study](../../../report/regions/nordic/sambosjon-direct-pollen/README.md)
keeps the source identity, frozen predictions, scores and count denominators.
Aggregate target count support was inspected before prediction, and aggregate
scores were inspected before a later protocol annotation correction. The
prediction bytes stayed fixed; this one-site result is descriptive development
evidence, not independent confirmation or vegetation accuracy. A separate
source age-bound screen finds that 58 of 111 sample intervals cross a nominal
500-year bin boundary, with at least one crossing in each scored bin. The
published MAE remains a point-age-bin result, not an age-uncertainty-adjusted
score.

## A second newly scored Swedish lake

At [Lilla Gloppsjön](../../../report/regions/nordic/lilla-gloppsjon-direct-pollen/README.md),
three fixed methods predicted every one of 23 nominal 500-year pollen bins
before the target counts were opened for scoring. All 69 method/bin scores
completed. On the same 16-label closed pollen response, the prespecified
inverse-distance-squared method has equal-bin MAE **0.017295** and Hellinger
distance **0.237576**. Training mean has lower MAE (0.016272), while nearest
site has lower Hellinger distance (0.228724); the method order depends on the
metric at this lake. The [research report](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/lilla-gloppsjon-direct-pollen.md)
and [score table](../../../report/regions/nordic/lilla-gloppsjon-direct-pollen/scored/scores.csv)
give the denominators and per-bin results.

Only 55,638 of 127,027 native pollen NISP counts lie on the exact 16-label
axis (43.80%). Two of 86 source samples are excluded from age-bin scores due
to negative source age bounds, with their counts retained separately. The
training source-validation screen had previously parsed this target's source
partition, so this is descriptive new-site development evidence, not an
untouched independent confirmation. It does not evaluate vegetation or LRA.

## What two lake pollen series can and cannot say

We compared observed `Alnus` and `Plantago lanceolata` pollen fractions at
Bussjösjön and Bökesjön in 13 common 500-cal-BP bins. The
[lake trajectory report](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sweden-lake-trajectory.md)
retains each site's source counts, age support and 48 taxon/threshold/interval
comparisons. Some site changes agree in direction and others contradict. A
1000-year binning and alternate nearby-site circles expose time and location
sensitivity. Giving both lakes equal weight versus pooling their pollen counts
changes 10 of 48 all-native direction classes and 9 of 48 closed-16 classes;
four comparisons in each denominator reverse between a qualified increase and
decrease. The matching count denominator is used for each composition.

Independent dated SEAD records describe nearby archaeological context, but
their feature counts are not vegetation or land-use measurements. The
LandClim model grid includes these pollen sites and cannot independently
validate them. The supported answer is a bounded description of two pollen
series; whether local land use caused their changes remains unresolved.

## Parameters and next experiments

### Measured vegetation evidence

Our [EMPD2–NFI source screen](../../../report/validation/empd2-nfi-pairing/README.md)
admits zero matched vegetation pairs for repository prediction accuracy. A
[Färskesjön plot](../../../report/vegetation-reference/farskesjon/README.md)
provides measured tree volume but is a 7 m radius plot whose source point is
427 m from the lake pollen point. [Historical Småland maps](../../../report/vegetation-reference/smaland-historical-maps/README.md)
give map coverage and shared pollen samples for three bogs, without the full
numerical vegetation fractions. A [published southern Swedish figure](../../../report/vegetation-reference/southern-sweden-figure/README.md)
supports a bounded nine-label comparison of its authors' estimates, not a
score of this repository's predictions. These source results answer different
questions; none supplies our missing independent vegetation outcome.

### Model settings

For the English LRA run, published PPE and fall speeds were fixed after a
declared one-taxon transport exclusion. A simplex-constrained LOVE fit used a
uniform-start SLSQP search, 300 iterations, 16,000 objective evaluations and
1e-8 tolerance. Three of 195 training fits failed; a bounded 600-iteration
check still refused those cases. The original author-R optimizer differs.
These settings are a reproducible development profile, not universal ideal
parameters.
The [two-case synthetic PPE and transport sweep](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/synthetic-model-selection/README.md)
completed 12 development trials and ranked one candidate first within that
set. Its independent pollen generator and installed REVEALS use different
transport laws, so the winning candidate may compensate for model mismatch.
We do not recommend its PPE or transport settings for a real core.
The repository's [model-use guide](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/model-use.md)
sets out the target-specific choices, source gates, numerical settings,
uncertainty scope and refusal conditions in one place.

One bounded author direct-pollen CLR-RBF search has lower common-support MAE
than inverse distance squared but less coverage; the
[development account](../../../report/pollen-reconstruction/README.md)
specifies its candidate set, denominator and prior exposure. Country-excluded
Nordic tuning did not establish a general advantage over the fixed IDW
baseline. A new independent cohort must be qualified and predictions frozen
before outcome inspection. Measured vegetation validation needs an admitted
reference with matching site, time, taxa and spatial support.

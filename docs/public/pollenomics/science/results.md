---
title: Scientific Results and Model Use
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-30
---

# Results and model use

## Implementation correspondence and archive differences

The installed Python publication profile matches the independent author-R
example on [14,074 supported mean and standard-error values](../../../report/publication-replay/landclim-author-example-correspondence/README.md)
within predeclared tolerances. Maximum residuals are about 1.84e-13 for means
and 7.16e-14 for standard errors in fraction units. The [raw-to-prepared
replay](../../../report/source-relations/landclim/author-example-taxon-support/README.md)
also reproduces the 17 released example files byte for byte.

The [paper/archive comparison](../../../report/pollen-reconstruction/paper-correspondence.md)
finds a genuine difference on the one exact shared 100–350 BP window:
archived means differ from the author replay by up to 9.20 percentage points
in grid 512 and 10.55 in grid 562. Only one of 25 intervals matches exactly.
The [PFT mean-arithmetic replay](../../../report/publication-replay/landclim-pft-crosswalk/README.md)
closes the archived ISTS/TBS means but does not identify their biological
definition or standard-error aggregation. The source revision and archive
transformation remain open; the differences are not ecological accuracy
estimates.

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

## Parameters and next experiments

For the English LRA run, published PPE and fall speeds were fixed after a
declared one-taxon transport exclusion. A simplex-constrained LOVE fit used a
uniform-start SLSQP search, 300 iterations, 16,000 objective evaluations and
1e-8 tolerance. Three of 195 training fits failed; a bounded 600-iteration
check still refused those cases. The original author-R optimizer differs.
These settings are a reproducible development profile, not universal ideal
parameters.
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

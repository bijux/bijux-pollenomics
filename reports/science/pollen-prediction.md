# What the current pollen prediction studies show

**Scope:** prior-exposed development results on observed pollen. These are
separate from independent vegetation accuracy and from a complete Nordic LRA
reconstruction.

## Four Nordic countries on the author taxon axis

The [four-country study](nordic-pollen-study.md)
withholds Denmark, Finland, Norway or Sweden from its corresponding training
set. It retains source counts, exclusions, predictions before outcome access,
scores and country-specific support. The response is a closed 31-author-target
pollen subcomposition; its errors cannot be compared numerically with the
separate 16-literal-label study. Denmark has one target site in the captured
cohort, and 94 Norwegian bins have no eligible prediction. The study reports
observed-pollen transfer, not a vegetation estimate. Prior outer outcomes were
already exposed, so it does not establish confirmatory country transfer skill.

## Swedish training scope on matched targets

The [Swedish training-scope comparison](sweden-training-scope.md) asks whether
adding 81 DK/FI/NO sites to two Swedish training sites changes prediction at
the third Swedish site. On 39 bins common to both scopes, three fixed methods
have 117 paired score rows. Inverse-distance-squared equal-site pollen MAE is
0.032846 with Sweden-only training and 0.023226 with four-country training.
Sweden-only has 15 support refusals among 54 candidate bins; four-country
training predicts all 54. The mean IDW advantage is concentrated in
Abborrtjärnen, and only three previously exposed Swedish sites are available.
This compares observed pollen, not LRA-derived vegetation or independent
ecological truth. It does not yet test time displacement or population-level
spatial generalization.

We then used the same four-country source-excluded folds for an
[age and distance sensitivity](sweden-spatiotemporal-sensitivity.md). Shifting
the training source by one nominal 500-year bin, capping its nearest sites at
five, and excluding source centers within 100 km yields 486 attempted
site-bin/policy queries, 473 predictions and 13 refusals. On 52 bins paired
to the unshifted all-site reference, the 100-km exclusion raises IDW equal-site
MAE from 0.023151 to 0.029171; the shift and nearest-five effects are smaller
and differ between sites. This is a three-site development sensitivity, not an
age-model uncertainty estimate or independent spatial validation.

## Matched English direct pollen and LRA forward pollen

The [constrained LOVE source study](english-lra-pollen-prediction.md)
uses 15 English author examples in one 1250–1750 BP window. The declared
30-taxon composition excludes `Filipendula` because its published fall speed
is outside the selected optimized transport contract. Whole-site training
reconstructions and regional inputs exclude the target pollen. Fourteen folds
publish predictions; the BECKHAM fold refuses because three training LOVE fits
did not converge. The 42 scored site-method rows are paired with fixed direct
observed-pollen baselines on the exact same target support.

| Method | Direct pollen MAE | LRA forward pollen MAE | Direct Hellinger | LRA Hellinger |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.020496 | 0.026273 | 0.282082 | 0.360671 |
| Nearest site | 0.019552 | 0.021132 | 0.255767 | 0.286001 |
| Inverse-distance-squared | 0.018579 | 0.021088 | 0.243673 | 0.285415 |

MAE is the mean absolute fraction error over 30 named taxa, averaged equally
across the 14 scored sites. Hellinger is the site-macro distance between two
closed compositions; smaller values favor the prediction. The
[Hellinger source rows](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger.json),
[paired MAE rows](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/matched-scores.csv)
and [site sensitivity](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/site-sensitivity.json)
retain all methods and source identities. The direct route uses all 14
training pollen sites. The LRA route uses one regional anchor and 13 local
reconstruction predictors, so their training information is not identical.
Both prediction sets were frozen before these target outcomes were scored.

The fixed direct methods have lower mean pollen error on this matched English
development support. This does not say that LRA is ecologically inferior,
that its vegetation reconstruction is inaccurate, or which method would win on
new Nordic sites. No independent vegetation observation was scored here.

The [Hellinger site-influence calculation](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/paired-hellinger-sensitivity.json)
omits each scored site in turn. The mean direct-minus-LRA Hellinger difference
stays below zero for every omission and all three methods. The nearest-site
method favors direct at only seven of 14 individual sites, however, so the
mean direction must not be read as unanimous site behavior. These correlated,
previously explored sites do not yield a sampling interval or independent
spatial confirmation.

## Model use and open inputs

The [bounded development search](nordic-pollen-study.md)
selected a CLR/WGS84 RBF-ridge candidate on one prior-exposed author comparison
and found lower common-support MAE than inverse-distance-squared with lower
prediction coverage. That candidate is best only within its declared search,
response, metric and cohort. For the English LRA run, the published PPE and
fall speeds were held fixed; the constrained SLSQP LOVE backend had three
training nonconvergences even after a higher-budget check. Neither result
identifies universal LRA parameters. Swedish/Nordic basin geometry, selected
chronology, PPE/taxon denominator decisions, independent vegetation pairs and
HYDE semantics remain open in the [research-needs register](../needed/README.md).

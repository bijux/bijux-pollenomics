# Swedish observed-pollen chronology-block development comparison

We used the three previously explored Swedish lake targets and their existing
whole-site-excluded four-country training folds. The estimand is prediction of
the closed 31-author-taxon **observed-pollen fraction** in a target 500 BP age
bin. The predictor used pollen from the source bin exactly 1,000 nominal BP
older and excluded the target and both adjacent source bins. These are
source-assigned bins, not nonoverlapping age probability distributions.

The [prepared rule](../../docs/report/regions/nordic/swedish-chronology-block/prepared/prepare.json)
and [frozen predictions](../../docs/report/regions/nordic/swedish-chronology-block/frozen/freeze.json)
preceded this run's scoring. The source cohort and methods had already been
examined in prior Swedish development work. All **54 target bins** were
attempted, eligible, predicted and scored; **zero were refused or failed**.
The sites contributed 21, 20 and 13 bins, respectively. Three fixed methods
produced 162 frozen predictions and 162 paired scores. The matched comparator
is the earlier same-bin, all-site result on the exact same targets and counts.

| Fixed method | Same-bin equal-site MAE | Older-bin equal-site MAE | Older minus same | Same-bin Hellinger | Older-bin Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: |
| Inverse distance squared | 0.023647 | 0.024023 | +0.000375 | 0.341619 | 0.342567 |
| Nearest site | 0.026940 | 0.026199 | −0.000741 | 0.393979 | 0.383523 |
| Training mean | 0.031718 | 0.030970 | −0.000748 | 0.451058 | 0.443563 |

The [machine report](../../docs/report/regions/nordic/swedish-chronology-block/report.json)
retains site-level and sample-weighted scores; the [paired rows](../../docs/report/regions/nordic/swedish-chronology-block/paired-scores.csv)
retain each target denominator. The inverse-distance-squared equal-site MAE
increased slightly, while the other two decreased slightly. Site effects have
different signs, so the pooled values do not show a consistent temporal
improvement or degradation. Sample-weighted MAE for inverse distance squared
rose from 0.022012 to 0.023075; these weights reflect retained sample density,
not independent replication.

This is one prior-exposed, nominal chronology-block observed-pollen comparison.
Different cores' calendar-age uncertainty can overlap despite separated bin
labels. We did not propagate age-model uncertainty, establish independent
confirmation, run LRA reconstruction or score measured vegetation. Three
correlated Swedish targets cannot establish Nordic temporal generalization.

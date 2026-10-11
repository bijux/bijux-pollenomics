# Lilla Gloppsjön observed-pollen transfer

We evaluated three fixed observed-pollen predictors at [Lilla
Gloppsjön](../../docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/README.md),
Neotoma/EPD site `3234`, core `4071`, dataset `4200`
([dataset DOI](https://doi.org/10.21233/vpnw-pv89)). This physical site and
its core were excluded from all 84 training sites. The [prediction
freeze](../../docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/frozen/freeze.json)
fixed 23 nominal 500-cal-BP bins and 69 predictions before target pollen
counts were read for this study. A separately committed [scoring
protocol](../../docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/scoring-protocol.json)
fixed count admission, the 16 exact source labels, equal-bin mean absolute
fraction error (MAE), Hellinger distance and refusal rules before scoring.

All 23 bins scored for all three methods. On those same bins, the [numeric
result](../../docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/scored/report.json)
is:

| Frozen method | Equal-bin pollen MAE | Equal-bin Hellinger |
| --- | ---: | ---: |
| Training mean | 0.016272 | 0.256392 |
| Nearest site | 0.020000 | 0.228724 |
| Inverse distance squared, the prespecified primary | 0.017295 | 0.237576 |

The training mean has the lowest MAE here, while nearest site has the lowest
Hellinger distance. The prespecified primary is lowest on neither metric at
this lake. These differences describe one site on a fixed response axis; we
did not use this target to choose a method. The [per-bin scores](../../docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/scored/scores.csv)
and [coverage rows](../../docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/scored/coverage.csv)
retain all 69 attempted method/bin combinations and zero refusals.

The source has 86 samples with direct pollen count rows. We assigned 84 to
comparable calibrated point ages and refused two with negative age bounds.
Across all 86 samples, the 16-label closed response contains 55,638 of
127,027 native pollen NISP counts (43.80%); 71,389 counts remain outside
that axis. The two age-refused samples retain 3,643 native and 709 closed-axis
counts separately. The [sample account](../../docs/report/regions/nordic/lilla-gloppsjon-direct-pollen/scored/sample-counts.csv)
preserves each sample's denominator. Missing labels inside a positive closed
response are zero counts on this declared subcomposition, not claims about
absence of vegetation.

The selected source age claims have younger and older bounds, but their
confidence level and joint age posterior are not established. The reported
scores use point-age bins and do not propagate chronology uncertainty. A
same-name LandClim point is nearby, yet physical identity and historical
basin geometry remain unproven; neither is borrowed for this analysis.

An earlier training-source validation screen parsed the full Neotoma
observation partitions, including this target, without selecting its rows
into training or the frozen predictions. The target compositions were first
interpreted by this scoring consumer after the freeze and scoring protocol
were committed. This is therefore a new-site descriptive development result,
not an untouched independent confirmation. It evaluates direct observed
pollen only: no LRA reconstruction, measured vegetation accuracy, or general
Swedish method ranking follows from it.

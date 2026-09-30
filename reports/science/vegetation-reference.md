# What our vegetation references can establish

## Our decision

We require an independent vegetation measurement matched to a pollen sample
in physical site, time, taxon response and spatial support before scoring a
repository prediction as vegetation accuracy. We screened the available
Swedish forest plots, historical maps and published REVEALS comparison under
that rule. None supplies an admitted pair for the predictions we produced.
The [EMPD2–NFI decision](../../docs/report/validation/empd2-nfi-pairing/report.json)
retains **zero admitted measured pairs** among 16 nearby candidates. We have
therefore not calculated a repository vegetation accuracy score.

## What we checked

| Evidence | What we established | Why it does not validate our predictions |
| --- | --- | --- |
| [Färskesjön EMPD2–NFI lead](../../docs/report/vegetation-reference/farskesjon/README.md) | A May 2013 forest plot has measured tree volume, a 7 m radius and a source point 427.122 m from the lake surface pollen point. The pollen collection note says September 2013. | A small, separated plot does not measure the lake's landscape pollen source area. Its five volume classes are not 31-taxon vegetation-cover fractions; the plot precedes the possible September sample days by 107–136 days. We refused this pair. |
| [Cui et al. historical maps](../../docs/report/vegetation-reference/smaland-historical-maps/README.md) | Three bogs have published map-coverage percentages within 3 km and one dated pollen sample per bog shared by the two modern windows. | The article and appendix do not give the full numerical class areas or distance-weighted fractions needed for an exact vegetation target. Complete modern map coverage is not a second independent pollen sample. We retain source support, not a scored pair. |
| [Published southern Swedish Figure 6](../../docs/report/vegetation-reference/southern-sweden-figure/README.md) | On nine region/taxon labels printed in all three panels, the published REVEALS estimates have mean absolute error 5.11 percentage points from the figure's observed vegetation, versus 17.33 for published raw pollen. | This is a rounded, label-selected reading of another study's two regional figures. It does not score our model, recover its 26-taxon result or provide nine independent landscapes. |

The [Färskesjön machine decision](../../docs/report/vegetation-reference/farskesjon/report.json)
retains the measured plot volume, date, distance and private-source hashes;
plot identifiers and coordinates remain private. The
[historical-map coverage rows](../../docs/report/vegetation-reference/smaland-historical-maps/coverage.json)
keep the distinct TW3 and TW4 map periods and the three shared pollen counts.
The [published-figure calculation](../../docs/report/vegetation-reference/southern-sweden-figure/report.json)
and [printed-label transcription](../../docs/report/vegetation-reference/southern-sweden-figure/printed-labels.csv)
keep the nine-label denominator visible. Their source-bound producers and
reproduction commands remain with those governed results.

## What follows

We can use these sources to explain spatial coverage, reject an unsuitable
plot, and compare values printed in the historical paper. We cannot use any
of them as an independent ecological outcome for our Nordic observed-pollen
models or English LRA forward-pollen study. The country and lake pollen scores
in this repository compare predicted pollen with observed pollen; they do not
become vegetation scores because a nearby map, plot or published validation
figure exists.

To change that decision, we need a source-owner-reviewed set of original
vegetation fractions and pollen counts, with linked physical cores, dates,
taxon mapping, landscape support and rights. The full Hellman ten-lake
source data or another independently matched cohort could meet that need.
We will freeze the benchmark and predictions before viewing its outcomes.
The [open research need](../needed/README.md) records the requested source
packet and resolver.

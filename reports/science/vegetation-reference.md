# What our vegetation references can establish

The [historical-map paper account](smaland-historical-maps-paper.md) and
[southern Swedish validation account](southern-sweden-validation-paper.md)
explain the published methods and examples before this repository's source-admission decisions. Their published results and our bounded
source checks have separate populations.

## Our decision

We require an independent vegetation measurement matched to a pollen sample
in physical site, time, taxon response and spatial support before scoring a
repository prediction as vegetation accuracy. We screened the available
Swedish forest plots, historical maps and published REVEALS comparison under
that rule. None supplies an admitted pair for the predictions we produced.
The [EMPD2–NFI decision](../../docs/report/validation/empd2-nfi-pairing/report.json)
retains **zero admitted measured pairs** among 16 nearby candidates. We have
therefore not calculated a repository vegetation accuracy score.

We separately acquired the original CC BY 4.0 [Namibian modern soil-pollen and
vegetation tables](../../docs/report/vegetation-reference/namibia-pollen-vegetation/README.md)
from PANGAEA. Their source-bound join contains ten pollen sites and 150
site-radius vegetation rows, yielding 750 five-taxon pairs. These are actual
published observations, but their soil samples, savanna taxa, calculated
vegetation areas and unspecified sample/image dates do not match any Nordic
lake prediction. Repeated radius rows are not independent pollen samples.
We retain the joined rows as an out-of-domain development source without a
model score or a selected pollen-source radius. We then compared the conditional
five-taxon pollen and vegetation compositions at each of the publisher's 15
radius labels. The [site-level descriptive distances](../../docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.csv)
retain ten sites per label; their mean Hellinger distances are **0.3664** at
100 m, **0.3427** at 400 m and **0.3777** at 1,500 m. The
[source-bound calculation](../../docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json)
does not determine whether the publisher's areas describe rings or cumulative
disks and does not choose a pollen-source radius. It compares two observed
subcompositions; it is not a model prediction score.

## What we checked

| Evidence | What we established | Why it does not validate our predictions |
| --- | --- | --- |
| [Färskesjön EMPD2–NFI lead](../../docs/report/vegetation-reference/farskesjon/README.md) | A May 2013 forest plot has measured tree volume, a 7 m radius and a source point 427.122 m from the lake surface pollen point. The pollen collection note says September 2013. | A small, separated plot does not measure the lake's landscape pollen source area. Its five volume classes are not 31-taxon vegetation-cover fractions; the plot precedes the possible September sample days by 107–136 days. We refused this pair. |
| [Cui et al. historical maps](../../docs/report/vegetation-reference/smaland-historical-maps/README.md) | Three bogs have published map-coverage percentages within 3 km and one dated pollen sample per bog shared by the two modern windows. | The article and appendix do not give the full numerical class areas or distance-weighted fractions needed for an exact vegetation target. Complete modern map coverage is not a second independent pollen sample. We retain source support, not a scored pair. |
| [Published southern Swedish Figure 6](../../docs/report/vegetation-reference/southern-sweden-figure/README.md) | On nine region/taxon labels printed in all three panels, the published REVEALS estimates have mean absolute error 5.11 percentage points from the figure's observed vegetation, versus 17.33 for published raw pollen. | This is a rounded, label-selected reading of another study's two regional figures. It does not score our model, recover its 26-taxon result or provide nine independent landscapes. |

The [Färskesjön machine decision](vegetation-reference/farskesjon/report.json)
retains the measured plot volume, date, distance and private-source hashes;
plot identifiers and coordinates remain private. The
[historical-map coverage rows](vegetation-reference/smaland-historical-maps/coverage.json)
keep the distinct TW3 and TW4 map periods and the three shared pollen counts.
The [published-figure calculation](vegetation-reference/southern-sweden-figure/report.json)
and [printed-label transcription](vegetation-reference/southern-sweden-figure/printed-labels.csv)
keep the nine-label denominator visible. Their source-bound producers and
reproduction commands are grouped here with those governed results.

## Why modeled cover is not a vegetation reference

We checked whether the southern Sweden LandClim modeled-cover grid could
independently validate our observed-pollen lakes. The [source-lineage
receipt](../../docs/report/countries/sweden/pollen-model-lineage/report.json)
matches Neotoma sites Abborrtjärnen, Bussjösjön and Bökesjön to LandClim II
site records ABB, BUS and BOKE. Each pair has the same site sample count
(107, 69 and 52) and coordinates within 0.5 m after source rounding.
LandClim lists these as reconstruction inputs. This is strong site-level
lineage evidence, though exact sample reuse and influence on each grid result
are not authenticated.

Bussjösjön and Bökesjön both belong to grid **779**, used by five of the six
[southern Sweden synthesis targets](../../docs/report/countries/sweden/sweden_land_use_synthesis_v66.csv).
Finjasjön uses grid 829, which alone does not establish independence from
other pollen inputs. LandClim cover is a modeled result rather than a measured
vegetation outcome. We therefore do not score the grid against these pollen
sites as independent vegetation validation. The source observations remain
useful for descriptive comparison, with their distinct chronology and basin
limits visible.

## Reproduction

From the repository root, run the three vegetation-source producers with
their pinned private packets and the modeled-lineage consumer into absent
destinations under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/farskesjon/plot_support.py \
  --source-root /path/to/private/reference-sources/empd2-nfi \
  --output artifacts/jobs/vegetation-reference/farskesjon.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/smaland-historical-maps/coverage.py \
  --source-root /path/to/private/reference-sources/smaland-historical-maps \
  --output artifacts/jobs/vegetation-reference/smaland.json
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/southern-sweden-figure/compare.py \
  --source-pdf /path/to/private/reference-sources/southern-sweden-vegetation-validation/gaillard-2010.pdf \
  --output artifacts/jobs/vegetation-reference/southern-figure
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_model_lineage \
  --repository . --output artifacts/jobs/vegetation-reference/model-lineage
```

The first three producers reproduce four numeric files byte for byte. The
model-lineage producer writes its separate governed JSON receipt. These
source-bound producers and result files retain the exact identities. The
plot replay reads original source bytes but publishes no private plot
identifiers or coordinates.

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

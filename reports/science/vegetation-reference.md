# What our vegetation references can establish

The [historical-map paper account](smaland-historical-maps-paper.md),
[southern Swedish validation account](southern-sweden-validation-paper.md)
and [Namibian source-paper account](namibia-pollen-vegetation-paper.md)
explain the published methods and examples before this repository's
source-admission decisions. Their published results and our bounded source
checks have separate populations. The [main-paper inventory](paper-accounts.md)
keeps the underlying original studies and partial source access explicit.

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

We separately projected the recovered [Pyrenees botanical surveys](../../docs/report/vegetation-reference/pyrenees-botanical-projection/README.md) onto a declared 17-axis botanical panel. Each strict scenario refuses all 125 complete vectors when source blanks remain unknown; eight separately declared taxonomy, parent-row and blank alternatives that treat blanks and unlisted axes as zero yield 125 conditional vectors each. The recovered 125-plot source is distinct from the paper’s 116-plot selection, and its missing Cichorioideae axis prevents full 18-axis reproduction. This source transformation establishes no matched pollen cohort or vegetation accuracy score.

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
The open research need records the requested source
packet and resolver.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Source-bound plot/map/printed-figure screens, modeled-input dependence and modern Namibia descriptive comparisons preserve separate populations. Actual Pyrenees 17-axis botanical projection retains all 16 declared scenarios and their source/refusal/conditional assumptions without a matched pollen cohort or vegetation score.

**Unsupported claim.** Nordic repository measured-vegetation accuracy, independent validation by LandClim/HYDE modeled cover, full Pyrenees 18-axis or 116-plot paper reproduction, or vegetation accuracy inferred from botanical projection or Namibia descriptive distances.

**Actual verification performed.** Original plot/map/nine-label/Namibia sources and modeled LandClim dependency checks are synthesized from retained producer outputs. Pyrenees actual native/maintained/canonical captures retain 54 guards and 64424 independent Decimal comparisons at 2e-13 tolerance; new code/name, parent and blank alternatives preserve positive source mass and ambiguity. This index refresh performs no source reacquisition, numerical model or qualified human review.

**Remaining input or review.** Nordic EMPD2-NFI, historical-map and printed-figure leads yield zero admitted site/time/taxon/footprint/units/rights matched prediction-reference pairs. Namibia modern observed subcompositions have distinct savanna soil-pollen support. Pyrenees botanical vectors are conditional on taxonomy, parent-row and zero-for-blank scenarios; recovered 125 plots differ from the unrecovered paper 116 selection and lack Cichorioideae/full 18-axis reproduction. Resolver: Measurement and pollen source custodians plus independent landscape/palynology/taxonomy and rights reviewers Reopen when: A source-owner-reviewed original vegetation/pollen packet supplies genuinely matched physical sites, dates, taxa, landscape support, units, uncertainty and terms; freeze benchmark and predictions before previously unopened outcomes.

**Cause category.** data|assumption|comparability|access/rights|qualified review

**Consequence.** Keep all source and model roles separate, null vegetation metrics unchanged and original 125/author 116/full 18-axis panel populations distinct. Publish aggregate qualified accounts while private detailed botanical/taxonomy and plot records retain their source-specific rights limits.

**Precise next acceptance route.** Acquire original measured fractions and pollen counts with linked physical cores, dates, taxon crosswalk, compatible landscape footprint/units/uncertainty and intended-use rights; obtain independent pairing/benchmark decisions, freeze predictions before new outcomes, then score eligible channels and update model-use. Pyrenees historical reproduction separately needs the author 116 plot selection, complete 18-axis mapping and source-qualified taxonomy/blank/rights decisions.

**Negative or refused result.** Zero of 16 nearby EMPD2-NFI candidates admitted; Färskesjön footprint/volume/date mismatch and missing historical-map numeric fractions remain. Pyrenees 8 strict unknown-blank scenarios refuse 1000 complete vectors; eight declared-zero alternatives yield 1000 conditional vectors. Missing Cichorioideae, Potentilla genus proxy and 25 original zero-code analyst associations remain explicit; Nordic vegetation score stays unavailable.

**Matched denominator.** 16 nearby Nordic leads;three Småland bogs with shared modern pollen anchors;nine printed labels across two published regional figures;ten Namibian soil sites/150 radius rows/750 five-taxon pairs. Separate Pyrenees 125 recovered plots/208 taxa/1757 positive observations:16 scenarios,2000 plot contexts,34000 raw axis cells;1000 strict refusals and 1000 conditional 17-axis vectors. None is a pooled independent accuracy population.

Retained evidence: [reports/science/vegetation-reference/farskesjon/report.json](vegetation-reference/farskesjon/report.json), [reports/science/vegetation-reference/smaland-historical-maps/coverage.json](vegetation-reference/smaland-historical-maps/coverage.json), [reports/science/vegetation-reference/southern-sweden-figure/report.json](vegetation-reference/southern-sweden-figure/report.json), [docs/report/validation/empd2-nfi-pairing/report.json](../../docs/report/validation/empd2-nfi-pairing/report.json), [docs/report/vegetation-reference/namibia-pollen-vegetation/report.json](../../docs/report/vegetation-reference/namibia-pollen-vegetation/report.json), [docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json](../../docs/report/vegetation-reference/namibia-pollen-vegetation/radius-sensitivity.json), [docs/report/vegetation-reference/pyrenees-botanical-projection/report.json](../../docs/report/vegetation-reference/pyrenees-botanical-projection/report.json), [docs/report/vegetation-reference/pyrenees-botanical-projection/source-account.json](../../docs/report/vegetation-reference/pyrenees-botanical-projection/source-account.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

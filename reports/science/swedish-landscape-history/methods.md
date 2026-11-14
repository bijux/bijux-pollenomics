# Swedish landscape history: methods and scientific qualification

[Return to the main report](README.md).

## Controlled recent comparison

The primary comparison uses the same valid grids in all eight recent windows,
from 2700–3200 BP to 0–100 BP. The following values are percentages of the same
31-taxon modeled-cover denominator. Each arrow goes from **2700–3200 BP →
100–350 BP → 0–100 BP**, not between individual calendar years.

| Latitude band | Common grids | Tree-associated cover (%) | Published open land (%) | Cereal cover (%) |
| --- | ---: | --- | --- | --- |
| 55–58°N | 8 | 48.72 → 33.71 → 46.31 | 31.78 → 60.83 → 49.52 | 0.92 → 6.06 → 2.94 |
| 58–61°N | 5 | 72.18 → 61.51 → 65.94 | 15.95 → 30.17 → 27.89 | 0.19 → 5.09 → 3.88 |
| 61–64°N | 4 | 69.29 → 53.41 → 56.48 | 25.37 → 39.93 → 38.86 | 0.00 → 0.55 → 0.27 |
| 64–67°N | 0 | Not estimated on common support | Not estimated on common support | Not estimated on common support |
| 67–70°N | 4 | 59.83 → 54.73 → 52.50 | 35.06 → 39.55 → 42.84 | 0.00 → 0.00 → 0.00 |

In the two southern bands, open land and cereals both reach their maximum
within this recent comparison in **100–350 BP**. Tree-associated cover then
increases in the youngest window. At 61–64°N, the cereal component is much
smaller. At 67–70°N, changing openness cannot be described as cereal expansion
from these estimates: all eight published cereal means are zero. That is a
model result, not proof of historical absence of cultivation.

The source windows are too broad to locate a particular nineteenth- or
twentieth-century turning point or match the Estonian chronology precisely.
BP uses the conventional 1950 reference; the youngest published “present to
100 BP” window also depends on source coring support. It is not a contemporary
2026 survey. The original Estonian screenshot supplies neither a numerical
comparison table nor authenticated class and uncertainty definitions, so no
quantitative Sweden–Estonia equivalence is claimed.

## Spatial coverage and four/six-band alternatives

[Swedish grid support and five latitude bands](figures/grid-support.png)

The fixed outer extent is **55–70°N**. Five bands use boundaries
55, 58, 61, 64, 67 and 70°N. Four and six bands divide the same extent into
equal latitude widths. Each grid belongs to the band containing its centre;
southern boundaries are included and northern boundaries excluded, except
70°N is included in the last band. Boundaries were fixed before examining
the curves.

The 26 source centres range from 55.5 to 68.5°N. Their one-degree cells are
selected by Swedish centre containment, following the existing source
projection. Full cells can cross borders and include water. Weights are their
spherical areas, proportional to the cosine of centre latitude, with Earth
radius 6371.0088 km. These are **means over represented Swedish-centre grid
support**, not total Swedish land-area means. No unsampled areas are filled
or spatially interpolated. Basemap: Natural Earth Admin 0, version 5.1.1,
public domain.

[Four-, five- and six-band comparisons](figures/latitude-band-comparison.png)

The southernmost common-cohort cereal peak stays in 100–350 BP under all
three layouts, but its magnitude changes with the included territory:

| Layout | Southernmost band | Common grids | Peak cereals (%) | Youngest cereals (%) |
| --- | --- | ---: | ---: | ---: |
| Four bands | 55–58.75°N | 10 | 6.46 | 3.55 |
| Five bands | 55–58°N | 8 | 6.06 | 2.94 |
| Six bands | 55–57.5°N | 5 | 6.77 | 3.02 |

These are different geographical populations, not three independent estimates
of an identical region. The heatmap shows the full 25-window available-grid
extension; older trajectories also reflect changes in available grid support.
[PDF](figures/latitude-band-comparison.pdf) ·
[SVG](figures/latitude-band-comparison.svg).

## Coverage and source exceptions

The source contains **650 grid/windows = 26 grids × 25 age windows**, spanning
the published 0–11,700 BP labels: 268 source high-quality, 300 low-quality and
82 no-pollen-data rows. After retaining the source no-data exclusions and
refusing one zero composition, **567 compositions are usable**. Source quality
codes concern basin/site support; they are not counts of independent sites.

Two original-source exceptions are retained explicitly:

- Grid **1336**, **350–700 BP**, is labeled low quality but all 31 taxon means
  are zero. It is refused as `zero_mass`, not interpreted as zero vegetation.
- Grid **927**, **11,200–11,700 BP**, has numeric cover but is labeled no pollen
  data. It remains excluded; the analysis does not override the source flag.

[Valid and high-quality grid counts](figures/coverage.png)

The five-band recent common cohort has **8, 5, 4, 0 and 4 grids**, respectively:
21 grids in total, repeatedly summarized over eight windows. There are
32 defined band/windows and eight missing ones. At 64–67°N, no grid remains
valid in every recent window after the zero-mass refusal. Its available-grid
curve can still be displayed, but cannot replace the missing common cohort.
[All 650 dispositions](cell-dispositions.csv) preserve missing values separately
from true zero component cover.

[Common, available and high-quality support comparisons](figures/support-sensitivity.png)

High-quality-only support is also sparse: it defines 29 of 40 recent five-band
summaries, versus 40/40 available-grid summaries. Restricting quality changes
which places contribute, so differences are not an isolated measurement of
source quality. Area versus equal-grid weighting changes the primary recent
means by at most 0.368 percentage points for tree-associated cover, 0.313 for
published open land and 0.0795 for cereals. This is a weighting diagnostic,
not statistical precision.

The [Holocene extension](figures/holocene-trajectories.pdf) retains all 25
source windows with changing support. There is no artificial 100-year series,
smoothing, nearest-window fallback or truncation of 2700–3200 BP to 3000 BP.

## Figure construction and range interpretation

The open-land/cereal figures use the deposited OL means and the sum of the two
cereal taxa. Green is open land on the left axis (0–100%); orange is cereals
on the right axis (0–25%). Both scales are fixed across all latitude bands.
The cereal limit includes the largest displayed cell maximum, 22.1392%, rather
than scaling to the much smaller regional mean.

Each line is the original area-weighted mean at the midpoint of its whole
source window. Straight joins connect only adjacent available windows as a
visual guide. They create no new estimates, temporal resolution or chronology.
No smoothing is applied; missing windows break both the line and the shaded
polygon. Isolated valid windows retain their mean point and a vertical min–max
range rather than disappearing.

The translucent band spans the minimum and maximum individual grid estimates
on the exact support used for the mean. It describes spatial heterogeneity;
it is not a standard error, confidence interval, prediction interval or
posterior band. True zero and single-grid ranges remain degenerate. Marginal
source SEs are not used to construct these envelopes.

Open land includes cereals. Dual-axis curve crossings and apparent amplitudes
are scale-dependent; the joint view supports comparison of timing, not a claim
of correlation or agricultural causation. Forest versus non-tree cover is shown
[separately](figures/forest-open.pdf) on a shared percentage axis, using the
operational taxon partition below. Non-tree includes shrubs and differs from OL.

## What “forest,” “open” and “cereals” mean here

We use an explicit, exhaustive, disjoint partition of the 31 published taxon
means, whose original spelling remains in [the protocol](protocol.json):

| Operational group | Included source taxa |
| --- | --- |
| Conifers | Abies, Picea, Pinus |
| Broadleaved trees | Alnus, Betula, both Carpinus types, Castanea, Fagus, Fraxinus, both Quercus types, Tilia, Ulmus |
| Shrubs/heath | Buxus, Calluna, Corylus, Ericaceae, Juniperus, Phillyrea, Pistacia, Salix |
| Non-cereal herbs | Amaranthaceae/Chenopodiaceae, Artemisia, Cyperaceae, Filipendula, Plantago, Poaceae, Rumex |
| Cereals | Cerealia-type excluding rye, plus Secale |

“Tree-associated cover” sums the first two groups. It is an operational forest
proxy: pollen types can mix tree and shrub life forms, notably Betula in
northern settings. Classifying Corylus, Salix and the other listed mixed-life-form
taxa as shrubs is an explicit analytical convention, not a botanical admission.

“All non-tree” includes shrubs/heath, non-cereal herbs and cereals. It is not
synonymous with grassland or cleared agricultural land. “Other non-tree” excludes
cereals but still includes shrubs. The unchanged source **OL** contains Calluna,
the seven herb types and both cereal types; the source **AL** equals the two
cereals and is nested inside OL. Published ET+ST includes tall-shrub classes,
so it is not silently relabeled shrub-exclusive forest. The unresolved source
[PFT crosswalk](../publication-correspondence/pft-crosswalk/README.md) remains
separate from this direct-taxon grouping.

Every component uses the same cells and weights. Means are summed directly,
without clipping or renormalization; the largest source 31-taxon closure
residual is 1.90×10⁻¹¹ percentage points. The declared nonnegative analytical
LOVE policy is not applied to these already published REVEALS means. The
cereal/non-tree ratio in the CSV is a ratio of aggregated covers, undefined
at zero denominator; it is not farming intensity or total arable area.

## Uncertainty and scientific limits

Marginal source standard errors remain attached to their original cell and
quantity. The CSV retains unpooled OL/AL SE ranges and cellwise spatial ranges.
Those ranges are not regional confidence intervals. Joint taxon, cell and
temporal covariance or compatible draws are unavailable; summing SEs or
assuming independence would not establish the uncertainty of these curves.
A separate source check finds 341/567 usable Swedish rows incompatible with
the necessary ET/ST/OL SE triangle condition for a jointly closed total.
The independently checked mean identities do not resolve that SE issue.

This published-model summary shares pollen lineage with other LandClim
products. It supplies no independent measured-vegetation reference, no local
LOVE admission, no causal attribution of clearance to agriculture, and no
untouched confirmation cohort. Historical maps or modern observations need
matched dates, categories, spatial support, units and permitted use before
accuracy can be measured. Qualified botanical, chronology and scientific
review remain necessary for stronger interpretation.

## Source, verification and reproduction

Data: **Fyfe, R. M., et al. (2021), A full Holocene record of transient gridded
vegetation cover in Europe**, [PANGAEA 937075](https://doi.org/10.1594/PANGAEA.937075),
CC BY 4.0. Method/source description: **Githumbi, E., et al. (2022)**,
[European pollen-based REVEALS land-cover reconstructions for the Holocene](https://doi.org/10.5194/essd-14-1581-2022),
*ESSD* 14, 1581–1619. Estimates, taxonomy and source parameters remain those of
this published release; the separate 2020 PPE reference was not substituted.

The [result](result.json) binds seven source inputs and eight calculation
modules at source commit `b768c7b1204c2dd43b2c88e69d47ce2b61f662b8`.
The full calculation produced 2,250 layout/window/policy/weighting summaries,
including explicit empty-policy rows. [All derived means, ranges, identities,
coverage and denominators](trajectories.csv) are retained. Installed editable
version labels predate the study; exact committed module bytes identify the run.

An [independent original-archive check](independent-check.json) parses the native
ZIP CSVs and quality-workbook XML, uses separately stated taxonomy, Decimal
sums and sine-boundary cell areas, and verifies all 650 native rows and all
2,250 JSON/CSV summaries. Maximum percentage/coordinate discrepancy is
1.79×10⁻¹⁴; maximum area difference is 1.52×10⁻¹⁰ km². Twenty new focused tests
and 131 existing LandClim tests pass, as do configured style, formatting and
strict typing of 12 calculation/test files. Computational review is not
qualified ecological acceptance. Earlier observer interface/parser refusals
are preserved separately from the successful check; they did not require a
producer or source change.

From the repository root, prepare the standard locked development environment
and choose absent artifact destinations. The interpreter can be overridden
with another prepared development environment:

```sh
make root-check-env
BIJUX_SCIENCE_PYTHON=artifacts/root/check-venv/bin/python
PYTHONDONTWRITEBYTECODE=1 "$BIJUX_SCIENCE_PYTHON" -B -m \
  bijux_pollenomics_dev.landscape_history.landclim \
  --repository . --output artifacts/swedish-landscape-replay
cmp artifacts/swedish-landscape-replay/trajectories.csv \
  reports/science/swedish-landscape-history/trajectories.csv
cmp artifacts/swedish-landscape-replay/protocol.json \
  reports/science/swedish-landscape-history/protocol.json
```

The scientific renderer is [render.py](render.py). For the retained exports,
use Python 3.11, Matplotlib 3.11.2 and NumPy 2.4.6 in an artifact-owned environment:

```sh
python3.11 -m venv artifacts/swedish-landscape-render
artifacts/swedish-landscape-render/bin/python -m pip install \
  'matplotlib==3.11.2' 'numpy==2.4.6'
MPLCONFIGDIR="$PWD/artifacts/swedish-landscape-matplotlib" \
  artifacts/swedish-landscape-render/bin/python \
  reports/science/swedish-landscape-history/render.py \
  --study artifacts/swedish-landscape-replay --repository . \
  --output artifacts/swedish-landscape-figures
```

All twelve figures are available as PNG, editable SVG and PDF. Rendered labels,
scales, gaps and figure integrity were inspected. This first Swedish study is
complete within its published-model scope; independent historical/modern
validation and a fresh source-qualified Swedish LRA study remain separate.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Source-bound Swedish-centre published REVEALS means are summarized in four, five and six latitude bands with fixed recent and changing-support views.

**Unsupported claim.** New raw-pollen or local LOVE reconstruction, national land-area census, measured vegetation accuracy, causal agricultural interpretation or quantitative Estonia reproduction.

**Actual verification performed.** The original 2,250 summaries and 650 native-row verification are retained. This presentation revision checks saved means and extrema, missing-window geometry, complete range scales, 30 focused tests and rendered exports; it does not rerun the pollen model.

**Remaining input or review.** Grid-centre support, coarse/mixed-life-form taxonomy and source age windows restrict interpretation; joint covariance and independent matched vegetation observations are unavailable. Resolver: Qualified Swedish palaeoecology, taxonomy, chronology and reference-data reviewers. Reopen when: A reviewed same-estimand physical source and matched independent observation packet supports a stronger claim.

**Cause category.** assumption|comparability|data|qualified review

**Consequence.** Retain the 64–67°N common-cohort gap, all source refusals, changing-support qualifications and unpooled source SEs.

**Precise next acceptance route.** Review the operational groups and geographical support, admit compatible independent reference observations, then freeze a separate accuracy protocol before evaluation.

**Negative or refused result.** 82 no-data cell/windows and one zero-mass composition excluded; eight recent five-band common-cohort summaries remain missing.

**Matched denominator.** 26 grids × 25 windows = 650 cell/windows; 567 valid; 2,250 layout/policy/weighting rows; five-band recent fixed support has 21 grids with 32 defined and 8 missing band/windows.

Retained evidence: [reports/science/swedish-landscape-history/result.json](result.json), [reports/science/swedish-landscape-history/trajectories.csv](trajectories.csv), [reports/science/swedish-landscape-history/independent-check.json](independent-check.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

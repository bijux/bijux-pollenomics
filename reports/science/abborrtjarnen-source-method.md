# Our Abborrtjärnen source-method decision

We compared the published core method with the later Neotoma, PANGAEA and
LandClim records to decide which inputs we can actually use. We retain their
matching evidence and their unresolved differences separately. We have not
admitted this core to a Swedish LRA reconstruction.

In the original study, [Giesecke (2005)](https://doi.org/10.1007/s00334-005-0070-2)
reports the Abborrtjärnen pollen percentages on a terrestrial-pollen-and-spore
sum excluding aquatic taxa and *Sphagnum* spores. Radiocarbon results were
calibrated with IntCal98 and BCal; the paper used PSIMPOLL 4.10 to fit a
four-term polynomial through the calibrated dates. The paper warns that
alternative interpolation choices materially affect sample ages between dates.
The publisher identifies the article as volume 14, pages 133–147. An
[author-uploaded full text](https://www.researchgate.net/publication/226533995_Holocene_forest_development_in_the_central_Scandes_Mountains_Sweden)
provides the methodological details.

We assign these choices to the **2005 publication**. The later Neotoma/EPD record
selects chronology `EPD 1`, a linear interpolation through six calibrated
controls and a core top; its 107 sample ages have no retained uncertainty
bounds. The [control comparison](../../docs/report/source-relations/neotoma/abbo-age-controls/README.md) matches the
six radiocarbon lab/depth/age/error controls to PANGAEA. The Rootsi `ABB.xls`
age labels differ from Neotoma's across the sequence and do not declare their
unit or model. No source establishes that either later export selected the
published polynomial.

We also joined the [LegacyAge 1.0 depth estimates](../../docs/report/source-relations/neotoma/legacyage-chronology/README.md)
to all 107 ABBO Neotoma sample depths. Its AWI Bacon chronology is a separate
published age model. The LegacyAge mean differs from the Neotoma point age by
−362 to +25 years (median −16); every point age lies within its matched S5
95% range. These comparisons support a new age-aware sensitivity study, not
the age vector used in the 2005 paper, the Rootsi workbook or LandClim.

We ran that separate [interval-contained observed-pollen sensitivity]
(../../docs/report/pollen-reconstruction/age-interval-sensitivity/README.md)
on the previously exposed three-site Swedish development cohort. Eight ABBO
samples have their entire reported LegacyAge 95% range within one of four
shared 500-year bins. Four fixed methods scored the same 12 site-bin targets
per method; the site-macro inverse-distance-squared MAE on matched support
changed from 0.060058 to 0.059762. The other two sites retained Neotoma point
ages. This sparse 16-label direct-pollen comparison does not supply an LRA
input, a joint chronology posterior or an independent accuracy estimate.

## One chronology across the four frozen prediction bins

We next asked whether **one supported age allocation for all 107 samples**
could change the ranking of the four frozen predictors across bins 3, 4, 5
and 9 (1500–2000, 2000–2500, 2500–3000 and 4500–5000 native BP).
The score is the equal-bin mean of each bin's mean absolute fraction error
over the same 16 pollen taxa. Counts, predictions and training identities
are fixed; only target ages vary within the retained LegacyAge marginal
intervals, subject to nondecreasing ages with depth and equal ages at tied
depths. Samples in the gaps and outside the four bins remain constrained.

The [joint sensitivity result](chronology/abborrtjarne-joint-prediction-age-sensitivity.json)
contains **123,480 compatible nonempty membership configurations**, rather
than the 6,050,520 combinations obtained by freely combining the single-bin
blocks. Every compatible configuration has positive closed-16 counts in all
four bins. Nearest-site has the lowest equal-bin MAE throughout; the strict
order is nearest-site, CLR RBF ridge, inverse-distance-squared, training mean.
None of the six paired differences reaches zero or reverses sign.

| Frozen predictor | Lowest equal-bin MAE | Highest equal-bin MAE |
| --- | ---: | ---: |
| Nearest-site | 0.0650948552 | 0.0690389706 |
| CLR RBF ridge | 0.0725214918 | 0.0765587676 |
| Inverse-distance-squared | 0.0745906520 | 0.0789822603 |
| Training mean | 0.0747267503 | 0.0791202892 |

These displayed endpoints are rounded; the result retains exact rational
scores, all six paired ranges and 13 complete attaining age vectors. For
example, nearest-site minus CLR ridge ranges from −0.0078126593 to
−0.0072267899 on shared age allocations. Separate marginal method ranges
alone do not establish this paired result. Each retained vector preserves
five negative young ages; none is clipped to zero. The earlier
[single-bin analysis](chronology/abborrtjarne-frozen-prediction-age-sensitivity.json)
answers a different question: CLR ridge wins bin 4 separately, while
nearest-site wins the other three bins. This four-bin equal-weight score
also differs from the three-site, 12-target site-macro comparison above.

The maintained [joint consumer](../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/depth_order/abborrtjarne_joint_prediction_sensitivity.py)
ran at Git revision `3344c0d78fdfd7aca5d4f3cf171ffd50be1e0282`, using the
four input identities recorded in the result, in 1.859 seconds. From the
repository root, its command is:

```sh
python -B -m bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.abborrtjarne_joint_prediction_sensitivity \
  --repository "$PWD" \
  --output "$PWD/artifacts/science/abbo-joint-prediction-sensitivity/report.json"
```

The algorithm's exact membership and scoring contracts passed the complete
998-case depth-order test scope, including independent exhaustive rational
toy cases. A separate standard-library calculation rejoined all 107 samples
and 2,121 literal pollen measurements, checked every retained age vector and
its half-open bin memberships, and reproduced all 52 pooled vectors and
scores plus the 20 endpoint claims without calling the new algorithm.
That check confirms the saved witnesses; global sharpness depends on the
qualified exhaustive algorithm, rather than a second full study run.

This is exploratory sensitivity on a previously exposed development target.
Membership configurations are not independent observations or probability
draws, and marginal 95% supports plus monotonicity do not supply a calibrated
joint 95% chronology. The result establishes neither a new reference epoch,
historical age model, field accuracy, analytical-use permission nor ABB LRA
admission. No model was refitted or selected from these outcomes.

We did **not** treat the paper's percentage definition as a measured denominator
for Neotoma sample `173174` or a LandClim REVEALS taxon subtotal. Its 23 pollen
NISP observations total 1,206, including four `Indeterminable` grains; six
nonpollen observations total 57. The source does not supply a reviewed
per-sample denominator or a LandClim-eligible taxon mask. `E(T500)` in a
different palynological richness analysis is a rarefaction target, not this
sample's raw count. No fixed count of 500 or Bacon chronology is admitted as
the historical LandClim input.

We checked the 2005 paper's statement that at least **1,000 pollen grains and
spores** were counted in nearly all samples. This is a counting target, not an exact count
for sample `173174`. A bounded calculation from the retained Neotoma raw
dataset `19913` (sample depth `650` in the source's unstated unit, matching
PANGAEA `6.50 m`) applies the paper's stated exclusions:

| Source count group | NISP | Treatment in calculated candidate |
| --- | ---: | --- |
| All pollen observations | 1,206 | Start |
| Aquatic pollen: *Nuphar* 1, *Nymphaea alba* 4 | 5 | Exclude |
| Nonsphagnum spores: *Equisetum* 1, *Lycopodium annotinum* 1, monolete Polypodiophyta 16 | 18 | Add |
| *Sphagnum* spores 20, *Pediastrum* colonies 13, *Pinus* stomata 6 | 39 | Outside this pollen-and-spore sum |

We calculated a **candidate of 1,219** (`1,206 − 5 + 18`) if four
`Indeterminable` pollen grains were included, or **1,215** if they were
excluded. The paper does not resolve that four-grain treatment for this
export. These are source-label calculations, not an author-confirmed
percentage denominator, a fixed 500-grain count, or a REVEALS taxon subtotal.
The input is `data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json`,
SHA-256 `d96046c88b497ba07082120e446fecacad0d9b5533d8960bdbc03811976ea435`;
the [core comparison manifest](../../docs/report/source-relations/neotoma/abbo-core-identity/manifest.json) pins
the same bytes.

Separately, we checked the retained [author taxonomy lookup](../../docs/report/source-relations/neotoma/author-taxonomy-mass/README.md)
(SHA-256 `3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507`).
It assigns **1,190 of 1,206 pollen NISP** in this Neotoma sample to **13**
LandClim author targets. It labels the remaining **16** grains excluded and
leaves none unmapped. This is a sample-level source-lookup partition of pollen
only. It neither includes the nonsphagnum spores in the 2005 percentage
candidate nor establishes the time-window pooling, historical input revision,
or reviewed REVEALS denominator for the LandClim ABB sequence.

Our [core identity lead](../../docs/report/source-relations/neotoma/abbo-core-identity/README.md) supplies Neotoma
dataset `19913`, site `13338`, collection unit `ABBO`, sample `173174`, and
LandClim II site metadata row 968 for sequence `ABB`. The [native count
comparison](../../docs/report/source-relations/neotoma/abbo-native-correspondence/README.md) matches 107 depths and
2,183 explicit same-label count pairs across the two exports. These are
strong series correspondence, while physical-core identity, historical basin
geometry, selected LandClim chronology, complete taxon/PPE mapping, and
analytical-use rights remain unresolved. The LandClim row's 98 m **site**
radius and the PANGAEA 3 ha area do not establish an age-specific basin
radius. No ABBO LRA reconstruction is admitted.

We checked the [LandClimII method](https://essd.copernicus.org/articles/14/1581/2022/):
it uses a source-reported lake radius where possible and otherwise derives a
radius from measured area under a circular-shape approximation. For **3 ha**,
`sqrt(30,000 m² / pi) = 97.7205 m`; a circle of radius **98 m** has area
`3.0172 ha`. Thus the PANGAEA event area and LandClim site-radius values are
numerically compatible at their reported precision. This does not establish
that the LandClim `ABB` radius was derived from that event, that either value
describes the basin at every sample age, or that a circular ABB source profile
has been approved. The paper's 3 m/s wind, 100 km regional extent and neutral
atmosphere are named LandClimII REVEALS settings, not missing ABB core evidence
or automatically transferable LOVE parameters.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Published 2005 percentage method is distinguished from later ABBO/ABB exports; 107 depths and six radiocarbon controls correspond. Across 123,480 compatible joint age memberships for four frozen ABBO pollen-prediction bins, nearest-site retains the lowest equal-bin MAE.

**Unsupported claim.** Historical ABB LRA input or a fixed 500-grain denominator.

**Actual verification performed.** Retained core/count/control reports compare 107 depths, 2,183 same-label counts and six controls. The actual joint sensitivity consumer at 3344c0d78 scored 123,480 complete memberships; 998 depth-order tests passed. Independent source joins and exact arithmetic confirm all 13 retained age witnesses, 52 pooled vectors/scores and 20 endpoint claims without rerunning the full search.

**Remaining input or review.** 107-depth ABBO correspondence and six dated controls do not identify LandClim-selected ages, time-specific basin, eligible pollen/spore denominator, reviewed taxon/PPE profile or Rootsi workbook use rights. Resolver: ABB core/author custodian and qualified chronology, basin and palynology reviewer Reopen when: One source-bound ABB sample/window packet supplies selected age, dated geometry, denominator, parameters and permitted use.

**Cause category.** data|assumption|access/rights|qualified review

**Consequence.** Do not import a modern 98 m radius, published polynomial or alternative LegacyAge into historical LRA.

**Precise next acceptance route.** Authenticate one ABB same-core/window age, basin, count denominator, PPE and rights packet; rerun docs/report/source-relations/neotoma/lra-prerequisites/README.md before revising this source-method account or admitting an LRA row.

**Negative or refused result.** Zero ABB LRA samples admitted; candidate sample 173174 denominator remains 1,219 or 1,215 under alternate indeterminable treatment.

**Matched denominator.** 107 source depths; 1,206 pollen NISP for sample 173174; 1,190 mapped to 13 author targets, 16 excluded. Joint sensitivity: 107 samples, 16 taxa, four fixed bins and four frozen predictors; 123,480 finite configurations are not independent observations.

Retained evidence: [docs/report/source-relations/neotoma/abbo-native-correspondence/README.md](../../docs/report/source-relations/neotoma/abbo-native-correspondence/README.md), [docs/report/source-relations/neotoma/abbo-age-controls/README.md](../../docs/report/source-relations/neotoma/abbo-age-controls/README.md), [reports/science/chronology/abborrtjarne-joint-prediction-age-sensitivity.json](chronology/abborrtjarne-joint-prediction-age-sensitivity.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

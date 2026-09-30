---
title: Nordic Pollen Study and Source Decisions
audience: scientific_review
type: report
status: scoped
owner: bijux-pollenomics-scientific
last_reviewed: 2026-09-30
---

# What we established about Nordic pollen and source admission

We keep governed numeric products and producers under
`docs/report/pollen-reconstruction/`; unprefixed paths below refer to that
directory. We use this report to connect source admission to prediction,
method correspondence and the remaining scientific questions. The
[evidence index](../evidence-index.md) leads to each exact result row.

## What we admitted from source records

We retained sample-level counts, selected ages, chronology controls and taxon
trajectories for three Neotoma/EPD lakes in our
[Swedish native pollen sequences](../../docs/report/pollen-reconstruction/swedish-native-sequences/source-notes.md).
In an [independent PANGAEA EPD comparison](../../docs/report/source-relations/neotoma/abbo-profile/README.md),
we matched all 107 Abborrtjärnen depths after an exact 100-to-1 conversion
and 535 selected taxon-count cells. We did not infer historical basin geometry
from its 3 ha event area; its core date also differs from the Neotoma
collection-unit date. Our [Bökesjön basin review](../../docs/report/source-relations/neotoma/boke-basin/README.md)
found a 1984 mapped lake and two modern area measurements, neither bound to
the fossil core and sample ages.

We refused a Gilltjärnen basin transfer because
[LandClim II row 994](../../docs/report/source-relations/rootsi-landclim-overlap/README.md)
gives a 169 m radius and 101 samples at 15.083333° E, while the 101-sample
Neotoma `GILL` core is at 15.83333° E. Their approximately 42 km discrepancy
and equal sample counts do not establish core identity or age-specific basin
geometry.

For Danish Solsø, we kept the
[EPD/PANGAEA `SOLSOE81` core record](https://doi.pangaea.de/10.1594/PANGAEA.740759)
separate from later site-area reports. It gives a 2.5 ha event area, 0.98 m
water depth and a strongly drained lake. Neotoma dataset 4445 binds the same
core handle to collection unit 4303 and reports a 25,563 m² site area, but
its centroid (8.61341° E, 56.12846° N) is 1.352 km from the PANGAEA event
point (8.63333° E, 56.13333° N) by WGS84 inverse geodesic. An
[author's later comparison](https://doi.org/10.1046/j.1365-2745.2000.00490.x)
lists `SOL` at 4 ha and 2 m maximum depth (Table 1), citing Odgaard (1994),
without binding either EPD core or an age-specific shoreline. We cannot use
that area or the 2.5 ha event area for fossil-sequence LRA rings while the
record and time support differ. Neotoma dataset 4446 is a separate
`SOLSOE83` core. We reproduce no source data from the PANGAEA record, which
carries CC BY-NC 3.0 terms, and admit neither core to LRA on this evidence.
Our [Solsø LRA source decision](solsoe-lra-input.md) separately compares
LandClim I/II, PANGAEA and Neotoma sample selection; its 69 m
LandClim-II-to-Neotoma point distance does not erase the distinct 1.352 km
PANGAEA-event-to-Neotoma point discrepancy described here.

## Scope and conclusion

We produced exploratory observed-pollen predictions on the previously exposed
17-site author cohort, a three-lake Swedish 16-label holdout, Denmark/Finland/
Norway 16-label country holdouts, four 31-author-target country holdouts, and
additional Swedish bog and lake transfers on that author axis. We also ran a
real [English constrained LOVE study](english-lra-pollen-prediction.md): 14 of
15 outer folds yielded held-out forward-pollen predictions, while BECKHAM
refused. Its earlier analytical and optimizer feasibility attempts remain
separate numerical refusals. We retained bounded correspondence to author-R
and the published archive, and modeled HYDE country context. We have not
established Swedish or other Nordic LRA predictions, independent vegetation
accuracy, a source-complete paper reproduction, or a measured benefit from
HYDE. We performed no untouched confirmatory pollen evaluation.

For the 17-site English author development search, we used 31 taxa and
whole-site holdouts in three grid-stratified folds. We have not reviewed site
aliases across databases. We had already exposed all target outcomes and
used them in designing the search; the selected candidate is exploratory,
not an unbiased final skill estimate.

We selected a WGS84 radial-basis-function candidate on centered log-ratio
compositions with a 0.25 distance-quantile scale and ridge 0.1. We applied
half-count smoothing only to CLR training inputs and scored original observed
counts. Its common-support site-macro MAE is lowest in this finite search,
but it covers 174/184 attempted site bins (94.6%) versus 178/184 (96.7%)
for inverse-distance squared. On 174 shared bins, MAE is 0.017774 versus
0.018948 for inverse-distance squared and 0.019621 for training mean. We
retain the roughly 6.2% difference as development evidence alongside lower
coverage and prior outcome exposure.

## Results by scientific question

| Question | Result | Status and scope |
| --- | --- | --- |
| Are computations correct for their declared assumptions? | Focused author-pollen search tests: 3 passed. Rootsi structural replay tests: 30 passed, 1 real-source test skipped because the test is explicitly opt-in. The exact retained workbook replay exited 0 with an unchanged read set. The installed Python publication profile matched the independent author-R replay on 14,074 supported mean and SE values; maximum residuals were 1.83881e-13 and 7.15331e-14 in fractional units. The development-package test selection reached 1,097 passing tests with 3 opt-in skips, then the command failed at its final workspace-layout guard. | Verified for these bounded implementations and inputs; not a general correctness or source-identity claim. |
| Do results correspond to the selected publications? | For exact TW2 support (100–350 BP), the 2016 author-R and June 2021 PANGAEA means differ by maximum 9.19787 percentage points in grid 512 and 10.5527 in grid 562. Standard-error maximum gaps are 3.21615 and 4.25814 points. Both Python-to-R residuals are at most 1.238e-11 points. The 31-taxon mean-vector total-variation gaps are 0.092406 and 0.110704. All 31 mean ± one reported SE envelopes overlap in each grid; this is descriptive and does not test significance. Only 1/25 published-window interval labels matches exactly; the other 24 were excluded from direct comparison. The publication metadata inventory has 1,128 rows but zero authenticated historical primary-input closures. | Numerically reconciled on TW2. Historical raw-input cohorts, the paper's 12 versus PANGAEA's 11 versus archived 13 PFT positions, and the ISTS definition remain unresolved. |
| Are archived PFT/LCT standard errors feasible sums of their component uncertainty? | For each of five observed mean-addend groups (ET, ST, OL, ISTS, TBS), all 10,500 archived grid/window SE rows satisfy the necessary covariance bounds. Respectively 7,588, 7,892, 5,921, 7,013 and 5,859 rows have a nondegenerate bound with the SE strictly inside it. | This bounds a possible joint covariance only. The archive-producing transformation and covariance/delta-method replay remain unresolved. |
| Can other sites predict held-out pollen? | On the 17-site author cohort, the selected CLR-RBF scores 174 common site bins at site-macro MAE 0.017774 and Hellinger 0.256559. On those same bins inverse-distance scores MAE 0.018948 and Hellinger 0.269752, and training mean scores 0.019621 and 0.283346. Separately, Swedish Neotoma whole-site holdouts score 39 target site-bin rows per method across 13 500-cal-BP bins: nearest-site is best among the four fixed candidates (site-macro MAE 0.055371; Hellinger 0.395725), narrowly ahead of training mean (0.057177; 0.406399). | Both are exploratory and prior-exposed. The Neotoma outcomes concern declared 16-taxon subcompositions; three Swedish lakes do not support broad transfer claims. |
| Does an untuned site mean predict withheld author pollen? | The [source-bound equal-site baseline](../../docs/report/pollen-reconstruction/author-example-site-mean-holdout/README.md) scores 177 of 184 observed site-bin targets across 17 author site IDs; seven bins have no other training site. Site-macro MAE is 0.018949 fraction and total variation is 0.293703. | Prior-exposed development evidence on author-prepared counts. Its 177 scored bins differ from the later search’s 174 common bins, so these metrics do not establish model improvement. No LRA, Swedish or vegetation claim. |
| Does country-held-out direct-pollen prediction work in the Nordic extension? | Denmark: 24 scored bins at one site; nearest-site site-macro MAE 0.029809 and Hellinger 0.353519. Finland: 435 scored bins at 28 sites; nearest-site MAE 0.033223 and Hellinger 0.289538. Norway: 1,084 scored bins at 52 sites; inverse-distance-squared MAE 0.027012 and Hellinger 0.260268. The Finnish CLR-RBF is substantially worse (MAE 0.082477), and 94 Norwegian target bins remain refused. | Exploratory, prior-exposed observed-pollen subcomposition results only. Denmark has one site and cannot establish between-site Danish skill. No LRA, vegetation, or all-country skill claim. |
| Does the broader author taxonomy support Nordic observed-pollen transfer? | On 31 author lookup targets, 1,543 country-held-out site-bins score three fixed baselines (4,629 method rows), with 94 Norwegian refusals. Nearest-site site-macro MAE is 0.023242 in Denmark and 0.017335 in Finland; inverse-distance-squared MAE is 0.019459 in Norway. Assigned native NISP is 94.78% DK, 97.52% FI and 88.29% NO. | Exploratory prior-exposed observed-pollen result. Its response and denominator differ from the 16-label study, so the scores are not a direct improvement estimate. No LRA or vegetation claim. |
| Can the three Swedish lakes be held out against the other Nordic countries on that same author axis? | All 228 Swedish source samples are excluded from 81 DK/FI/NO training sites. Three fixed methods score 51 of 54 attempted Swedish site-bins (153 method rows); three early bins are refused. Inverse-distance-squared has the lowest equal-site MAE, 0.028740, and Hellinger, 0.413111. Assigned native NISP is 221,800/240,966 (92.05%) across all bins. | Exploratory prior-exposed observed-pollen result at only three target sites. The earlier Swedish author-parameter screen covers 39 common bins, not all 54. No Swedish LRA or independent vegetation claim. |
| Can an additional Swedish core be held out against those Nordic training sites? | A metadata-selected Storasjö bog core contributes 77 physical samples and 22 scored bins on the same 31-target axis. All three fixed methods score the same 22 bins (66 rows); nearest-site MAE is 0.015389 and Hellinger is 0.243786. Author-assigned NISP is 35,505/35,767; a parallel EPD dataset duplicates all 77 depths, ages and pollen count vectors and is excluded. | Additional prior-exposed development transfer at one bog core. The predictions were committed before target scoring. It does not establish country-wide skill, LRA or independent vegetation accuracy. |
| Can the same fixed methods transfer to three more Swedish lake cores? | A metadata-selected, source-default age cohort contributes 268 samples and 63 site-bins at Gilltjärnen, Lake Avegöl and Flinkasjön. All three methods score every bin (189 rows), assigning 231,115/238,797 native NISP to 31 targets. Inverse-distance-squared equal-site MAE is 0.017334 and Hellinger 0.286757; nearest-site MAE is 0.017932. | Prior-exposed development transfer across three physical lake sites, with predictions committed before scoring. The best method differs by lake; no LRA, independent vegetation, country-wide or confirmatory claim. |
| Can fold-specific LRA information predict withheld-site pollen or vegetation? | Our first author-prepared attempt refused all 15 folds after negative LOVE cover in 54/54 inspected ring rows. We then constrained local cover on the 30-target English author profile: 192/195 training fits completed and 14/15 outer folds published 42 forward-pollen predictions. Inverse-distance-squared vegetation gave site-macro pollen MAE 0.021088. The [separate English account](english-lra-pollen-prediction.md) retains the optimizer refusal, matched direct-pollen comparison and basin-radius forward sensitivity. | This is an English, prior-exposed LRA-derived pollen score. We have no independent vegetation truth. We admitted zero Swedish or four-country Nordic fossil cores to LRA because same-core chronology, historical basin, count denominator, PPE use and rights remain unresolved. |
| Are predictions accurate against independent measured vegetation? | The EMPD2–NFI review selected 16 spatial leads within 1 km and admitted 0 independent vegetation pairs. The dated Färskesjön lead is one 7 m forest plot 427 m from the lake point. A historical-map screen retains three bogs' map coverage and pollen anchors, but no exact numerical map-class values. A separate published Swedish validation figure prints nine matched pollen/REVEALS/observed-vegetation labels; its selected subset has REVEALS MAE 5.11 versus pollen MAE 17.33 percentage points. | This repository's predictors were not evaluated against measured vegetation. The published figure is a different study and its selected printed labels do not provide the original ten-lake input cohort or full 26-taxon accuracy. |
| Do HYDE or extra countries add useful information? | Native ISO-grid sums agree with 84 four-country cropland totals at seven CE labels and three scenarios. The separate count-only private-window adapter still refuses country assignments. No paired pollen ablation was run. | Source-grid correspondence established for selected cropland labels; matched pollen use remains blocked by rights, formal CRS, calendar, covariate support and scenario interpretation. |

For Swedish LRA screening, we found that exact-name LandClim II PPE/FSP
coverage intersects only six direct-cohort labels, retaining 18.1–38.7% of
each site's native NISP. The authors' taxonomy lookup assigns 98.5080%,
72.4801% and 97.3183% at Abborrtjärnen, Bussjösjön and Bökesjön, with the
remainder excluded or unmapped; all 31 author targets bind to the author
code's RPP, fall-speed and covariance files. A 1986 field study maps an
approximately 0.3 ha Bussjösjön and an older gyttja edge, while a later
3 ha inventory point lies 2.5264 km from the Neotoma site point. We cannot
bind a calibrated historical basin outline to those pollen samples. Our
[source cohort account](source-cohorts.md) and [open needs](../needed/README.md)
retain the same-core decisions needed before Swedish LRA.

The separate [30-taxon optimized LOVE feasibility pilot](../../docs/report/pollen-reconstruction/author-lra-optimized-feasibility/README.md)
retained the excluded `Filipendula` count mass and source request identities. Its
two bounded one-pair requests both refused optimizer convergence; it produced no
LRA prediction or score.

The selected CLR-RBF therefore improves the development score against the declared simple baselines on common support, but does not establish Swedish transfer, LRA-derived prediction skill, vegetation accuracy, publication reproduction or HYDE value. A separate [buffered author spatial study](../../docs/report/pollen-reconstruction/author-buffered-pollen/README.md) on two adjacent grids retained four methods' frozen predictions and scores. Its fixed fitted-RBF diagnostic performed worse than the training mean (MAE 0.040564 versus 0.025298 on 140 common bins); it remains a distinct, previously exposed diagnostic and is not the selected three-fold model.

The [archived PFT taxon arithmetic](publication-correspondence/pft-crosswalk/README.md)
now identifies the three published taxon-mean columns that sum to `ISTS` and
the six that sum to `TBS` in all 10,500 grid/window rows. Custody-bound author files support seven of nine parameter-to-output taxon names exactly and `Castanea sativa` through a source-name LUT; `Quercus deciduous t.` has no exact author source-name row. This evidence does not define
`ISTS` biologically, authenticate the source-to-output name changes, settle the
paper/archive PFT count discrepancy, or supply an SE aggregation rule. The
[paper's Sect. 3.2](https://essd.copernicus.org/articles/14/1581/2022/)
assigns deciduous Quercus type to TBS, while the archive's corresponding taxon
mean is an ISTS addend. The disagreement remains explicit in the
[publication correspondence account](../../docs/report/pollen-reconstruction/paper-correspondence.md), whose detailed
narrative is now owned by `reports/science/publication-correspondence.md`.

The Nordic direct-pollen study uses the exact 16-label response selected for the Swedish direct-pollen cohort and excludes the target country from each training set. The corrected Neotoma screen finds 91 Denmark, 1,797 Finland and 3,544 Norway candidate samples across 1, 28 and 52 physical sites. The held-out score table contains 6,172 method rows over 24 Danish, 435 Finnish and 1,084 Norwegian scored bins. Norway retains 94 refused target bins. These are prior-exposed observed-pollen results, not independent landscape or vegetation truth. Direct-pollen eligibility does not admit these data to LRA: basin geometry, exact PPE/FSP support, count-denominator choices and other source decisions remain unresolved. Independent vegetation screening admitted zero EMPD2 records in Denmark, Norway or Finland; the reviewed NFI sources lack an admitted country cohort. The source review and exact output digests are in the [Nordic direct-pollen report](../../docs/report/regions/nordic/direct-pollen/RESULTS.md), its [manifest](../../docs/report/regions/nordic/direct-pollen/manifest.json), and the public source reviews for [LandClim](../../docs/public/pollenomics-data/sources/landclim.md), [Neotoma/EPD](../../docs/public/pollenomics-data/sources/neotoma.md), [vegetation references](../../docs/public/pollenomics-data/sources/empd2-nfi-review.md), and [HYDE](../../docs/public/pollenomics-data/sources/hyde.md).

The separate [31-target author-taxonomy study](denmark-finland-norway-author-pollen.md)
uses the same Danish, Finnish and Norwegian candidate samples with the source
lookup's explicit excluded and unmapped count mass. It saves country-excluded
predictions before scoring all 1,543 supported site-bins. Nearest-site is the
lowest-MAE fixed baseline in Denmark and Finland; inverse distance squared is
lowest in Norway. The response aggregates more native NISP than the 16-label
study, but its fractional-error scores are not comparable across those two
different taxon axes. All target countries were previously exposed, so the
result is development evidence only.

The [Swedish country holdout on that same 31-target axis](sweden-author-pollen.md)
excludes all three Swedish lakes from the Danish, Finnish and Norwegian
training input. It scores 51 of 54 Swedish site-bins, with three refused
early bins. The broader all-bin source denominator is reconciled exactly to
the earlier 39-common-bin Swedish author-parameter screen. The four-country
responses are source-bound but remain small, prior-exposed development
studies; no measured vegetation or LRA result follows from them.

The [additional Storasjö core holdout](../../docs/report/regions/nordic/swedish-neotoma-holdout/README.md)
uses the previously fixed three baselines and 81 DK/FI/NO training sites. Its
protocol selected one of two parallel EPD datasets before target counts were
read; a subsequent source review found their 77 pollen count vectors identical
at matching depths. The 22-bin result extends the observed-pollen development
evidence to one bog core, with a distinct pollen source setting from the three
earlier Swedish lakes. It adds no LRA or measured-vegetation validation.

A [training-only Nordic development search](nordic-observed-pollen-selection.md)
selected IDW for Denmark and tuned CLR-RBF for Finland and Norway. The
[frozen country transfer result](nordic-observed-pollen-transfer.md)
scores the same 1,543 site-bins as the fixed study. Selected versus IDW
site-macro MAE is 0.033022 versus 0.033022 in Denmark, 0.034871 versus
0.034375 in Finland, and 0.033942 versus 0.027012 in Norway. Tuning improves
over the older fixed RBF in Finland and Norway, but does not beat IDW on either
country's matched support. Country outcomes had been inspected before this
protocol; the comparison is development evidence, not independent validation.

## Denominators and exclusions

- **Development pollen search:** 12 candidates, 17 author site groups, 3 grid-stratified whole-site folds, 184 attempted observed site bins, 174 common scored bins. The selected candidate scores 174/184 bins; the 10 unscored attempts remain in the denominator and in the coverage output.
- **Publication correspondence:** 14,074 author-example mean/SE values with zero missing or extra keys; 31 taxa compared on the sole exact published support, TW2 100–350 BP, for each of grids 512 and 562. No retrospective interval shifting was applied.
- **Archived uncertainty feasibility:** Five PFT/LCT aggregate groups times 10,500 grid/window SE rows; zero necessary-bound violations. Nondegenerate strictly interior counts are 7,588 ET, 7,892 ST, 5,921 OL, 7,013 ISTS and 5,859 TBS. The original covariance and archived release transformation were not recovered.
- **Swedish pollen-only study:** 3 Neotoma/EPD lakes, 228 source samples, 13 common 500-cal-BP bins and 39 held-out target site-bin rows per fixed method. The exact-name 16-taxon subcomposition retains 45.4–57.2% of native NISP; 3,615 exclusion rows retain every other observed label/count. **LRA:** zero folds run because basin geometry/time support and parameterized denominator are not sufficiently established.
- **Nordic direct-pollen country holdout:** Denmark 91 candidates at one site, Finland 1,797 at 28 sites and Norway 3,544 at 52 sites. The respective scored-bin denominators are 24, 435 and 1,084; Norway retains 94 refused bins. Four fixed methods yield 6,172 scored country-bin-method rows. These are not LRA or vegetation denominators.
- **Nordic author-taxonomy pollen:** The same 91/1,797/3,544 target samples aggregate into 31 author targets, retaining 122,998/1,229,019/2,018,295 assigned native NISP in DK/FI/NO while keeping excluded and unmapped mass explicit. Three fixed methods score 4,629 rows on 1,543 shared site-bins; 94 Norwegian bins are refused.
- **Swedish author-taxonomy country holdout:** 228 Swedish source samples at three sites aggregate to 221,800 assigned of 240,966 native NISP across 54 candidate site-bins. Three fixed methods score 153 rows on 51 supported bins; three are refused. The prior 39-common-bin parameter screen's 169,013/187,002 NISP matches the same-bin subset exactly.
- **Additional Swedish core holdout:** Storasjö contributes 77 physical samples after excluding a parallel duplicate EPD dataset, 22 supported 500 BP site bins, 66 fixed-method scores, and 35,505 author-assigned of 35,767 native pollen NISP. This single bog core is development evidence only.
- **Nordic selected transfer:** 12 training-only candidates over three whole-site inner folds for each excluded country yielded 40,932 trial scores and 2,439 RBF fits. The frozen selected predictors and IDW score the same 24, 435 and 1,084 outer bins; selected RBF loses to IDW in Finland and Norway. All outer cohorts were previously exposed.
- **Vegetation reference:** 16 spatial leads reviewed; zero admitted pairs. These are not 16 independent validation observations.
- **HYDE:** three private scenario windows retain 72,576 source-index positions each, including 29,217 missing values. Separately, release country tables supply 84 modeled cropland values for four Nordic countries, seven CE labels and three scenarios. All 84 native grid/ISO-country sums conserve the matched country tables within 0.000001 km². No pollen ablation was run.
- **Rootsi historical-input linkage:** 79 unique metadata candidates among 1,128 publication records, 1,049 with no candidate, zero authenticated historical inputs and zero reproduction-ready rows. The 79 retained candidate workbooks replayed to 7,459 header positions and 5,170 mechanical data rows; 78 sample-count claims agree and EKE claims 25 while the replay finds 42. This is structural evidence only.

## Reproduction and evidence

| Result | Producer, configuration and inputs | Retained output |
| --- | --- | --- |
| Development pollen search | Twelve fixed candidates were compared over three deterministic whole-site folds. Its input-manifest SHA-256 is `48d853468f979a04636642c6c757e9d05edf708d799b29cbae4d2286a9ac0acb`; the retained design declares folds, taxa, selection rule and prior exposure. | `author-development-design.json`, `author-development-interpretation.md`, `leaderboard.csv`, `coverage.csv`, `scores.csv`, and `author-development-predictions.csv.gz` in this directory |
| Author-prepared LRA development | The source-bound 1250–1750 cal BP cohort has 15 positive-count sites and 31 taxa. Whole-site folds complete training but all refuse negative reconstructed local cover. This is a prior-exposed English numerical diagnostic under declared geometry assumptions. | [Author LRA development report](english-analytical-love/README.md), `report.json`, `folds.csv` and `cover-diagnostics.csv` |
| Constrained author LRA development | A 30-target closed subcomposition excludes 159 of 20,732 author NISP. A bounded simplex LOVE backend reconstructs 192/195 training items and publishes 42 withheld-site method predictions over 14/15 folds; BECKHAM remains refused. All 42 published pollen predictions are scored after separate target opening, with site-mean MAE 0.026273 (training mean), 0.021132 (nearest) and 0.021088 (inverse-distance-squared). Fixed direct-pollen baselines score lower on the same 14 sites; vegetation accuracy is not evaluated. | [Constrained LOVE report](english-lra-pollen-prediction.md), `report.json`, `folds.csv`, `predictions.csv`, `scores.csv` and [matched direct-pollen comparison](../../docs/report/pollen-reconstruction/author-lra-constrained/direct-pollen/comparison.json) |
| Author raw/prepared counts | A private-source recount of the 17 author examples finds 501,713 raw counts and 299,660 prepared counts. The 202,053-count difference partitions into 200,247 author-excluded, 418 unmapped and 1,388 outside-window counts; each site matches its prepared total. Exact `Plantago` lookup labels prevent a six-count misclassification at LOBBSBOG. This does not identify publication inputs. | [Author preparation audit](../../docs/report/source-relations/landclim/author-preparation-audit/README.md) and its [source-bound report](../../docs/report/source-relations/landclim/author-preparation-audit/report.json) |
| Buffered spatial-block pollen comparison | The same 17 author sites in two adjacent withheld grids with a 20 km basin-edge buffer. Three fixed baselines score 148/184 observed site bins; a fixed half-count CLR-RBF scores 140/184. On the 140-bin common support its site-macro MAE is 0.040564 versus 0.025298 for the training mean. Strict-positive CLR training support is absent in both blocks. | [Source-bound study](../../docs/report/pollen-reconstruction/author-buffered-pollen/README.md), [four-method result](../../docs/report/pollen-reconstruction/author-buffered-pollen/comparisons/fitted-common-support/REPORT.md), four method prediction and score directories, and the [custody manifest](../../docs/report/pollen-reconstruction/author-buffered-pollen/manifest.json). This is prior-exposed English direct-pollen development evidence. |
| Author and archive correspondence | Independent R/Python author-example replay and exact-window PANGAEA comparison; the former passes declared tolerances, while the latter is descriptive across revisions. The three-way ledger traces the installed Python result through independent author R to the archive; mean-vector diagnostics and reported uncertainty envelopes describe the TW2 difference. A 25-window axis check establishes that only TW2 has exact shared bounds. | [Full author-example ledger](../../docs/report/publication-replay/landclim-author-example-correspondence/README.md), [full published-window ledger](../../docs/report/publication-replay/landclim-published-window-correspondence/README.md), [three-way provenance](../../docs/report/publication-replay/landclim-published-window-provenance/README.md), [uncertainty envelopes](../../docs/report/publication-replay/landclim-published-window-uncertainty/README.md), [window alignment](../../docs/report/publication-replay/landclim-window-alignment/README.md), detailed narrative in `reports/science/publication-correspondence.md`, and `paper-correspondence.csv` here |
| Publication study input identity | The pinned public site-metadata workbook yields 1,128 row-level locators and 4,512 explicit missing-input/rights refusals. Nordic source labels total 84 SE, 66 DK, 42 NO and 31 FI; these are not admitted historical study inputs or governed country cohorts. A source-bound Amsoldingersee check finds one current core with the reported 23 sample IDs, but zero of three cores with an exact `E#69` bridge or authenticated author chronology. | [Full-study input inventory](../../docs/report/publication-replay/landclim-study-inputs/README.md), [one-row source refusal](../../docs/report/publication-replay/landclim-amsoldingersee-source-review/README.md), [primary-source crosswalk](../../docs/report/publication-replay/landclim-study-inputs/primary-source-crosswalk.csv), [refusal ledger](../../docs/report/publication-replay/landclim-study-inputs/refusals.csv) and source-bound [manifest](../../docs/report/publication-replay/landclim-study-inputs/manifest.json) |
| Archived PFT/LCT uncertainty | Pinned PANGAEA source archive standard errors pass necessary lower and upper bounds for five observed aggregate/addend groups on all 10,500 grid/window rows each. | [Uncertainty-bound report](publication-correspondence/pft-crosswalk/uncertainty-bounds/report.json) and [window ledger](publication-correspondence/pft-crosswalk/uncertainty-bounds/windows.csv) |
| Rootsi structure and chronology | The retained structural replay covered 79 candidate workbooks, 7,459 header positions and 5,170 mechanical rows; 78 of 79 sample-count claims agree. A separate source-bound Neotoma check pairs all 109 FLINK and 77 STAV depths, identifies the single FLINK sign discrepancy, and supplies an STAV candidate point-age vector. Cell-level workbook content is not redistributed; historical input identity and use rights remain unresolved. | [LandClim source review](../../docs/public/pollenomics-data/sources/landclim.md), [FLINK/STAV chronology witness](../../docs/report/source-relations/landclim/neotoma-chronology-witness/README.md) and `swedish-source-questions.csv` |
| Nordic country readiness and direct-pollen transfer | Exact-label targets were separated from training by country. Frozen predictions were scored after prediction outputs were saved. The result contains 6,172 country-bin-method rows, with unsupported target bins retained in coverage. | `docs/report/regions/nordic/direct-pollen/RESULTS.md`, `manifest.json`, `coverage.csv`, `scores.csv` and `predictions.csv`; source and LRA limits are stated in the linked public source reviews. |
| Nordic author-target observed pollen | The exact author lookup maps selected native counts into 31 targets. Three fixed, country-excluded predictors score 4,629 method rows after prediction hashes are frozen; site and taxon diagnostics retain the aggregation. | [31-target study](denmark-finland-norway-author-pollen.md), [frozen predictions](../../docs/report/regions/nordic/author-target-pollen/predictions), `scores.csv`, `site-scores.csv` and `taxon-diagnostics.csv` |
| Swedish author-target observed pollen | All Swedish target sites are excluded from 81 DK/FI/NO training sites. Frozen 31-target predictions score 51 bins by three fixed methods, with three explicit refusals and exact native-count closure to the 39-common-bin screen. | [Swedish 31-target holdout](sweden-author-pollen.md), [predictions](../../docs/report/regions/nordic/swedish-author-target-pollen/predictions) and [scores](../../docs/report/regions/nordic/swedish-author-target-pollen/scores.csv) |
| Additional Swedish lake transfer | Three metadata-selected EPD lake cores contribute 268 calibrated-age samples; frozen 31-target predictions score all 63 site-bins with matched source count mass. | [Our three-lake account](sweden-lake-transfer.md), [prediction freeze](../../docs/report/regions/nordic/swedish-lake-transfer/prediction-freeze.json), [scores](../../docs/report/regions/nordic/swedish-lake-transfer/scores.csv) and [verification](../../docs/report/regions/nordic/swedish-lake-transfer/verify.py) |
| Nordic selected model transfer | A three-fold training-site search chose predictors without target-country counts. Its selected predictions were frozen and scored on identical fixed-study support, retaining 94 Norwegian refusals. | [Development search](nordic-observed-pollen-selection.md), [selected transfer](nordic-observed-pollen-transfer.md), freeze and paired scores |
| Swedish pollen-only and LRA boundary | Neotoma/EPD native pollen was admitted for direct prediction under the EPD CC BY 4.0 policy. LRA remains refused on unresolved, time-matched basin geometry and restricted exact-name parameter coverage. | `swedish-direct-pollen/` in this directory and `swedish-source-questions.csv`; the [LandClim](../../docs/public/pollenomics-data/sources/landclim.md) and [Neotoma](../../docs/public/pollenomics-data/sources/neotoma.md) reviews state the LRA boundary. |
| Vegetation boundary | The EMPD2/NFI source review admits zero matched pairs; the dated Färskesjön plot is too small and distant for the landscape estimand. The historical-map study supplies map coverage and pollen anchors at three bogs, without original numerical vegetation fractions. A separate published figure yields a bounded nine-label comparison of the original Swedish REVEALS study, not validation of this repository's predictions. | [Our vegetation-reference decision](vegetation-reference.md), [Färskesjön plot support](../../docs/report/vegetation-reference/farskesjon/README.md), [historical-map support](../../docs/report/vegetation-reference/smaland-historical-maps/README.md), [published Swedish figure comparison](../../docs/report/vegetation-reference/southern-sweden-figure/README.md), [EMPD2/NFI source review](../../docs/public/pollenomics-data/sources/empd2-nfi-review.md) and [NFI access review](../../docs/public/pollenomics-data/sources/nordic-nfi-reference-access.md) |
| HYDE modeled context | Source-reported Nordic cropland totals and matched native ISO-grid conservation at seven CE labels, with the source declaration review and separate private scenario windows. | [Country result](hyde-cropland-source-account.md) and [HYDE source review](../../docs/public/pollenomics-data/sources/hyde.md) |

We retained development predictions, per-candidate coverage, score
definitions, source hashes and refusal rows in the linked repository outputs.
We did not open a new final outcome set or call this an outcome-independent
confirmatory redesign.

To verify the tracked result, configuration and producer digests locally, run:

```sh
.venv/bin/python docs/report/pollen-reconstruction/verify_report.py
```

We retained the Swedish producer
`bijux_pollenomics_dev.source_completion.swedish_direct_pollen` with its
configuration, source hashes, cohort, prepared profiles, frozen predictions,
scores and exclusions under `swedish-direct-pollen/`. We retained the author
development design, leaderboard, coverage, candidate scores and compressed
predictions in the same governed directory. The Nordic country-held-out
products remain under `docs/report/regions/nordic/direct-pollen/`. We keep
raw snapshots in their source repositories under the public source reviews.

### Author source custody and reproduction

We use private source files alongside the tracked author-development producer.
We retained the exact original input manifest and 193 source/reference files
(2,282,688 bytes excluding the manifest) under `landclim/author-reference`
in the external source-data store. They include prepared counts, site
geometry, time windows, a taxon crosswalk and independent R reference files.
The grouped-development consumer needs 22 of those files plus the manifest.
We keep the files private because redistribution rights remain unresolved.
Their custody and author geometry do not admit the separate Swedish Neotoma
cohort to LRA.

Our [custody record](../../docs/report/pollen-reconstruction/author-source-custody.json)
binds the exact manifest, consumed input hashes, source revision, producer
and source reader independently of disposable run directories. Supply the
private capsule path to authenticate it with the existing source reader,
then reproduce the previously exposed development comparison:

```sh
author_source_root=/path/to/private/source/store/landclim/author-reference
.venv/bin/python docs/report/pollen-reconstruction/verify_report.py \
  --author-source-root "$author_source_root"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_pollen_spatial.development_search \
  --author "$author_source_root/author" \
  --reference "$author_source_root/reference" \
  --output artifacts/author-pollen-development-reproduction
```

We treat the output directory as disposable; the documented results and
private source capsule survive its removal. Readers without the private
source files can inspect retained predictions and scores, but cannot rerun
the source-backed study from this report alone.

## Earlier software delivery receipt

We retain the following earlier software check as historical implementation
evidence. We do not treat it as a current integrated acceptance run or a
scientific completion decision.

| Acceptance dimension | Current state |
| --- | --- |
| Software path | Implemented for the declared direct observed-pollen and named numerical profiles; real Nordic LRA intake remains source-gated. |
| Numerical parity | The [current R oracle](../../docs/report/method-certification/current-r-oracle/README.md) passes 43 named core and 23 source-domain cases; the separate author-example comparison covers 14,074 mean/SE values. Neither result authenticates missing historical publication inputs. |
| Empirical observed pollen | Evaluated within the stated exposed Swedish, author and country-held-out cohorts, with refusals retained in the denominator. |
| Independent measured vegetation | Not evaluated: zero admitted matched pollen/reference pairs. |
| Practical superiority | Not established. The selected author model improves one prior-exposed common-support development score, while selected Nordic transfer loses to inverse-distance squared in Finland and Norway. |
| Scientific acceptance | Pending for the full Nordic LRA and independent vegetation objective; this is a scoped developmental report. |
| Public release | Not authorized by this scientific report or its software checks. |

We ran the full non-slow/non-live/non-API development-package selection
against commit `20ecd351`. It had 1,097 passing tests before the final
guard, 3 explicitly opt-in skips and 3 pytest-asyncio deprecation warnings.
The command exited nonzero at the workspace-layout guard because an earlier
lint command had left `.ruff_cache` at the repository root. We removed that
generated cache and reran runtime isolation, both direct-pollen suites and
the guard: all 10 focused tests passed on an unchanged read set. Ruff check
and format passed with cache reads disabled; mypy passed on both direct-pollen
producers.

Our no-isolation package build stopped because `hatch-vcs` was absent from
that environment. The normal isolated build passed on the committed producer
and generated a source archive and wheel. That local version included
`+dirty` because the checkout had a separate staged documentation edit.
We published nothing. We did not run the tox build target then because its
`sync-license-assets-package` pretarget would rewrite the tracked
development-package `LICENSE`, which differs from the root license.

We keep software delivery separate from scientific acceptance. Swedish and
Nordic direct-pollen results remain exploratory; Nordic LRA and independent
measured-vegetation accuracy are still blocked or not evaluated. We have
bounded HYDE country and seven-year native grid results, but have not run a
matched pollen comparison using HYDE.

## Reopening conditions and remaining work

The Swedish and Nordic Neotoma direct-pollen results are reproducible from the retained producers and source manifests. For Sweden, use `bijux_pollenomics_dev.source_completion.swedish_direct_pollen` with the retained `swedish-direct-pollen/config.json`. For the Nordic country holdout, use `bijux_pollenomics_dev.source_completion.nordic_direct_pollen` and the reproduction command in `docs/report/regions/nordic/direct-pollen/RESULTS.md`. Swedish LRA can reopen when time-matched basin geometry, BUS source-area discrepancies, and an acceptable parameterized count denominator are documented. Rootsi workbook comparisons separately require their unresolved rights, age, taxonomy and denominator decisions. Independent vegetation scoring additionally needs authenticated pollen collection dates, cross-source identity and a defensible mapping from measured field variables to the target estimand. The [HYDE country result](hyde-cropland-source-account.md) verifies native country totals and grid cropland conservation at seven CE labels. A matched pollen comparison still requires release/member rights, formal CRS, historical CE/BP support and a justified land-use covariate design.

Nordic country-held-out direct-pollen prediction is available for Denmark, Finland and Norway on both declared taxon axes. The [Danish chronology coverage replay](../../docs/report/countries/denmark/pollen-chronology-coverage/README.md) accounts for all five captured Danish sites: 279 pollen-count samples, 91 comparable-age candidates at Solsø and 188 prerequisite refusals. Source descriptions identify 104 of the refused samples as Eemian or middle Pleistocene, outside this Holocene prediction scope; the other 83 have no source-bound Holocene eligibility. The DK/NO/FI LRA extension can reopen after country-specific Neotoma taxa/PPE, chronology, count-denominator, basin and rights review identifies admitted inputs; independent vegetation work additionally needs accessible measured source records and matched pollen/reference support. The 91 Danish, 1,797 Finnish and 3,544 Norwegian source-screen candidates are not the scored-bin denominators; coverage and refusals are retained separately in the [16-label](../../docs/report/regions/nordic/direct-pollen/coverage.csv) and [31-target](../../docs/report/regions/nordic/author-target-pollen/coverage.csv) studies.

Until those conditions are met, we claim exploratory prediction on the
exposed 17-site author cohort, exploratory Swedish and other Nordic
observed-pollen transfer, source-bound English LRA forward-pollen prediction
and bounded paper numerical correspondence. We do not certify completion
of the full Nordic LRA and vegetation-validation objective.

---
title: Swedish Pollen and Nordic Transfer Study
audience: scientific_review
type: report
status: scoped
owner: bijux-pollenomics-scientific
last_reviewed: 2026-09-29
---

# Swedish pollen and Nordic prediction study

The [Swedish native pollen sequences](swedish-native-sequences/source-notes.md) expose
the three Neotoma/EPD lakes' sample-level observed counts, selected ages, source
chronology controls and browsable taxon trajectories separately from prediction.
An [independent PANGAEA EPD profile comparison](../source-relations/neotoma/abbo-profile/README.md)
matches all 107 Abborrtjärnen depths after an exact 100-to-1 conversion and
535 selected taxon-count cells. It reports a 3 ha event area but does not
establish historical basin geometry; its core date differs from the Neotoma
collection-unit date. Neither fact changes the LRA refusal below.
The [Bökesjön basin review](../source-relations/neotoma/boke-basin/README.md)
adds a 1984 mapped lake and two modern area measurements but does not bind
their geometry to the fossil-pollen core or its sample ages.
For Denmark, the [EPD/PANGAEA Solsø core record](https://doi.pangaea.de/10.1594/PANGAEA.740759)
identifies `SOLSOE81` and reports a 2.5 ha event area, 0.98 m water depth and
a strongly drained lake. The captured Neotoma dataset 4445 binds the same
core handle to collection unit 4303 and reports a 25,563 m² site area, but
its site polygon centroid (8.61341° E, 56.12846° N) is 1.352 km from the
PANGAEA event point (8.63333° E, 56.13333° N) by WGS84 inverse geodesic.
An [author's later Danish lake comparison](https://doi.org/10.1046/j.1365-2745.2000.00490.x)
lists Solsø as `SOL` with 4 ha area and 2 m maximum depth (Table 1), citing
Odgaard (1994), but does not identify either EPD core handle or an age-specific
shoreline. Its area differs from the 2.5 ha `SOLSOE81` event record, and its
maximum lake depth is not the 0.98 m water depth at that core. Neither area can
be selected for LRA rings across the fossil sequence without resolving the
record and time support. The core-specific record therefore leaves the location
conflict and age-specific basin extent unresolved. Dataset 4446 is a separate
`SOLSOE83` core; the 1981 record does not bind its geometry. The PANGAEA
record carries a CC BY-NC 3.0 license; no source data from it are reproduced
here. Neither core is admitted to an LRA run on this evidence alone.

## Scope and conclusion

This report records the strongest supported results available on 29 September 2026. It contains exploratory observed-pollen analyses on the previously exposed 17-site author cohort, a source-backed three-lake Swedish Neotoma/EPD whole-site holdout on 16 exact labels, Denmark/Finland/Norway 16-label country holdouts, four 31-author-target country holdouts, and an additional Swedish bog-core transfer on that 31-target axis. An additional author-prepared LRA development run ends in a documented numerical refusal. It also contains evidence-bound comparisons to retained author examples and the published archive. It does **not** establish Swedish LRA predictions, independent vegetation accuracy, a source-complete reproduction of the paper, or a valid HYDE-based country extension. No untouched confirmatory pollen evaluation was performed.

The prediction cohort is the previously opened English author-prepared pollen dataset: 17 author site IDs and 31 taxa. Results use whole-site holdouts in three grid-stratified folds. Site aliases across databases have not been reviewed. All target outcomes were previously exposed and informed this development search, so the selected candidate is exploratory and is not an unbiased final skill estimate.

The selected development candidate is a WGS84 radial-basis-function model fitted to centered log-ratio transformed compositions with a 0.25 distance-quantile scale and ridge penalty 0.1. Training-only half-counts are used for the CLR fit; scores use the original observed counts. It has the lowest common-support site-macro MAE in this finite search, but covers 174/184 attempted site bins (94.6%) compared with 178/184 (96.7%) for the inverse-distance baseline. On the common 174 bins its MAE is 0.017774, versus 0.018948 for inverse-distance squared and 0.019621 for the training mean. The roughly 6.2% reduction from inverse-distance MAE is development evidence only; the lower coverage and prior outcome exposure remain part of that result.

## Results by scientific question

| Question | Result | Status and scope |
| --- | --- | --- |
| Are computations correct for their declared assumptions? | Focused author-pollen search tests: 3 passed. Rootsi structural replay tests: 30 passed, 1 real-source test skipped because the test is explicitly opt-in. The exact retained workbook replay exited 0 with an unchanged read set. The installed Python publication profile matched the independent author-R replay on 14,074 supported mean and SE values; maximum residuals were 1.83881e-13 and 7.15331e-14 in fractional units. The development-package test selection reached 1,097 passing tests with 3 opt-in skips, then the command failed at its final workspace-layout guard. | Verified for these bounded implementations and inputs; not a general correctness or source-identity claim. |
| Do results correspond to the selected publications? | For exact TW2 support (100–350 BP), the 2016 author-R and June 2021 PANGAEA means differ by maximum 9.19787 percentage points in grid 512 and 10.5527 in grid 562. Standard-error maximum gaps are 3.21615 and 4.25814 points. Both Python-to-R residuals are at most 1.238e-11 points. Only 1/25 published-window interval labels matches exactly; the other 24 were excluded from direct comparison. | Numerically reconciled on TW2. Historical raw-input cohorts, the paper's 12 versus PANGAEA's 11 versus archived 13 PFT positions, and the ISTS definition remain unresolved. |
| Are archived PFT/LCT standard errors feasible sums of their component uncertainty? | For each of five observed mean-addend groups (ET, ST, OL, ISTS, TBS), all 10,500 archived grid/window SE rows satisfy the necessary covariance bounds. Respectively 7,588, 7,892, 5,921, 7,013 and 5,859 rows have a nondegenerate bound with the SE strictly inside it. | This bounds a possible joint covariance only. The archive-producing transformation and covariance/delta-method replay remain unresolved. |
| Can other sites predict held-out pollen? | On the 17-site author cohort, the selected CLR-RBF scores 174 common site bins at site-macro MAE 0.017774 and Hellinger 0.256559. On those same bins inverse-distance scores MAE 0.018948 and Hellinger 0.269752, and training mean scores 0.019621 and 0.283346. Separately, Swedish Neotoma whole-site holdouts score 39 target site-bin rows per method across 13 500-cal-BP bins: nearest-site is best among the four fixed candidates (site-macro MAE 0.055371; Hellinger 0.395725), narrowly ahead of training mean (0.057177; 0.406399). | Both are exploratory and prior-exposed. The Neotoma outcomes concern declared 16-taxon subcompositions; three Swedish lakes do not support broad transfer claims. |
| Does an untuned site mean predict withheld author pollen? | The [source-bound equal-site baseline](author-example-site-mean-holdout/README.md) scores 177 of 184 observed site-bin targets across 17 author site IDs; seven bins have no other training site. Site-macro MAE is 0.018949 fraction and total variation is 0.293703. | Prior-exposed development evidence on author-prepared counts. Its 177 scored bins differ from the later search’s 174 common bins, so these metrics do not establish model improvement. No LRA, Swedish or vegetation claim. |
| Does country-held-out direct-pollen prediction work in the Nordic extension? | Denmark: 24 scored bins at one site; nearest-site site-macro MAE 0.029809 and Hellinger 0.353519. Finland: 435 scored bins at 28 sites; nearest-site MAE 0.033223 and Hellinger 0.289538. Norway: 1,084 scored bins at 52 sites; inverse-distance-squared MAE 0.027012 and Hellinger 0.260268. The Finnish CLR-RBF is substantially worse (MAE 0.082477), and 94 Norwegian target bins remain refused. | Exploratory, prior-exposed observed-pollen subcomposition results only. Denmark has one site and cannot establish between-site Danish skill. No LRA, vegetation, or all-country skill claim. |
| Does the broader author taxonomy support Nordic observed-pollen transfer? | On 31 author lookup targets, 1,543 country-held-out site-bins score three fixed baselines (4,629 method rows), with 94 Norwegian refusals. Nearest-site site-macro MAE is 0.023242 in Denmark and 0.017335 in Finland; inverse-distance-squared MAE is 0.019459 in Norway. Assigned native NISP is 94.78% DK, 97.52% FI and 88.29% NO. | Exploratory prior-exposed observed-pollen result. Its response and denominator differ from the 16-label study, so the scores are not a direct improvement estimate. No LRA or vegetation claim. |
| Can the three Swedish lakes be held out against the other Nordic countries on that same author axis? | All 228 Swedish source samples are excluded from 81 DK/FI/NO training sites. Three fixed methods score 51 of 54 attempted Swedish site-bins (153 method rows); three early bins are refused. Inverse-distance-squared has the lowest equal-site MAE, 0.028740, and Hellinger, 0.413111. Assigned native NISP is 221,800/240,966 (92.05%) across all bins. | Exploratory prior-exposed observed-pollen result at only three target sites. The earlier Swedish author-parameter screen covers 39 common bins, not all 54. No Swedish LRA or independent vegetation claim. |
| Can an additional Swedish core be held out against those Nordic training sites? | A metadata-selected Storasjö bog core contributes 77 physical samples and 22 scored bins on the same 31-target axis. All three fixed methods score the same 22 bins (66 rows); nearest-site MAE is 0.015389 and Hellinger is 0.243786. Author-assigned NISP is 35,505/35,767; a parallel EPD dataset duplicates all 77 depths, ages and pollen count vectors and is excluded. | Additional prior-exposed development transfer at one bog core. The predictions were committed before target scoring. It does not establish country-wide skill, LRA or independent vegetation accuracy. |
| Can fold-specific LRA information predict withheld-site pollen or vegetation? | In the separate English author-prepared development cohort, 15 whole-site folds trained 195 items but all refused prediction because reconstructed LOVE local cover was negative in 54/54 inspected ring rows. No Swedish Neotoma LRA fold was run. Exact-name LandClim II PPE/FSP coverage intersects six Swedish direct-cohort labels, retaining 18.1–38.7% of each site's NISP. The authors' taxonomy lookup assigns 98.5080%, 72.4801% and 97.3183% of all native NISP at Abborrtjärnen, Bussjösjön and Bökesjön respectively, but excludes or leaves the remainder unmapped. All 31 author targets bind exactly to the author code's RPP, fall-speed and covariance files. A 1986 field study maps a roughly 0.3 ha Bussjösjön and an ancient gyttja edge, while a later 3 ha inventory point lies 2.5264 km from the Neotoma site point; no calibrated basin outline is bound to the pollen samples. | The English calculation is a numerical negative result under declared geometry assumptions. The exact author parameter profile is source-bound, but Swedish Neotoma use still needs time-matched basin geometry and a complete count-denominator decision. Neither result is a model score. |
| Are predictions accurate against independent measured vegetation? | The existing EMPD2–NFI review selected 16 spatial leads within 1 km and admitted 0 independent vegetation pairs. Fifteen lack an authenticated pollen collection date; one source note needs review; five retain cross-source identity concerns. | Not evaluated. NFI plot measurements do not by themselves provide matched landscape-wide pollen taxon fractions. |
| Do HYDE or extra countries add useful information? | Native ISO-grid sums agree with 84 four-country cropland totals at seven CE labels and three scenarios. The separate count-only private-window adapter still refuses country assignments. No paired pollen ablation was run. | Source-grid correspondence established for selected cropland labels; matched pollen use remains blocked by rights, formal CRS, calendar, covariate support and scenario interpretation. |

The selected CLR-RBF therefore improves the development score against the declared simple baselines on common support, but does not establish Swedish transfer, LRA-derived prediction skill, vegetation accuracy, publication reproduction or HYDE value. A separate fixed fitted-RBF diagnostic on two adjacent buffered author grids performed worse than the training mean (MAE 0.040564 versus 0.025298 on 140 common bins); it remains a distinct, previously exposed diagnostic and is not the selected three-fold model.

The [archived PFT taxon arithmetic](../publication-replay/landclim-pft-crosswalk/README.md)
now identifies the three published taxon-mean columns that sum to `ISTS` and
the six that sum to `TBS` in all 10,500 grid/window rows. Custody-bound author files support seven of nine parameter-to-output taxon names exactly and `Castanea sativa` through a source-name LUT; `Quercus deciduous t.` has no exact author source-name row. This evidence does not define
`ISTS` biologically, authenticate the source-to-output name changes, settle the
paper/archive PFT count discrepancy, or supply an SE aggregation rule. The
[paper's Sect. 3.2](https://essd.copernicus.org/articles/14/1581/2022/)
assigns deciduous Quercus type to TBS, while the archive's corresponding taxon
mean is an ISTS addend. The disagreement remains explicit in the
[paper correspondence](paper-correspondence.md).

The Nordic direct-pollen study uses the exact 16-label response selected for the Swedish direct-pollen cohort and excludes the target country from each training set. The corrected Neotoma screen finds 91 Denmark, 1,797 Finland and 3,544 Norway candidate samples across 1, 28 and 52 physical sites. The held-out score table contains 6,172 method rows over 24 Danish, 435 Finnish and 1,084 Norwegian scored bins. Norway retains 94 refused target bins. These are prior-exposed observed-pollen results, not independent landscape or vegetation truth. Direct-pollen eligibility does not admit these data to LRA: basin geometry, exact PPE/FSP support, count-denominator choices and other source decisions remain unresolved. Independent vegetation screening admitted zero EMPD2 records in Denmark, Norway or Finland; the reviewed NFI sources lack an admitted country cohort. The source review and exact output digests are in the [Nordic direct-pollen report](../regions/nordic/direct-pollen/RESULTS.md), its [manifest](../regions/nordic/direct-pollen/manifest.json), and the public source reviews for [LandClim](../../public/pollenomics-data/sources/landclim.md), [Neotoma/EPD](../../public/pollenomics-data/sources/neotoma.md), [vegetation references](../../public/pollenomics-data/sources/empd2-nfi-review.md), and [HYDE](../../public/pollenomics-data/sources/hyde.md).

The separate [31-target author-taxonomy study](../regions/nordic/author-target-pollen/README.md)
uses the same Danish, Finnish and Norwegian candidate samples with the source
lookup's explicit excluded and unmapped count mass. It saves country-excluded
predictions before scoring all 1,543 supported site-bins. Nearest-site is the
lowest-MAE fixed baseline in Denmark and Finland; inverse distance squared is
lowest in Norway. The response aggregates more native NISP than the 16-label
study, but its fractional-error scores are not comparable across those two
different taxon axes. All target countries were previously exposed, so the
result is development evidence only.

The [Swedish country holdout on that same 31-target axis](../regions/nordic/swedish-author-target-pollen/README.md)
excludes all three Swedish lakes from the Danish, Finnish and Norwegian
training input. It scores 51 of 54 Swedish site-bins, with three refused
early bins. The broader all-bin source denominator is reconciled exactly to
the earlier 39-common-bin Swedish author-parameter screen. The four-country
responses are source-bound but remain small, prior-exposed development
studies; no measured vegetation or LRA result follows from them.

The [additional Storasjö core holdout](../regions/nordic/swedish-neotoma-holdout/README.md)
uses the previously fixed three baselines and 81 DK/FI/NO training sites. Its
protocol selected one of two parallel EPD datasets before target counts were
read; a subsequent source review found their 77 pollen count vectors identical
at matching depths. The 22-bin result extends the observed-pollen development
evidence to one bog core, with a distinct pollen source setting from the three
earlier Swedish lakes. It adds no LRA or measured-vegetation validation.

A [training-only Nordic development search](../regions/nordic/pollen-development/README.md)
selected IDW for Denmark and tuned CLR-RBF for Finland and Norway. The
[frozen country transfer result](../regions/nordic/selected-pollen-transfer/README.md)
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
| Author-prepared LRA development | The source-bound 1250–1750 cal BP cohort has 15 positive-count sites and 31 taxa. Whole-site folds complete training but all refuse negative reconstructed local cover. This is a prior-exposed English numerical diagnostic under declared geometry assumptions. | [Author LRA development report](author-lra-development/README.md), `report.json`, `folds.csv` and `cover-diagnostics.csv` |
| Earlier buffered baseline and fixed fitted diagnostic | Existing retained analyses with the same 17 author sites and two adjacent withheld grids; the fitted comparison uses a 20 km basin-edge buffer. | The prior exposed buffered diagnostic is summarized in this report and is not selected as the final model. |
| Author and archive correspondence | Independent R/Python author-example replay and exact-window PANGAEA comparison; the former passes declared tolerances, while the latter is descriptive across revisions. | [Full author-example ledger](../publication-replay/landclim-author-example-correspondence/README.md), [full published-window ledger](../publication-replay/landclim-published-window-correspondence/README.md), `paper-correspondence.md` and `paper-correspondence.csv` in this directory |
| Archived PFT/LCT uncertainty | Pinned PANGAEA source archive standard errors pass necessary lower and upper bounds for five observed aggregate/addend groups on all 10,500 grid/window rows each. | [Uncertainty-bound report](../publication-replay/landclim-pft-crosswalk/uncertainty-bounds/report.json) and [window ledger](../publication-replay/landclim-pft-crosswalk/uncertainty-bounds/windows.csv) |
| Rootsi structure | The retained structural replay covered 79 candidate workbooks, 7,459 header positions and 5,170 mechanical rows; 78 of 79 sample-count claims agree. Cell-level workbook content is not redistributed while source identity and use rights remain unresolved. | [LandClim source review](../../public/pollenomics-data/sources/landclim.md) and `swedish-source-questions.csv` |
| Nordic country readiness and direct-pollen transfer | Exact-label targets were separated from training by country. Frozen predictions were scored after prediction outputs were saved. The result contains 6,172 country-bin-method rows, with unsupported target bins retained in coverage. | `docs/report/regions/nordic/direct-pollen/RESULTS.md`, `manifest.json`, `coverage.csv`, `scores.csv` and `predictions.csv`; source and LRA limits are stated in the linked public source reviews. |
| Nordic author-target observed pollen | The exact author lookup maps selected native counts into 31 targets. Three fixed, country-excluded predictors score 4,629 method rows after prediction hashes are frozen; site and taxon diagnostics retain the aggregation. | [31-target study](../regions/nordic/author-target-pollen/README.md), [frozen predictions](../regions/nordic/author-target-pollen/predictions/), `scores.csv`, `site-scores.csv` and `taxon-diagnostics.csv` |
| Swedish author-target observed pollen | All Swedish target sites are excluded from 81 DK/FI/NO training sites. Frozen 31-target predictions score 51 bins by three fixed methods, with three explicit refusals and exact native-count closure to the 39-common-bin screen. | [Swedish 31-target holdout](../regions/nordic/swedish-author-target-pollen/README.md), [predictions](../regions/nordic/swedish-author-target-pollen/predictions/) and [scores](../regions/nordic/swedish-author-target-pollen/scores.csv) |
| Nordic selected model transfer | A three-fold training-site search chose predictors without target-country counts. Its selected predictions were frozen and scored on identical fixed-study support, retaining 94 Norwegian refusals. | [Development search](../regions/nordic/pollen-development/README.md), [selected transfer](../regions/nordic/selected-pollen-transfer/README.md), freeze and paired scores |
| Swedish pollen-only and LRA boundary | Neotoma/EPD native pollen was admitted for direct prediction under the EPD CC BY 4.0 policy. LRA remains refused on unresolved, time-matched basin geometry and restricted exact-name parameter coverage. | `swedish-direct-pollen/` in this directory and `swedish-source-questions.csv`; the [LandClim](../../public/pollenomics-data/sources/landclim.md) and [Neotoma](../../public/pollenomics-data/sources/neotoma.md) reviews state the LRA boundary. |
| Vegetation boundary | Existing EMPD2/NFI source, time, rights and spatial-feasibility reviews. NFI tree and field-layer labels were not opened by the eligibility scan. | `docs/public/pollenomics-data/sources/empd2-nfi-review.md` and `nordic-nfi-reference-access.md` |
| HYDE modeled context | Source-reported Nordic cropland totals and matched native ISO-grid conservation at seven CE labels, with the source declaration review and separate private scenario windows. | [Country result](../regions/nordic/hyde-country-cropland/README.md) and [HYDE source review](../../public/pollenomics-data/sources/hyde.md) |

Development predictions, per-candidate coverage, score definitions, source hashes and refusal rows are retained in the linked repository outputs. No new final outcome access or outcome-informed confirmatory redesign occurred for this report.

To verify the tracked result, configuration and producer digests locally, run:

```sh
.venv/bin/python docs/report/pollen-reconstruction/verify_report.py
```

The Swedish producer is `bijux_pollenomics_dev.source_completion.swedish_direct_pollen`; its exact configuration, source hashes, cohort, prepared profiles, frozen predictions, scores and exclusions are retained under `swedish-direct-pollen/`. The author development design, leaderboard, coverage, candidate scores and compressed predictions are retained in this directory. The Nordic country-held-out outputs are retained under `docs/report/regions/nordic/direct-pollen/`. Raw source snapshots remain governed by their source repositories and the public source reviews.

### Author source custody and reproduction

The author development study consumes private source files in addition to its tracked producer. The exact original input manifest and its 193 source/reference files (2,282,688 bytes excluding the manifest) are retained under `landclim/author-reference` in the external source-data store. This includes the prepared counts, site geometry, time-window axis, taxon crosswalk and independent R reference files. The grouped-development consumer requires 22 of those files plus the original manifest. Source inputs and reference files remain private because redistribution rights are unresolved; neither source custody nor the existing author geometry admits the separate Swedish Neotoma cohort to LRA.

The [custody record](author-source-custody.json) binds the exact manifest, consumed input hashes, source revision, producer and source reader. It preserves source identity independently of disposable run directories. Supply the private capsule path to authenticate it with the study's existing source reader, then reproduce the previously exposed development comparison:

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

The output directory is disposable; the documented results and private source capsule survive its removal. A recipient without access to the private source files can inspect the retained predictions and scores but cannot rerun the source-backed study from the report alone.

## Software delivery verification

The full non-slow/non-live/non-API development-package selection ran against commit `20ecd351`: 1,097 tests passed before the final guard, 3 explicitly opt-in tests were skipped, and 3 pytest-asyncio deprecation warnings were reported. The command exited nonzero at the final workspace-layout guard because `.ruff_cache` from an earlier lint command was present at the repository root. I removed that generated cache; the managed focused rerun of runtime isolation, both direct-pollen suites, and the workspace-layout guard passed all 10 tests with an unchanged read set. Ruff check and format passed with cache reads disabled, and mypy passed on both direct-pollen producers.

The no-isolation package build stopped because `hatch-vcs` was absent from the active environment. The package's normal isolated build passed on the committed producer and generated a source archive and wheel. The local version includes `+dirty` because the shared checkout retains a separate staged documentation edit outside the package. Nothing was published. The tox build target was not run because its `sync-license-assets-package` pretarget would rewrite the tracked development-package `LICENSE`, which differs from the root license.

These software delivery checks do not change the scientific acceptance state. Swedish and Nordic direct-pollen results are exploratory; LRA and independent measured-vegetation accuracy remain blocked or not evaluated. HYDE now has bounded source country and seven-year native grid results, while matched pollen use remains blocked.

## Reopening conditions and remaining work

The Swedish and Nordic Neotoma direct-pollen results are reproducible from the retained producers and source manifests. For Sweden, use `bijux_pollenomics_dev.source_completion.swedish_direct_pollen` with the retained `swedish-direct-pollen/config.json`. For the Nordic country holdout, use `bijux_pollenomics_dev.source_completion.nordic_direct_pollen` and the reproduction command in `docs/report/regions/nordic/direct-pollen/RESULTS.md`. Swedish LRA can reopen when time-matched basin geometry, BUS source-area discrepancies, and an acceptable parameterized count denominator are documented. Rootsi workbook comparisons separately require their unresolved rights, age, taxonomy and denominator decisions. Independent vegetation scoring additionally needs authenticated pollen collection dates, cross-source identity and a defensible mapping from measured field variables to the target estimand. The [HYDE country result](../regions/nordic/hyde-country-cropland/README.md) verifies native country totals and grid cropland conservation at seven CE labels. A matched pollen comparison still requires release/member rights, formal CRS, historical CE/BP support and a justified land-use covariate design.

Nordic country-held-out direct-pollen prediction is available for Denmark, Finland and Norway on both declared taxon axes. The [Danish chronology coverage replay](../countries/denmark/pollen-chronology-coverage/README.md) accounts for all five captured Danish sites: 279 pollen-count samples, 91 comparable-age candidates at Solsø and 188 prerequisite refusals. Source descriptions identify 104 of the refused samples as Eemian or middle Pleistocene, outside this Holocene prediction scope; the other 83 have no source-bound Holocene eligibility. The DK/NO/FI LRA extension can reopen after country-specific Neotoma taxa/PPE, chronology, count-denominator, basin and rights review identifies admitted inputs; independent vegetation work additionally needs accessible measured source records and matched pollen/reference support. The 91 Danish, 1,797 Finnish and 3,544 Norwegian source-screen candidates are not the scored-bin denominators; coverage and refusals are retained separately in the [16-label](../regions/nordic/direct-pollen/coverage.csv) and [31-target](../regions/nordic/author-target-pollen/coverage.csv) studies.

Until those conditions are met, the supported claims include exploratory prediction on the exposed 17-site author cohort, exploratory three-lake Swedish observed-pollen interpolation, and bounded paper numerical correspondence. This report does not certify completion of the full Nordic LRA and prediction objective.

# How sampling and parameters affect southern Swedish REVEALS reconstructions

Hellman, S. E. V., Gaillard, M.-J., Broström, A. and Sugita, S. (2008), “[Effects of the sampling design and selection of parameter values on pollen-based quantitative reconstructions of regional vegetation: a case study in southern Sweden using the REVEALS model](https://doi.org/10.1007/s00334-008-0149-7),” *Vegetation History and Archaeobotany* **17**, 445–459, is **Hellman et al. (2008b)** in [Gaillard et al. (2010)](https://doi.org/10.5194/cp-6-483-2010). The full supplied article has now been read. It establishes the published sensitivity designs and their conditional conclusions, replacing this account's earlier abstract-only interpretation. It does not supply a reproduced scenario calculation or validate this repository's predictions. See the [original regional-validation account](hellman-regional-validation-paper.md) and [vegetation-reference decision](vegetation-reference.md).

## Source examined

The user supplied `s00334-008-0149-7.pdf` on 26 October 2026: **832,489 bytes**, SHA-256 `4abeff940d5871015d972d1b676a84f8bcbbdca4c0892aa99334b29f644f4203`. Its fifteen PDF pages cover printed pp. 445–459, including methods, three tables, nine figures and references. Online publication is dated 2 April 2008. The original remains in the supplied directory; neither the PDF nor a full transcription is redistributed here. Receipt permits this source review, without implying rights to redistribute publisher or underlying numerical materials.

All text was read after `pdftotext -layout` extraction, and page images of Tables 2–3, Figure 8 and the parameter discussion on p. 457 were checked. Derivatives remain in `artifacts/raa-reconciliation/hellman-full-text/`. Poppler emitted an invalid shared-object hint-table warning when extracting/rendering this PDF; commands completed and the inspected pages rendered. That parser warning is not evidence of a missing article. No numerical model was rerun or plotted value digitized. Page references below are printed journal pages; PDF page number is the printed number minus 444.

## Shared observations and the six designs

The source observations are the same ten-lake, fifty-surface-sample study described in [Hellman 2008a](hellman-regional-validation-paper.md): five lakes per province, five samples per lake, at least 500 grains per sample. These are alternative calculations on shared observations, not additional independent landscapes. The companion account gives the lake roster, measured radii, winter 2003 collection, approximate 1998–2002 pollen-age support, older mixed sediment possibility and 1983–2002 vegetation-source dates. Here the lake areas are described as 76–1225 ha, mean 385 ha (p. 447); the earlier paper's prose gives a different approximate mean. Neither statement is used to replace the actual lake-specific table radii.

The 26 model taxa account for over approximately 87% of pollen. Cerealia includes Poaceae grains over 35 μm and Hordeum/Avena types; *Secale* remains separate. The Poaceae category includes smaller grains and *Phragmites* (p. 447). These definitions require an explicit taxon crosswalk before comparison with a different dataset.

Table 2 (p. 451, PDF p. 7) gives the following designs. Counts are **per region**; there are two contrasting regions.

| Published run | Samples | Lakes × samples per lake | Survey square | PPE description in Table 2 |
| --- | --- | --- | --- | --- |
| 1 | 25 | 5 × 5 | 100 × 100 km | Trees/*Secale*: Sugita 1999; Danish *Calluna*, Cerealia, *Plantago*, *Rumex*; other herbs: Broström 2004 |
| 2 | 20 | 4 × 5 | Both 50 × 50 and 100 × 100 km | Same as run 1 |
| 3 | 20 | 4 × 5 | 100 × 100 km | Danish Cerealia; other Swedish inputs |
| 4 | 20 | 4 × 5 | 100 × 100 km | Swedish inputs |
| 5 | 4 | 1 × 4 | 100 × 100 km | Same as run 1; subruns 5a–c |
| 6 | 4 | 4 × 1 | 100 × 100 km | Same as run 1; subruns 6a–c |

The 25-to-20 comparison removes all five samples from Vombsjön in Skåne and all five from Trummen in Småland. It is **five removed samples in each region**, not five total across the study. The remaining Tenhultasjön outlier is retained in the twenty-sample design to preserve balanced within-lake counts. For the four-sample designs, the prose describes random lake/sample selections repeated three times (p. 450). It does not deliver a complete source-owned sample-ID membership ledger, random seed or unrounded realization for every subrun.

## Source disagreements that prevent one unqualified replay configuration

The following are visible in the original pages, rather than extraction artifacts. They must remain separate until source-owned run information resolves their intended use.

| Source locations | Statements that disagree | Consequence |
| --- | --- | --- |
| Table 2, p. 451 versus Figure 8 caption, p. 455 | Table 2 calls four samples from one lake run 5 and one sample from four lakes run 6. Figure 8 assigns those designs to runs 6 and 5 respectively. The p. 450 prose repeats “run 5” for the second design while naming its subruns 6a–c. | Describe the physical designs explicitly; do not assign a plotted 5a–c or 6a–c realization to one design by silently selecting a label. |
| Table 2, p. 451 versus Cerealia rows in Table 3, p. 452 | Table 2 makes run 3 Danish Cerealia and run 4 Swedish. Table 3 marks Swedish 3.2 in run 3 and Danish 0.75 in run 4. | A run number alone does not bind the actual Cerealia PPE. |
| Table 3, p. 452 versus parameter prose, p. 457 | Danish *Calluna/Plantago/Rumex* entries are 1.10/0.897/1.56 in the table; the prose cites 1.61/0.46/0.35. Swedish *Rumex* is 4.7 in the table and 4.74 in prose. | Retain both locations and values; do not repair the source or transfer one as the uniquely established run input. |

The p. 456 discussion also cites a Swedish Cerealia value of 3.8 in an earlier Hellman (2005) comparison, while Table 3 prints 3.2. That historical comparison and the table's present-run input are distinct source contexts, rather than proof that one should overwrite the other.

## Parameters, survey support and uncertainty

Table 3 (p. 452, PDF p. 8) prints PPEs and fall speeds for all 26 taxa plus alternative Danish entries for four taxa. For example, its *Betula* PPE is **8.94**, fall speed **0.024 m/s**; *Ulmus* is **1.27**, **0.032 m/s**; Poaceae is reference **1**, **0.035 m/s**. These are this paper's printed values, not authority to replace a different source-bound parameter set in the repository. The methods set wind speed to **3 m/s** and attribute fall speeds to Broström (2002) (p. 450). Source and units are now available; original covariance arrays, executable input files and random uncertainty realizations are not supplied by this table. The [2008a account](hellman-regional-validation-paper.md) records the delta-method/Monte Carlo method and unpublished variance inputs, which must not be replaced with independent Gaussian errors inferred from figure bars.

The survey design is more specific than two abstract square sizes. One 100 × 100 km plot contains all five Skåne lakes; one contains the four northern Småland lakes and a separate one surrounds Trummen. Both 50 × 50 and 100 × 100 km supports are considered (pp. 447–449, Fig. 1). Crop statistics use counties for the larger support and municipalities for the smaller; municipalities with at least half their area inside the plot are included, with crop composition scaled to mapped cultivated cover (p. 449). Exact GIS polygons, pixels and unrounded regional vectors remain separate inputs.

The paper reports pollen-producing vegetation fractions of **55% and 77%** for the Skåne 50/100 km squares and **83% and 88%** for Småland (p. 453). The 2008a account reports 55%/83% for its two 100 km squares. Preserve these paper-specific support descriptions; they do not define one interchangeable cover denominator. Seven forest/cereal taxa have the strongest reference support, while some minor-herb estimates are explicitly tentative and based on class-composition assumptions (p. 454). This reference is not 26 directly measured independent cover values.

The characteristic-radius calculation assumes homogeneous vegetation, a hypothetical **950 m lake radius**, and all pollen originating within **400 km**. Twenty-five dispersal types represent the 26 taxa because Cerealia and *Secale* share a fall speed (p. 447). For abundant taxa, the source estimates roughly 60–80% within 25 km, 70–95% within 50 km and over 80% within 100 km (p. 452). The approximately **200 km characteristic radius** is a conditional, taxon-dependent transport summary; it is not a measured footprint or an RSAP estimate for each lake. The authors discuss a 200 × 200 km survey as desirable, but choose smaller squares to avoid combining contrasting regions and sea. Radius, square side and the 400 km normalization domain remain distinct.

## What the full results support

Figures 7–9 expose the published scenario estimates and error bars; numerical widths are no longer wholly inaccessible. They remain printed plots rather than an unrounded output table. The twenty-sample designs tend to have smaller estimated errors than the four-sample designs, but a smaller error bar need not mean a point estimate closer to the survey. In Småland the reported *Picea* estimate with 25 samples is about 42%, closer to the stated 45% reference than the twenty-sample estimate of about 54%, despite the outlier-related uncertainty (p. 454). This is a rounded author-reported example, not a new calculated score.

Four samples distributed over four lakes often give less variable estimates for abundant taxa than four from one lake, without consistently smaller error estimates or closer agreement. The paper explicitly notes that twenty samples need not match cover better than four (p. 455). Thus neither sample number nor outlier removal supplies a universal accuracy threshold.

Danish alternatives improve some herb comparisons, but *Plantago* in Småland can be overcorrected, and *Calluna* in Skåne changes from under- to overrepresentation (p. 456). Survey-size differences are generally modest but taxon-specific: for Skåne the larger square improves *Fagus* agreement but worsens Cerealia and *Picea*, while some Småland taxa agree better at the larger support (p. 457). These findings do not establish a universally superior PPE set or footprint.

Recommendations for multiple lakes and contemporaneous samples are conditional on the study setting. The suggested three to five samples per 100–300-year interval when only one lake is available requires good chronology (p. 458); it is not a new universal admission rule. Fossil bins, modern mixed surface sediments and vegetation compiled across years require their own temporal-support assessment.

## Existing figure arithmetic and remaining acceptance

The [Gaillard Figure 6 calculation](vegetation-reference/southern-sweden-figure/report.json) remains unchanged: nine selected rounded labels from two regional compositions give mean absolute differences of **5.11 percentage points** for REVEALS and **17.33** for raw pollen. It is neither the six-design sensitivity comparison nor a substitute for its unrounded errors or covariance. Its [transcribed rows](vegetation-reference/southern-sweden-figure/printed-labels.csv) and [producer](vegetation-reference/southern-sweden-figure/compare.py) were not rerun for this review.

The existing `hellman-sampling-scenarios` request can treat **full article receipt, published conceptual designs, printed PPE/fall-speed alternatives, survey construction and conditional findings** as supplied. It should no longer request the same main paper or say these are known only from an abstract. The remaining replay inputs are original counts and complete sample/subrun identities, resolution of the stated label/parameter conflicts, exact survey realizations, versioned numerical settings, unrounded scenario estimates/errors and uncertainty inputs. Reading the article does not manufacture those payloads, establish rights to redistribute them or constitute an independent scientific endorsement of a repository run.

The [bounded retained-input metadata check](hellman-regional-validation-paper.md#acceptance-resolved-and-remaining) found only three matching lake names represented by four historical cores, collected in 1982/1988 or with collection date absent. Their sample populations and original publications do not identify the winter-2003 five-surface-samples-per-lake population. Neither the archive nor the retained LandClim metadata supplies the original **50-sample ledger/count packet**, final **40-sample selection**, or random four-sample memberships. This is a scoped source-identity result, not a count reanalysis, proof of provider-wide absence or an untouched-cohort claim. Vombsjön and Trummen retain their published outlier/exclusion roles; the reference remains seven directly derived and nineteen class-generalized taxon estimates.

This source review closes published-design interpretation, with contradictions recorded. It adds no admitted measured-vegetation cohort, held-out score or numerical reproduction. A future comparison must preserve site grouping, source-calibration dependence, taxon closure, date and footprint compatibility, and review the particular transfer question. The main paper's availability is resolved; exact replay and matched independent validation are separate remaining work.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Full original six-design sensitivity study examined, including the per-region 25/20/four-sample denominators, printed parameters, survey supports, graphical results and conflicting internal labels/values.

**Unsupported claim.** Exact scenario reproduction, uniquely resolved conflicting inputs, universal parameter/sample-size advice, or validation of repository models.

**Actual verification performed.** Full text, source byte/hash identity and critical table/caption/prose page images checked on 26 October 2026. No model, figure digitization or existing arithmetic rerun.

**Remaining input or review.** Original 50/final 40 modern-sample ledger and counts, raw/unrounded realizations, complete random-subrun membership, conflict resolution, uncertainty inputs and a specific matched-support/dependence assessment. Three retained lake-name matches/four historical cores do not supply the modern samples. Main-paper access is resolved. Resolver: Original study custodian and qualified REVEALS/survey-design reviewer Reopen when: Source-owned original modern sample/count/run realizations permit exact replay, or genuinely matched independent observations support a separately declared validation and specific qualified comparability review. Main-paper access is resolved.

**Cause category.** data|comparability|qualified review

**Consequence.** Preserve physical scenario descriptions and conflicting source statements; do not elect a correction or substitute nine later labels for the original sensitivity results.

**Precise next acceptance route.** Source-owned numerical run information can permit exact scenario replay. A separately justified matched observation cohort and qualified interpretation are needed for repository vegetation validation.

**Negative or refused result.** No exact original modern-sample binding from three retained lake-name matches/four historical cores; original numerical replay and new repository vegetation pairing remain unperformed.

**Matched denominator.** Per region: 25 samples from five lakes, twenty from four, or four from one/four lakes; two regional landscapes, repeated alternative calculations on shared observations.

Retained evidence: [reports/science/hellman-sampling-design-paper.md](hellman-sampling-design-paper.md), [reports/science/vegetation-reference/southern-sweden-figure/report.json](vegetation-reference/southern-sweden-figure/report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

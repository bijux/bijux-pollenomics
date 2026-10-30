# REVEALS validation against regional vegetation in southern Sweden

Hellman, S., Gaillard, M.-J., Broström, A. and Sugita, S. (2008), “[The REVEALS model, a new tool to estimate past regional plant abundance from pollen data in large lakes: validation in southern Sweden](https://doi.org/10.1002/jqs.1126),” *Journal of Quaternary Science* **23**(1), 21–42, is the original modern regional validation called **Hellman et al. (2008a)** in [Gaillard et al. (2010)](https://doi.org/10.5194/cp-6-483-2010). It was published online on 26 July 2007. The full supplied article has now been read; this account replaces its earlier abstract-only interpretation. It supports a published comparison of regional vegetation estimates with a compiled vegetation reference. It does not validate predictions made by this repository. See the [vegetation-reference decision](vegetation-reference.md) and [companion sampling-design account](hellman-sampling-design-paper.md).

## Source examined

The user supplied `J Quaternary Science - 2007 - Hellman - The REVEALS model a new tool to estimate past regional plant abundance from pollen.pdf` on 26 October 2026: **729,811 bytes**, SHA-256 `c5dd00095ba3d3c13cf09aad66c111853c41884055421a50a45c489c9c26ae71`. The retained offering contains 21 PDF pages, printed pp. 21–41, including methods, Tables 1–4, Figures 1–8 and a completed reference list. The citation ends at p. 42. That pagination discrepancy alone does not justify requesting the article again. Its download watermark identifies Wiley Online Library via Lund University; receiving it is not permission to redistribute the publisher PDF or its underlying datasets.

All article text was read after `pdftotext -layout` extraction. Page images of Tables 1, 3 and 4 were also inspected. Text and page-image derivatives remain under `artifacts/raa-reconciliation/hellman-full-text/`; the original stays in the supplied source directory and is not copied into this repository. No model or figure calculation was rerun for this review. Page references below are printed journal pages; PDF page number is the printed number minus 20.

## Lakes, samples and the actual denominator

Table 1 (p. 24, PDF p. 4) gives the ten named lakes, central sampling-point coordinates, areas and measured average radii. The radius is the mean of compass-direction measurements to a fitted circle, not an area-equivalent radius calculated here.

| Region | Lakes and published radii in metres | Final inclusion |
| --- | --- | --- |
| Skåne | Börringe 520; Krageholm 805; Snogeholm 675; Sövdesjön 663; Vombsjön 1965 | First four; Vombsjön excluded |
| Småland | Vallsjön 1248; Storesjön 1372; Kansjön 468; Tenhultasjön 793; Trummen 343 | First four; Trummen excluded |

The table gives areas of 76–1225 ha, including Kansjön at 77 ha. The selection prose describes a general criterion of at least 100 ha with exceptions of 75 and 77 ha, nearly circular shape and little stream inflow/outflow, and an approximate mean lake size of 220 ha (p. 24). The companion paper instead reports a mean of 385 ha; neither mean replaces the source-specific area/radius entries. The reported radii and areas must remain source values rather than being forced to satisfy an ideal-circle identity. Central-point coordinates do not establish a coordinate datum or full survey polygon.

Winter 2003 sampling used the top 2 cm from a central deepest-basin point and four points 10 m north, east, south and west, with at least 500 grains counted per sample (p. 27). Initially there were **50 samples: five per lake, five lakes per region**. PCA identified all five samples from each of Vombsjön and Trummen and one from Tenhultasjön as outliers. The final model removed the two whole lakes, but retained the Tenhultasjön sample to keep five samples per lake. Thus it used **40 samples from eight lakes, 20 per region**, rather than removing all eleven flagged samples (p. 28).

The authors ran both pooled five-sample lake counts, producing four lake estimates and a regional mean in each region, and the 40 individual sample counts (p. 28; Figs. 6–7, pp. 34–35). The model's 26-taxon closure accounts for at least 87%, usually nearly all, of terrestrial pollen. The separate exploratory PCA used 33 terrestrial taxa. Neither taxa nor within-lake samples are independent regional landscapes: the central comparison is **two regional compositions**.

Surface sediments were estimated to represent approximately 2001–2002 in Skåne and 1998–2002 in Småland. These are minimum accumulation periods; mixing can include older pollen. Vegetation sources span 1983–2002, mostly 2000/2002 (pp. 26–27, 32). “Modern” therefore does not establish exact same-year observation pairing.

## What the vegetation reference measures

The two **100 × 100 km** survey squares were positioned with the sampled lake groups near their centres (Fig. 1, p. 22; p. 24). Land-cover classes from Swedish CORINE Land Cover, Landsat/forest-inventory composition and agricultural statistics were combined. Fifty-seven land-cover subclasses became fifteen vegetation classes (Table 2, p. 25). Exact machine-readable boundaries and original mapped pixels are not supplied by these figures.

Only **seven taxa** could be derived directly from those sources: *Pinus, Picea, Fagus, Quercus, Betula*, Cerealia excluding *Secale*, and *Secale*. Cover for the other **nineteen taxa** was approximated through vegetation-class composition. That generalization used vegetation mapping within 100 m and aerial-photo interpretation from 100–1500 m at 33 sites (Broström et al., 2004; p. 24). These are compiled reference estimates with differing measurement support, rather than 26 independently measured taxon-cover observations. The herb PPEs also cite Broström et al. (2004). This shared cited source motivates a specific dependence check before calling every reference component independent; the article does not establish a row-level overlap audit or independence of the full reference and calibration chain.

**Table 3 (p. 26, PDF p. 6) supplies printed reference percentages and error estimates for all 26 taxa in both regions.** The earlier claim that no full reference vector was available is obsolete. For example, printed *Picea* cover is 13.06% in Skåne and 43.84% in Småland; Cerealia is 41.07% and 5.49%. These rounded table values are source evidence, not unrounded GIS realizations or newly admitted observations.

The denominator removes water, cities, non-pollen-producing cover and vegetation outside the 26-taxon selection. The remaining area is reported as 55% of the Skåne square and 83% of the Småland square; the selected taxa represent approximately 70–90% of vegetation. Taxon cover is then renormalized to sum to 100% (pp. 26–27). It is not an unconditional percentage of every square kilometre in the survey square.

Reference errors also have different meanings (pp. 24–26; Table 2). SCLC errors use half of one minus user accuracy from a regrouped national confusion matrix; forest errors use pixel-scale cross-validation; crop errors reflect incomplete knowledge of unsubsidized agricultural area. Some classes combine sources. These printed errors cannot be assigned one common standard-error distribution without further evidence.

## Model inputs, uncertainty and footprint

The paper specifies `reveals.v3.7.exe`, source-specific lake radii, wind speed **3 m/s**, and a **50 km** integration cutoff, chosen with the 100 × 100 km vegetation squares in mind (p. 28). The transport model assumes a circular canopy opening, even directional dispersal and wind transport; actual inflow, shoreline shape and sediment redistribution can violate these assumptions (pp. 23–24). The paper distinguishes the lake deposition model from the mire approximation; it does not justify replacing every receiver with a point or a homogeneous landscape of arbitrary radius.

Tree and *Secale* PPEs come from Sugita et al. (1999), herb PPEs from Broström et al. (2004), and the main Cerealia PPE from Nielsen (2004). Values originally referenced to *Juniperus* were converted to Poaceae as reference. Fall speeds are attributed to Broström et al. (2004). A second prediction additionally substitutes Danish PPEs for *Fagus, Plantago, Rumex* and *Calluna* (p. 28; Fig. 5, p. 30). The [companion article](hellman-sampling-design-paper.md) prints PPE/fall-speed tables but also contains conflicting parameter labels; those are not silently resolved here.

PPE variance inputs are attributed to unpublished Broström and Nielsen material. The paper states that covariances for *Picea, Pinus* and *Secale* were fixed at zero because data were lacking. Regional standard errors combine a delta method with Monte Carlo simulation (p. 28). The full variance/covariance inputs, original executable/run configuration and simulation realizations are not delivered by a marginal error bar or this methods description.

The cited footprint calculation assumes a hypothetical 950 m lake radius, homogeneous vegetation, wind 3 m/s and all pollen originating within 400 km. It yields at least about 80% within 50 km for most selected taxa, about 70% for *Filipendula* (p. 28). These assumptions do not make a 50 km circle, 100 km square and 400 km normalization domain interchangeable, nor establish an empirical footprint for each lake.

## Published results and the separate figure calculation

The original comparison supports improved agreement for broad vegetation groups, with substantial taxon-specific exceptions (pp. 29–33; Figs. 4–5). *Alnus* and *Corylus* are overestimated and *Quercus* underestimated in both regions; *Picea* is underestimated in Skåne and overestimated in Småland. Danish alternatives improve some herb estimates, whereas the Danish *Fagus* choice worsens Skåne. Thus the full paper does not imply uniformly accurate taxon estimates or a generally superior PPE origin.

Table 4 (p. 37, PDF p. 17) compares older methods with REVEALS after a **fourteen tree/shrub taxon closure**, with printed REVEALS Euclidean distances of **24.4 for Skåne and 13.3 for Småland**. Its censored entries such as `<1`, taxon selection and comparison supports preclude treating it as an exact 26-taxon error or comparing it directly with our selected-label MAE. The authors themselves discuss limits to comparisons among the earlier studies (p. 38).

The existing [Gaillard Figure 6 transcription](vegetation-reference/southern-sweden-figure/printed-labels.csv) remains a different calculation: **five Skåne plus four Småland printed labels** from two compositions yield mean absolute differences of **5.11 percentage points** for REVEALS and **17.33** for raw pollen. Its [selection/result](vegetation-reference/southern-sweden-figure/report.json) and [producer](vegetation-reference/southern-sweden-figure/compare.py) are unchanged. Whole-percentage display selection and rounding prevent inference to the complete original taxon set; no new score or confidence interval was calculated from this full-text review.

## Acceptance resolved and remaining

The existing `hellman-regional-validation` source request can treat **article receipt and published study interpretation** as supplied: lake identities/regions/printed coordinates, areas/radii, collection method and approximate age support, original versus final sample counts, full printed 26-taxon reference/error table, reference construction, software name, parameter provenance and uncertainty method. Repeating a request for the main article or claiming that these published details are still wholly absent would be incorrect.

Correspondence recorded on **27 October 2026** supplies Anneli Poska's reply and her subsequent author enquiry addressed to Marie-José for Sofie's testing datasets for both 2008 studies. The current correspondence state is **reply received; author enquiry in progress; original data pending**. Anneli reports that these study datasets are unavailable from Neotoma; this is her reported finding, not an exhaustive archive search or proof that no related records exist. No original message files, message IDs, email dates, attachments or recipient address for Marie-José were supplied; the recording date establishes neither the messages' sending dates nor delivery or a response from Marie-José. No original count/sample packet, vegetation-reference files, scripts/settings/outputs or use conditions accompanied the messages. Await the existing enquiry's outcome and inspect any supplied material against the remaining fields below before asking for gaps; this reply does not reproduce the study or admit a new validation pair.

A bounded metadata check of the retained Neotoma/EPD archive and LandClim metadata found three Table 1 lake-name matches, representing four historical cores: Kansjön `KANSJON` (dataset 1438/unit 1400; 45 samples, collected 1988), Krageholmssjön `KRAGJR` (4162/4033; 110 samples, collected 1982) and `KRAGMJNY` (23013/16622; 96 samples, collected 1982), and Lake Trummen `TRUMMTOT` (4496/4353; 98 samples, collection date null). Their devices, populations and linked historical publications do not bind the winter-2003 Hon-Kajak surface samples. Retained Swedish provider listings and LandClim workbook rows 1001/1004/1011 identify the same historical leads, without supplying that binding. The other seven lake names were absent from these scoped metadata sources; this is not a claim that no provider holds them. The original native candidate parts were checked against the retained archive baseline. The native scan completed in 0.44 s with 218,791,936-byte peak RSS, and the workbook metadata check in 0.17 s with 53,870,592-byte peak RSS, within the declared 60 s/512 MiB bounds. Metadata extracts remain private under `artifacts/raa-reconciliation/hellman-input-support/`; no pollen datum values were inspected or fitted. Existing source names, publication-year overlaps or nearby coordinates do not establish sample identity, and Trummen remains excluded from the original final analysis.

An exact replay still needs the source-owned **original 50-sample ledger/count packet and its final 40-sample selection**, unrounded reference/model outputs, original spatial layers and boundaries, sufficient taxon mapping, executable/run settings and PPE covariance/Monte Carlo inputs. The text refers to an Appendix for counts/PPEs/nomenclature (pp. 27–28); no such Appendix is present in the supplied article offering, which ends with completed references. This identifies the missing payload rather than proving the main article was supplied incorrectly. Any use or redistribution of underlying survey/count data needs its actual terms; no blanket permission gate prevents reading the supplied paper.

Published source interpretation is consequently complete within this account; **new matched independent vegetation admission and held-out validation remain unperformed**. They require an explicit estimand, date/taxon/footprint match, source-dependence assessment and appropriate uncertainty. Receiving a peer-reviewed article does not constitute an independent review of this repository's implementation or establish target observations for its cohorts. The separate qualified pairing/replay review remains open; there is no new repository vegetation pair and no new numerical model run.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Full original paper examined: ten-lake sampling, eight-lake final analysis, two regional reference compositions, 26 printed reference/error rows per region and conditional published validation findings.

**Unsupported claim.** Exact original-run reproduction, 26 independent measured references, or validation of repository predictions.

**Actual verification performed.** Full text, source byte/hash identity and critical table page images checked on 26 October 2026; existing nine-label arithmetic retained without rerun.

**Remaining input or review.** Original 50/final 40 modern-sample ledger and counts, unrounded outputs, spatial realization, uncertainty inputs, source-dependence and matched-estimand review. Four retained historical cores from three lake-name matches do not bind the 2003 samples. Main-paper access is resolved. Resolver: Original study custodian and independent vegetation/palynology reviewer Reopen when: Source-owned original modern sample/count/run realizations permit exact replay, or genuinely matched independent observations support a separately declared validation and specific qualified comparability review. Main-paper access is resolved.

**Cause category.** data|comparability|qualified review

**Consequence.** Preserve the nine-label 5.11 versus 17.33 percentage-point comparison on its own denominator; keep new independent vegetation metrics unavailable.

**Precise next acceptance route.** Obtain the missing original numerical payload where replay is intended, or source-bind genuinely matched independent observations for a new validation. Review actual comparability questions rather than asking again for the supplied article.

**Negative or refused result.** No exact original modern-sample binding from three retained lake-name matches/four historical cores; original numerical replay and new repository vegetation pairing remain unperformed.

**Matched denominator.** Initial 50 samples/ten lakes; final 40/eight lakes, twenty/four per region; two regional compositions. Later local figure calculation: nine displayed region/taxon labels.

Retained evidence: [reports/science/hellman-regional-validation-paper.md](hellman-regional-validation-paper.md), [reports/science/vegetation-reference/southern-sweden-figure/report.json](vegetation-reference/southern-sweden-figure/report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

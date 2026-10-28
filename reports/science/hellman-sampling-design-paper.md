# How sampling and parameters affect southern Swedish REVEALS reconstructions

**Citation and question.** Hellman, S. E. V., Gaillard, M.-J., Broström, A. and Sugita, S. (2008), “[Effects of the sampling design and selection of parameter values on pollen-based quantitative reconstructions of regional vegetation: a case study in southern Sweden using the REVEALS model](https://doi.org/10.1007/s00334-008-0149-7),” *Vegetation History and Archaeobotany* **17**(5), 445–459. This is the paper called **Hellman et al. (2008b)** in [Gaillard et al. (2010)](https://doi.org/10.5194/cp-6-483-2010). It asks how pollen-sample selection and number, vegetation-survey size and pollen productivity values affect quantitative regional cover estimates. We need it to judge whether an apparently good REVEALS comparison is stable under those choices, not to score our own predictions. [Publisher citation and abstract](https://link.springer.com/article/10.1007/s00334-008-0149-7); [corresponding university record](https://portal.research.lu.se/en/publications/effects-of-the-sampling-design-and-selection-of-parameter-values-/).

The publisher abstract compares **25, 20 and four pollen samples**; its scenario-level numerical outputs are unavailable here. [Publisher abstract](https://link.springer.com/article/10.1007/s00334-008-0149-7).

## Why the choices matter

Pollen percentage is a share of counted grains; regional vegetation percentage is a share of cover over a defined landscape. Taxa differ in grain production and dispersal. **REVEALS** (Regional Estimates of VEgetation Abundance from Large Sites), part of the Landscape Reconstruction Algorithm, uses pollen from large sites and a pollen productivity estimate (**PPE**) for each taxon to estimate regional vegetation. The PPE set is therefore an input assumption, not a measured cover value. Pollen fall speed and source geometry also govern dispersal. Changing sample selection, survey area or productivity inputs may change the cover estimate or its uncertainty. The [regional validation paper](hellman-regional-validation-paper.md) establishes the modern southern Swedish setting. [Our method profile](publication-correspondence/author-method-profile.md).

```text
large-site pollen samples + selected taxa/PPEs + dispersal setup
  → REVEALS regional cover and its error estimate
  ↔ vegetation compiled over a chosen survey area
  → compare outcomes across sample/PPE/area choices
```

The comparison units are **reconstructions under alternative inputs**, not new independent landscapes. The abstract reports little survey-size effect, a **200 km characteristic radius**, and good agreement with vegetation in a **100 × 100 km²** square. A radius and square describe different spatial supports; exact polygons are unavailable. [Publisher abstract](https://link.springer.com/article/10.1007/s00334-008-0149-7).

## What the authors report

The authors report larger error estimates with outliers and very large ones with four samples. Danish PPEs improved agreement for **Cereals, *Rumex acetosa/acetosella*, *Plantago lanceolata* and *Calluna***. They favor multiple sites and testing more than one PPE set. Numeric error widths are unavailable. [Publisher abstract](https://link.springer.com/article/10.1007/s00334-008-0149-7).

The **25 → 20** comparison gives a worked denominator: `25 − 20 = 5` excluded outliers. A taxon-specific percentage-point change or standard error is **not available** from this source access. [Publisher abstract](https://link.springer.com/article/10.1007/s00334-008-0149-7).

## What our available comparison can and cannot show

[Gaillard et al. (2010), Figure 6, p. 490](https://cp.copernicus.org/articles/6/483/2010/) presents one southern Swedish published pollen–REVEALS–vegetation comparison and refers readers to **both** Hellman papers. Our [nine transcribed labels](vegetation-reference/southern-sweden-figure/printed-labels.csv) include, for example, Småland *Picea*: **16% pollen, 54% REVEALS and 44% observed cover**, hence absolute differences of **28** and **10 percentage points** against the rounded observed label. Across five Skåne and four Småland labels, the corresponding pooled mean differences are **17.33** and **5.11 percentage points**. [Calculation](vegetation-reference/southern-sweden-figure/report.json). The Figure 6 caption says REVEALS used southern Swedish productivity estimates; this single displayed setup cannot reveal the Danish-versus-Swedish PPE sensitivity, the 25/20/four sample comparison, or their uncertainty estimates. The nine labels are selected taxa in two compositions, not nine independent sample replicates or the original 26-taxon result.

The publisher page offers an abstract and a subscription preview; no full lawful article or scenario-level data were located in the retained packet examined for this account. Consequently this is a **partial paper account**. It verifies the paper's citation and abstract-level claims and uses the separate Gaillard figure only as contextual evidence. It neither reconstructs the scenario calculations nor determines whether their results transfer to the repository's present validation cohorts. [Publisher record](https://link.springer.com/article/10.1007/s00334-008-0149-7); [our vegetation-reference decision](vegetation-reference.md).

To reproduce only the bounded figure calculation with lawful access to the Gaillard PDF, run from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/southern-sweden-figure/compare.py \
  --source-pdf /path/to/gaillard-2010.pdf \
  --output artifacts/jobs/southern-sweden-figure/reproduction
```

The [producer](vegetation-reference/southern-sweden-figure/compare.py) authenticates the PDF SHA-256 `46bd92497d03169735b9a4665d71214c5dd8ff52ceddf39c577f0a4495fe73bd` and writes the printed-label calculation; it does not implement the Hellman sensitivity scenarios.

The precise **unsent source request** is for lawful full text and supplements of this 2008b paper; the 25-sample ledger identifying the five excluded outliers and the four retained samples, with lake IDs and sampling dates; scenario-specific pollen counts and 26-taxon mapping; both survey boundaries and cover vectors; Swedish and Danish PPE tables and taxon crosswalks; fall-speed, basin and dispersal settings; per-scenario estimated cover and error values and their calculation method; and permitted reuse terms. An **unsent qualified-review request** is to examine whether those scenario definitions and uncertainty measures are comparable to any proposed repository run and whether a different site or PPE set would require new sensitivity analysis. No reviewer verdict or colleague reading outcome is claimed.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Publisher abstract supports a bounded original sensitivity summary and separates it from later figure arithmetic.

**Unsupported claim.** Scenario-level Hellman 2008b numerical reproduction or transferred parameter advice.

**Actual verification performed.** Retained primary publisher/university records and later figure check are described; index did not access full scenario data.

**Remaining input or review.** Abstract-level 25/20/four-sample findings lack original scenario membership, counts, PPE alternatives, survey areas and numeric errors; the nine rounded later labels cannot reproduce them. Resolver: Original study custodian and qualified REVEALS/survey-design reviewer Reopen when: Lawful versioned scenario tables and parameter/output rows allow scenario-by-scenario reproduction and transfer review.

**Cause category.** data|access/rights|comparability|qualified review

**Consequence.** Do not treat nine rounded figure labels as the 25/20/four-sample sensitivity or recommend a PPE set from them.

**Precise next acceptance route.** Lawful versioned scenario tables and parameter/output rows allow scenario-by-scenario reproduction and transfer review. Then update reports/science/vegetation-reference.md.

**Negative or refused result.** Scenario-specific errors and uncertainty widths not evaluated locally.

**Matched denominator.** Original scenarios compare 25, 20 and four samples; 25 to 20 excludes five outliers, not five independent landscapes.

Retained evidence: [reports/science/hellman-sampling-design-paper.md](hellman-sampling-design-paper.md), [reports/science/vegetation-reference/southern-sweden-figure/report.json](vegetation-reference/southern-sweden-figure/report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

---
title: Papers and Evidence Roles
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-10-02
---

# Read the papers without mixing their claims

A paper can explain a model, show a numerical calculation, publish a reconstruction or compare it with measured vegetation. These are different uses of evidence. Before treating a reported success as validation, identify **what was compared, on which inputs, in what units, and with what independent reference**.

The repository's [main-paper inventory](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/paper-accounts.md) identifies nine canonical accounts. Each explains the scientific question and assumptions, works through a source-to-result example, separates the authors' findings from our own calculation, and states which inputs or decisions are missing. The [machine inventory](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/paper-accounts.csv) records source access and data-release scope. These report references describe the local source revision; a local candidate does not establish public deployment or independent review.

## Follow the evidence route

**Counts are not cover.** A sediment sample's pollen fraction divides counted grains. A vegetation fraction divides land cover within a defined spatial area. Productivity and dispersal differ among taxa, so one cannot stand in for the other. REVEALS estimates regional cover; LOVE uses regional background and small-site pollen to infer local cover. Their physical basin, age, taxon, parameter and area assumptions need source-specific admission. A finite calculation can still yield an invalid cover composition.

**A code comparison tests calculation.** Our selected author-R and Python values agree on declared inputs, as explained in the [method correspondence results](results.md#implementation-correspondence-and-archive-differences). This does not authenticate the complete historical publication inputs or measure ecological accuracy.

**A pollen prediction score tests pollen.** Whole-site or country exclusion reduces training overlap under a declared protocol. The result still needs the taxon/count denominator, attempted and refused bins, outcome exposure and temporal support. Our [source scope](sources.md) and [prediction results](results.md) retain those limits.

**Vegetation accuracy needs an independent matched measurement.** A nearby plot, historical map or another model's cover estimate must match the proposed physical site, time, taxa and spatial estimand. Our current [vegetation reference review](../../../report/validation/empd2-nfi-pairing/README.md) has no admitted Nordic pair for repository prediction accuracy. Published validation in another study does not supply that missing outcome.

## Choose an account for your question

| Read | Evidence role | Our current boundary |
| --- | --- | --- |
| [Githumbi et al. (2022), LandClim II](https://doi.org/10.5194/essd-14-1581-2022) and the [LandClim account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/landclim-paper.md) | Published regional archive and historical reproduction target | Selected author-example parity and an exact-window archive discrepancy; full historical input identity remains open. |
| [Theuerkauf and Couwenberg (2024)](https://doi.org/10.3390/quat7020018) and the [LOVEoptim account](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/loveoptim-paper.md) | Local-inference method and published simulation | Printed parameter correspondence and later source fixtures; no reproduction of the original simulation. |
| [Sugita (2007a)](https://doi.org/10.1177/0959683607075837) and [Sugita (2007b)](https://doi.org/10.1177/0959683607075838) | Regional and local theoretical estimands | Accounts disclose abstract-level original source access; later calculation traces do not reproduce original simulations. |
| [Hellman et al. (2008a)](https://doi.org/10.1002/jqs.1126) and [Hellman et al. (2008b)](https://doi.org/10.1007/s00334-008-0149-7) | Original regional validation and sampling/parameter sensitivity | Full original input/scenario vectors are unavailable here; original findings remain distinct from our figure-label arithmetic. |
| [Gaillard et al. (2010)](https://doi.org/10.5194/cp-6-483-2010) | Carrier of the figure used in our current validation explanation | Nine rounded selected labels from two regional compositions; no full 26-taxon or repository score. |
| [Cui et al. (2014)](https://doi.org/10.1002/ece3.1198) | Potential historical-map vegetation reference | Map support and pollen anchors replay; numerical class fractions are unavailable for a new score. |
| [Tabares et al. (2021)](https://doi.org/10.1177/09596836211003193) | Modern pollen/vegetation reference observations | Complete source-table join and descriptive distances; out-of-domain development, rather than Nordic validation. |

The canonical reports annotate partial primary-text access and precise unsent source/reviewer questions. They preserve numerical differences, invalid compositions and missing outcomes. Actual collaborator comprehension and qualified scientific review remain outstanding.

The [report and presentation downloads](downloads.md) provide all nine canonical
accounts and three audience briefings as source-bound PDFs. Their main text,
tables and diagrams can be read offline; linked external evidence still needs
access to its source.

## Use a result responsibly

Start with the scientific question, then check the [claim-to-evidence index](https://github.com/bijux/bijux-pollenomics/blob/main/reports/evidence-index.md) for exact rows, source identity and producer. Read the corresponding account's unavailable conclusions before selecting a parameter or using a model output. A source-bound numerical test, development prediction and independent vegetation comparison have different acceptance conditions; the current [model-use results](results.md) explain which choices their evidence supports.

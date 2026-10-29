# Neotoma LRA prerequisite review

The [source-bound projection](projection.json) has SHA-256
`26135d91bbe5d729dcca3a1f6f0ea69f5cec4dc00a54a6dd740d5004d4e4b809`.
It retains 10,637 sample-owned chronology review rows and 163 source-site basin
review rows from the corrected Neotoma relational snapshot. Country partitions
are Sweden 5,011 samples/77 sites, Denmark 91/1, Norway 3,544/52, Finland
1,797/28, and unassigned 194/5. The unassigned partition is not a fifth Nordic
country. Every row carries source identity, review status and source locators.

The lakeparameter source capture contains 24,554 rows in verified public API
pages. It was originally bound to a 54-site review with SHA-256
`aaded8ed751a8f245a357c50bb2c2a96a8710168deab7223f0c48284180e96ce`.
The producer verifies that original review and the original capture summary
against the exact page bytes. It then verifies that all 54 original site IDs
remain in the corrected 163-site cohort under the same raw Neotoma snapshot,
and projects the same source pages against the larger cohort. Fourteen native
lakeparameter rows match 13 current sites; 43 sites separately retain a native
site `area` value without an established unit or historical basin meaning.
The source pages came from live offset pagination, not a transactional snapshot;
absence of a row is not certified.

These are review leads. Chronology choice, taxon classification, count support,
PPE/fall-speed binding, justified basin assumptions and qualified returned
decisions remain unresolved. The projection has **zero
accepted samples**, `scientific_acceptance=not_evaluated`, and no executable LRA
request. It does not supersede the separate four-country observed-pollen
prediction study.

## Historical correspondence and a new reconstruction

Reproducing LandClim requires its actual selected chronology, sample membership,
geometry and parameters. A separately declared reconstruction can use a
source-qualified alternative chronology and a justified static basin model.
[Trondman et al. (2016)](https://link.springer.com/article/10.1007/s00334-015-0536-9)
assumed constant present basin size and type where stratigraphic information was
insufficient, with exceptions where evidence supported a change.
[LandClim II](https://essd.copernicus.org/articles/14/1581/2022/) describes several
chronology sources and circular radius approximations. These published choices
support explicit modeling assumptions; they do not authenticate a particular
site's past shoreline or the historical LandClim selection.

A new profile must name its question, physical core and source rows, permitted
use, chronology selection, taxon mask, count support, parameter units, geometry,
pooling and weighting, sensitivity and evaluation target. Missing historical
selection blocks historical correspondence, while a justified alternative can
answer its separately stated question. An interval crossing a time-bin boundary
can contribute to conditional set-based bounds without an invented probability
distribution. Such bounds are distinct from a selected age model and joint
confidence intervals. A common denominator cancels from a fixed-mask normalized
REVEALS point estimate; original counts and taxon eligibility still govern
sampling uncertainty and the reconstructed composition. None of these
distinctions admits the presently unreviewed source rows automatically.

To reproduce, run
`python -m bijux_pollenomics_dev.taxa_review.lra_prerequisites` with the
repository raw root `data/neotoma/raw/neotoma_pollen_dataset_downloads`,
normalized root `data/neotoma/relational`, external capture root
`<external-Neotoma-lakeparameter-capture-root>`, capture
SHA-256 `0c800ed252d6bd2bbed72f5ac7798e27d7a72f89330170b8ce33989384c758fd`,
and a new output path under `artifacts/`. Compare the resulting exact SHA-256
with the governed projection above before reuse. The external capture path is a
local custody location, not a source publication URL.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The prerequisite projection retains 10,637 sample chronology leads and 163 source-site basin review rows without selecting an executable LRA request.

**Unsupported claim.** A necessary count/typed-age candidate or native area value is not an accepted chronology, basin, taxon/PPE/count mask or source right.

**Actual verification performed.** Earlier verification: Read projection denominators, country partitions, review states and lake-parameter join posture; no projection regeneration or model fit. Separately, the maintained current prerequisite producer, lake-source checker and independent source/projection observer each returned native zero on source commit `82c8fc4ed3d847909d14162f51b77dc59ccc0a70`. All 30 raw/normalized inputs were pinned, and the complete 22,907,955-byte projection matched its current governed bytes and typed values: 10,637 necessary source rows, 163 source-site reviews and 14 lake-parameter locator joins. Independent pollen eligibility was not recomputed, and no sample, basin, chronology, source right or model fit was admitted.

**Remaining input or review.** Qualified source-bound chronology, physical core, permitted use, count support, parameters and justified geometry decisions remain.

**Cause category.** Required scientific decisions are deliberately unselected.

**Consequence.** Historical reproduction needs the authentic selected inputs; a new declared reconstruction needs its own justified profile.

**Precise next acceptance route.** Return scoped source/reviewer decisions and freeze an explicit independent reconstruction protocol before building an executable request.

**Negative or refused result.** accepted_samples=0, executable_request=null, scientific_acceptance=not_evaluated; 194 unassigned samples are not a fifth Nordic country.

**Matched denominator.** 10,637 sample rows/163 sites:SE 5,011/77, DK 91/1, NO 3,544/52, FI 1,797/28, unassigned 194/5; 0 accepted.

Qualified authored reader SHA-256: `53cb52c36de696d3090cea07251311248a8df58bdfab5a7bacd9f99837a8a45c`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/lra-prerequisites/projection.json](projection.json) (SHA-256 `26135d91bbe5d729dcca3a1f6f0ea69f5cec4dc00a54a6dd740d5004d4e4b809`).

- [Retained qualification evidence: reports/science/source-cohorts/neotoma-lake-source-custody.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/neotoma-lake-source-custody.json) (SHA-256 `df23f600e89cfd4e285442b5f82480b95521216cad2363f25a91640623953024`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

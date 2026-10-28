# ESSD published-window numerical provenance

The exact 100–350 BP author bin in grids 512 and 562 is paired across the independent author-R replay, installed LRA computation, and pinned PANGAEA 937075 published estimate. The 31 taxon mean and standard-error axes close in each grid (124 numerical values). Fractions from the author-R replay are multiplied by 100 before comparison with published percentage cover.

| Grid | Metric | Maximum absolute R–archive gap (percentage points) | Median absolute gap | Maximum Python–R gap | Largest-gap taxon |
| --- | --- | ---: | ---: | ---: | --- |
| 512 | mean | 9.19787 | 0.0214392 | 1.23800e-11 | Cyperaceae |
| 512 | standard_error | 3.21615 | 0.0114477 | 3.28900e-12 | Cyperaceae |
| 562 | mean | 10.5527 | 0.0322204 | 3.8700e-12 | Calluna.vulgaris |
| 562 | standard_error | 4.25814 | 0.0145312 | 3.42100e-12 | Calluna.vulgaris |

The shared 31-taxon means are summed without renormalization. L1 is the sum of absolute percentage-point gaps across those taxa; total variation is L1/200, and Hellinger uses the nonnegative percentage means divided by 100. Both vectors must sum to 100% within 0.000001 percentage points. These are modeled-product correspondence distances, not vegetation accuracy.

| Grid | Archive mean sum (pp) | Author R mean sum (pp) | Mean L1 gap (pp) | Total variation | Hellinger | Two largest-gap taxa | Share of L1 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| 512 | 100.000000 | 100.000000 | 18.481237 | 0.092406 | 0.078055 | Cyperaceae, Calluna.vulgaris | 0.729 |
| 562 | 100.000000 | 100.000000 | 22.140770 | 0.110704 | 0.101288 | Calluna.vulgaris, Poaceae | 0.940 |

On this author example, the archive difference also appears in the independent R replay; it is not a Python-only numerical discrepancy. The 2016 author-example and June 2021 archive historical raw-input cohorts are not closed as identical. This does not reproduce the 1,128-row published study or evaluate measured vegetation accuracy.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

**Supported claim.** The three-way retained comparison shows that the same large archive discrepancies occur in independent author-R and installed Python results on the exact shared window; R/Python source parity remains much tighter than archive differences.

**Unsupported claim.** This is not authentication of historical count cohorts, a resolved archive producer, measured vegetation accuracy, a statistical test, complete publication reproduction or independent ecological confirmation.

**Actual verification performed.** The generated residual and compositional-distance summary was inspected against its governed ledger/report. Retained means close to 100% within 1e-6 pp without renormalization; L 1,total variation and Hellinger use their declared percentage scales. This qualification performs no R/native model, fresh numerical comparison or inferred historical execution.

**Remaining input or review.** Historical production source revisions, selected members, chronology, weighting and classification remain unclosed; cross-version dependence and original covariance are unknown. Source-use rights, independent measured vegetation and qualified review remain separate.

**Cause category.** data | comparability | assumption | qualified review

**Consequence.** The archive gap is not explained as a Python-only implementation error. Keep modeled-product distances descriptive and avoid turning shared author lineage into independent biological corroboration.

**Precise next acceptance route.** Obtain authenticated production inputs and transformation for one named archive grid/window; replay exact source membership and units with all residuals preserved. Assess ecological accuracy only against a separately admitted measured reference.

**Negative or refused result.** AuthorR-to-archive maximum mean gaps 9.19787/10.5527 pp and SE 3.21615/4.25814 pp remain. Grid total variations 0.092406/0.110704 and Hellinger 0.078055/0.101288 describe modeled products; no historical cohort identity or accuracy follows.

**Matched denominator.** One 100–350 BP interval,two grids,31 taxa,mean+SE =124 paired values. Mean L 1 gaps 18.481237/22.140770 pp; grid 512 six andgrid 562 five active author sites. The rest of 25 windows and 1,128 historical records are outside this exact comparison.

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-provenance/report.json](report.json) (SHA-256 `f188d1d0277fbfed1c4c2f8b28ade15c1fcef5c4d6e881af85ea1c8c7d748f6c`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-published-window-provenance/paper-correspondence.csv](paper-correspondence.csv) (SHA-256 `dfecc6d9a36f4f458e2d09a05f4764cb138e42df39f39e646c528025bdc07eb0`).

- [Canonical scientific account: reports/science/publication-correspondence/published-window-provenance.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence/published-window-provenance.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

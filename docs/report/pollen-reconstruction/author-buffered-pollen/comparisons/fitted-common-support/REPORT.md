# Buffered observed-pollen fitted and fixed comparison

All four methods use the same author-prepared 31-taxon counts, 17 site IDs, two adjacent withheld grids and 20 km basin-edge buffer. Scores are paired only where every method produced a prediction; each site has equal weight after its bins are averaged. Model-specific coverage and refusal reasons remain in report.json.

140 of 184 observed site bins are common to all four methods.

| Method | Scored bins (own) | Common-site MAE | Common-site TV | MAE minus training mean |
| --- | ---: | ---: | ---: | ---: |
| training_mean | 148 | 0.025298 | 0.392124 | +0.000000 |
| nearest_site | 148 | 0.025347 | 0.392878 | +0.000049 |
| inverse_distance_squared | 148 | 0.025206 | 0.390691 | -0.000092 |
| clr_rbf_ridge_half_count | 140 | 0.040564 | 0.628745 | +0.015266 |

This fixed fitted configuration is a development diagnostic. Its zero replacement, length scale rule and ridge penalty were declared before scoring; these outer-block results do not select a model. The author-prepared English pollen cohort is not a source-complete Swedish LRA cohort or measured vegetation reference.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** Four fixed methods are compared only on their shared 140 scored site-bins, retaining method-specific coverage. The half-count CLR/RBF fit is poorer than training mean on this support.

**Unsupported claim.** Untouched confirmation, Swedish LRA vegetation reconstruction, independently measured vegetation accuracy, general long-distance transfer skill, calibrated spatial confidence intervals or cleared publication/redistribution rights.

**Actual verification performed.** This qualification reads the exact retained report JSON, reader text and family source/producer manifest. It does not rerun predictions, fitting, scoring or private source acquisition, and supplies no independent numerical or human review. The retained scores concern author-prepared observed pollen, not measured vegetation.

**Remaining input or review.** The 20 km basin-edge rule does not independently close pollen-source footprints or cross-database aliases. Two adjacent previously exposed English blocks do not establish independent transfer uncertainty. Full raw-core grain denominators, matched vegetation observations, intended-use rights and qualified scientific review remain unbound.

**Cause category.** data | assumption | comparability | access/rights | qualified review

**Consequence.** Read these observed-pollen outcomes as descriptive development evidence on their stated support. Do not convert their errors or source identity into vegetation, LRA, independent confirmation or general-transfer accuracy.

**Precise next acceptance route.** For a new general-transfer claim, qualify source identity/footprints/aliases, raw denominators and rights, then freeze a development-selected protocol before scoring genuinely untouched independent spatial groups. A vegetation/LRA claim additionally needs admitted basin/chronology/taxon support and independently matched vegetation truth; obtain qualified review of that exact estimand.

**Negative or refused result.** Fitted site-macro MAE 0.040564 exceeds training mean 0.025298 by 0.015266 fraction; nearest site also has positive difference+0.000049. All 44 fitted exclusions remain and are not scored zeros.

**Matched denominator.** 17 common English sites;2 adjacent withheld grids;31 taxa;140/184 observed site-bins shared by 4 methods. Each fixed baseline scores 148 bins; fitted method 140. Fitted refusals are 36 without same-bin training plus 8 requiring two training sites.

Qualified authored reader SHA-256: `6c8eab1a9ff11367dd701c6ecf52d1d20a761827f06c9e12342671ee35c86534`.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/manifest.json](../../manifest.json) (SHA-256 `6ea5f219f9bc1d3878ef50ff831d3eb95f7d4d6293dd61ce34e6e5c442412026`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/comparisons/fitted-common-support/report.json](report.json) (SHA-256 `8c9d218fd294cfbe485a153d1e635f953146e408bd5aa31321e2cf1b4036754a`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

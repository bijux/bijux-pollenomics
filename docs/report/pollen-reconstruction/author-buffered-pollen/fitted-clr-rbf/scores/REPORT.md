# Buffered adjacent-grid pollen prediction

Two one-degree author grids are withheld in turn. Prediction reads only the opposite grid's count tables and predicts each author bin with clr_wgs84_rbf_ridge_half_count_31_taxon_observed_pollen_fraction_by_bin. A training basin must be at least 20 km from every target basin after subtracting both reported basin radii. The independently reopened target counts are scored afterward.

Across 17 author site IDs and 2 adjacent blocks, 184 site-bin targets have observed counts, 140 are scored and 44 lack the declared fit support ({'no_training_site_same_bin': 36, 'fitted_model_requires_two_training_sites': 8, 'no_positive_training_distance': 0}). Site-macro MAE is 0.040564 fractions; site-macro total variation is 0.628745. On 140 site bins scored by both methods, the site-macro MAE is 0.040564 for the buffered block holdout and 0.019955 for the retained within-grid site holdout. This paired difference is descriptive development evidence; coverage differs between methods.

The fitted model adds 0.5 to every named training taxon count before CLR closure, uses a per-bin median positive training-centre distance scale and ridge penalty 0.01. No target count enters fitting; the zero policy and scale rule were declared before scoring.

This is a development comparison on author-prepared pollen, not a Swedish cohort, LRA vegetation reconstruction, or measured vegetation accuracy. The 20 km basin-edge buffer is a declared diagnostic rule; the broader pollen source footprints and cross-database site aliases are not independently closed. Two adjacent blocks cannot establish general spatial-transfer uncertainty. Author-prepared 31-taxon counts do not certify a full raw-core pollen denominator or publication rights.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** The fixed half-count CLR/RBF ridge prediction uses eligible opposite-grid counts under the declared 20 km basin-edge split; held-out target counts are scored afterward. Retained site-macro MAE is 0.040564 fraction on its stated support.

**Unsupported claim.** Untouched confirmation, Swedish LRA vegetation reconstruction, independently measured vegetation accuracy, general long-distance transfer skill, calibrated spatial confidence intervals or cleared publication/redistribution rights.

**Actual verification performed.** This qualification reads the exact retained report JSON, reader text and family source/producer manifest. It does not rerun predictions, fitting, scoring or private source acquisition, and supplies no independent numerical or human review. The retained scores concern author-prepared observed pollen, not measured vegetation.

**Remaining input or review.** The 20 km basin-edge rule does not independently close pollen-source footprints or cross-database aliases. Two adjacent previously exposed English blocks do not establish independent transfer uncertainty. Full raw-core grain denominators, matched vegetation observations, intended-use rights and qualified scientific review remain unbound.

**Cause category.** data | assumption | comparability | access/rights | qualified review

**Consequence.** Read these observed-pollen outcomes as descriptive development evidence on their stated support. Do not convert their errors or source identity into vegetation, LRA, independent confirmation or general-transfer accuracy.

**Precise next acceptance route.** For a new general-transfer claim, qualify source identity/footprints/aliases, raw denominators and rights, then freeze a development-selected protocol before scoring genuinely untouched independent spatial groups. A vegetation/LRA claim additionally needs admitted basin/chronology/taxon support and independently matched vegetation truth; obtain qualified review of that exact estimand.

**Negative or refused result.** Buffered MAE 0.040564 is poorer than retained within-grid MAE 0.019955 on matched support. The fixed CLR fit also has lower coverage than all 3 baselines and is poorer than the training baseline on the 140-bin common support.

**Matched denominator.** 17 English author sites;2 adjacent outer blocks;31-taxon prepared axis;140/184 observed site-bins scored out of 425 possible site-bins. 44 refusals=36 with no same-bin training+8 with fewer than 2 training sites;0 no-positive-distance refusals. The within-grid comparison pairs only the same 140 bins; sites, not all bins pooled, receive equal weight.

Qualified authored reader SHA-256: `3b822cfad5c39cac9d12ed70859e17e6d967f1d5323d7ec33526757254e9df9c`.

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/manifest.json](../../manifest.json) (SHA-256 `5b243b240ba16b3523fe679aed97860e506a15bbf781c84a215b22e9edca3c60`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/fitted-clr-rbf/scores/report.json](report.json) (SHA-256 `a2b883dfac3732d30d7c02d53e5c19309093fc26f24a244828d0955d5f82790f`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/author-buffered-pollen/fitted-clr-rbf/scores/scores.csv](scores.csv) (SHA-256 `1d8e737b7e41d0e390beee8d3916e8f087713ebbcf9096f8493a92e1fd2db828`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

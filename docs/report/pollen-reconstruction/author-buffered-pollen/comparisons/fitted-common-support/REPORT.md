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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

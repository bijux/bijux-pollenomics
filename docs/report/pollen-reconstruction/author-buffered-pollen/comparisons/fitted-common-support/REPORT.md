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

# Buffered adjacent-grid pollen baseline comparison

The same 17 English author site IDs form two withheld one-degree grids. Training sites must satisfy the frozen 20 km basin-edge buffer. All three methods score the same 148 of 184 observed site bins; 36 lack a buffered training site in the corresponding bin.

| Method | Site-macro MAE (fraction) | Site-macro total variation | MAE minus training mean |
| --- | ---: | ---: | ---: |
| training_mean | 0.025303 | 0.392194 | +0.000000 |
| nearest_site | 0.025285 | 0.391916 | -0.000018 |
| inverse_distance_squared | 0.025217 | 0.390867 | -0.000086 |

These are descriptive author-prepared observed-pollen predictions from two adjacent English grids. The fixed distance exponent and buffer were not tuned on these outcomes. This result does not establish Swedish LRA skill, long-distance transfer, independent vegetation accuracy, or publication-ready source rights.

# Buffered adjacent-grid pollen baseline comparison

The same 17 English author site IDs form two withheld one-degree grids. Training sites must satisfy the frozen 20 km basin-edge buffer. All three methods score the same 148 of 184 observed site bins; 36 lack a buffered training site in the corresponding bin.

| Method | Site-macro MAE (fraction) | Site-macro total variation | MAE minus training mean |
| --- | ---: | ---: | ---: |
| training_mean | 0.025303 | 0.392194 | +0.000000 |
| nearest_site | 0.025285 | 0.391916 | -0.000018 |
| inverse_distance_squared | 0.025217 | 0.390867 | -0.000086 |

Block means give each site equal weight within its grid. Differences are paired against the training mean on the same scored bins; negative values indicate lower error.

| Grid | Sites | Scored / observed bins | Nearest-site MAE difference | Inverse-distance MAE difference |
| --- | ---: | ---: | ---: | ---: |
| 512 | 9 | 69 / 97 | +0.000271 | -0.000176 |
| 562 | 8 | 79 / 87 | -0.000343 | +0.000016 |

| Grid | Site | Scored / observed bins | Nearest training basin edge (km) | Nearest-site MAE difference | Inverse-distance MAE difference |
| --- | --- | ---: | ---: | ---: | ---: |
| 562 | BECKHAM | 11 / 11 | 59.3 | -0.000400 | -0.000051 |
| 512 | BROADOWN | 11 / 17 | 57.1 | -0.000243 | -0.000186 |
| 562 | COMERSLA | 15 / 16 | 52.7 | +0.000077 | +0.000137 |
| 512 | CUTHILL2 | 8 / 13 | 55.8 | -0.000131 | -0.000161 |
| 562 | EXEBRID | 3 / 10 | 50.6 | +0.001115 | +0.000037 |
| 562 | GOURTEMIRES | 9 / 9 | 48.4 | +0.001284 | +0.000059 |
| 512 | HANGINGS | 11 / 17 | 52.5 | +0.001672 | -0.000055 |
| 512 | HARESDOWN | 7 / 7 | 20.1 | +0.000980 | -0.000209 |
| 562 | LARKBARR | 9 / 9 | 60.2 | -0.003124 | -0.000093 |
| 512 | LOBBSBOG | 7 / 7 | 21.6 | +0.000460 | -0.000235 |
| 562 | LONGBREACH | 15 / 15 | 49.4 | +0.000108 | +0.000073 |
| 562 | MOLECHAM | 7 / 7 | 54.5 | -0.002115 | -0.000058 |
| 562 | NTWITCHEN | 10 / 10 | 52.5 | +0.000310 | +0.000023 |
| 512 | WHH05 | 4 / 8 | 52.7 | -0.000629 | -0.000032 |
| 512 | WHH11 | 4 / 4 | 52.7 | +0.002242 | -0.000152 |
| 512 | WINDMILL | 7 / 7 | 20.8 | -0.001073 | -0.000227 |
| 512 | WINNEYS | 10 / 17 | 55.7 | -0.000838 | -0.000326 |

nearest_site has lower / equal / higher site MAE at 8 / 0 / 9 sites relative to the training mean.

inverse_distance_squared has lower / equal / higher site MAE at 12 / 0 / 5 sites relative to the training mean.

Taxon errors below are site-macro absolute fractions on the same 148 site bins. Signed differences compare each method with the training mean; all 31 taxa and signed prediction bias are in report.json. Taxon ranks are descriptive and were inspected after outer scoring.

| Taxon | Training mean error | Nearest-site difference | Inverse-distance difference |
| --- | ---: | ---: | ---: |
| Poaceae | 0.186685 | +0.003969 | +0.000152 |
| Cyperaceae | 0.137440 | +0.005387 | -0.000849 |
| Calluna vulgaris | 0.136179 | -0.016798 | +0.000439 |
| Corylus avellana | 0.120266 | -0.000864 | -0.000952 |
| Alnus glutinosa | 0.051489 | +0.005792 | -0.000943 |
| Betula | 0.038899 | -0.009799 | -0.001345 |
| Quercus deciduous | 0.037812 | +0.020077 | +0.001115 |
| Salix | 0.017100 | -0.004648 | +0.000034 |
| Plantago lanceolata type | 0.011845 | +0.001945 | +0.000057 |
| Filipendula | 0.010321 | -0.004702 | -0.000198 |

These are descriptive author-prepared observed-pollen predictions from only two adjacent English grids. Per-site bins are correlated, so no confidence interval or model selection is inferred from them. The fixed distance exponent and buffer were not tuned on these outcomes. This result does not establish Swedish LRA skill, long-distance transfer, independent vegetation accuracy, or publication-ready source rights.

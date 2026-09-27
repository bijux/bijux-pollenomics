# Nordic country-held-out direct-pollen predictions

This is a prior-exposed exploratory prediction of a closed 16-label, exact-name Neotoma pollen subcomposition. It predicts observed pollen composition; it is not an LRA reconstruction, measured vegetation estimate, or confirmatory test.

The entire target country is omitted from each prediction's training set. Finland is one physical site group and Norway has 14; all Swedish training groups are the three previously admitted Neotoma sites. Targets use sample-owned Neotoma ages and site coordinates only. Prediction files are saved and hashed before the scoring command reads held-out count profiles.

The fixed methods are training mean, nearest site, inverse-distance-squared, and the existing CLR/WGS84 RBF-ridge (half-count smoothing on training cells, median positive training-distance scale, ridge 0.01). They are comparisons, not a Nordic-tuned winner search. No target-country outcome is used to choose taxa: the 16 literal labels are inherited from the earlier Swedish direct-pollen cohort.

The exact axis is a closed subcomposition. A missing literal Neotoma NISP row is treated as an unreported zero cell under the documented Neotoma count-matrix workflow. All remaining pollen labels are outside the response and are not interpreted as absent vegetation. Coordinates for source polygon geometries use their WGS84 geometric centroids; source point geometries are retained as points.

| Held-out country | Candidate samples | Candidate sites | Candidate bins | Positive 16-label bins | Predicted bins | Scored bins | Refused bins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FI | 127 | 1 | 2 | 2 | 2 | 2 | 0 |
| NO | 921 | 14 | 249 | 248 | 154 | 154 | 95 |

Denmark has 279 samples in the same retained screen but 0 agreeing-pollen/count plus comparable-age candidate samples; no country-held-out prediction was eligible.

| Country | Method | Attempted predictions | Scored bins | Scored sites | Site-macro MAE | Site-macro Hellinger |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| FI | training_mean | 2 | 2 | 1 | 0.085853 | 0.655921 |
| FI | nearest_site | 2 | 2 | 1 | 0.024404 | 0.352884 |
| FI | inverse_distance_squared | 2 | 2 | 1 | 0.072422 | 0.589167 |
| FI | clr_rbf_ridge | 2 | 2 | 1 | 0.079572 | 0.609858 |
| NO | training_mean | 154 | 154 | 12 | 0.055197 | 0.451704 |
| NO | nearest_site | 154 | 154 | 12 | 0.046873 | 0.402600 |
| NO | inverse_distance_squared | 154 | 154 | 12 | 0.047481 | 0.408829 |
| NO | clr_rbf_ridge | 154 | 154 | 12 | 0.049218 | 0.417336 |

Site-macro scores average bins within each physical site and then weight sites equally within country. The single Finnish site cannot estimate between-site Finnish variation. Country-held-out scores are descriptive transfer results from this captured EPD subset, not evidence for all Nordic landscapes or all time periods. `coverage.csv` retains site-level age/count candidate bins and separates positive closed-axis outcomes, predicted bins, scored bins, empty/refused target outcomes, and eligible bins without a prediction.

## Source and limits

The Norwegian and Finnish candidates and the Swedish training cohorts come from European Pollen Database datasets distributed through Neotoma. The [Neotoma source review](../../../../public/pollenomics-data/sources/neotoma.md) records EPD reuse under CC BY 4.0 with Neotoma, EPD, and original investigator attribution. Dataset identifiers, DOIs, and contributors are retained in `cohort.csv` and `training-sources.csv`. No PPE, fall-speed, basin-area, or vegetation-reference assumption is needed for observed-pollen prediction; those inputs remain blocked for LRA and measured-vegetation claims.

All candidates have one source-owned comparable sample-age claim in the retained snapshot. Norway contains both calibrated radiocarbon years BP and calendar years BP, which share the BP calendar reference but retain their distinct source labels in the input profile. Finland candidates are calendar years BP. Chronology uncertainty bounds are not supplied. Fixed 500-year bins are an exploratory alignment choice.

Target bins lacking two positive-count training sites, bins with no positive count on the fixed 16-label axis, and predictions without target outcomes remain unscored; the CSV files retain the actual prediction and scoring denominators. Spatial coordinates from polygon geometry centroids are approximate source locations. No independent vegetation truth was used.

## Reproduction

From the repository root, run `PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src .venv/bin/python -m bijux_pollenomics_dev.source_completion.nordic_direct_pollen prepare --relational-root data/neotoma/relational --raw-root data/neotoma/raw/neotoma_pollen_dataset_downloads --workdir artifacts/nordic-direct-pollen`, then run `predict` separately for `NO` and `FI`, then run `score` with `--relational-root data/neotoma/relational --workdir artifacts/nordic-direct-pollen --publish-dir docs/report/regions/nordic/direct-pollen`. The prediction commands do not read the held-out outcome inputs. Input and prediction hashes are retained in `manifest.json`.

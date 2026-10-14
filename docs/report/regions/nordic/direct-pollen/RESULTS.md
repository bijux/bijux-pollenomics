# Nordic country-held-out direct-pollen predictions

This is a prior-exposed exploratory prediction of a closed 16-label, exact-name Neotoma pollen subcomposition. It predicts observed pollen composition; it is not an LRA reconstruction, measured vegetation estimate, or confirmatory test.

The entire target country is omitted from each prediction's training set. Denmark, Finland and Norway contribute the source-backed physical site groups counted below; Sweden contributes the three previously admitted Neotoma training sites. Targets use selected sample-owned Neotoma ages and site coordinates only. Prediction files are saved and hashed before the scoring command reads held-out count profiles.

The fixed methods are training mean, nearest site, inverse-distance-squared, and the existing CLR/WGS84 RBF-ridge (half-count smoothing on training cells, median positive training-distance scale, ridge 0.01). They are comparisons, not a Nordic-tuned winner search. No target-country outcome is used to choose taxa: the 16 literal labels are inherited from the earlier Swedish direct-pollen cohort.

The exact axis is a closed subcomposition. A missing literal Neotoma NISP row is treated as an unreported zero cell under the documented Neotoma count-matrix workflow. All remaining pollen labels are outside the response and are not interpreted as absent vegetation. Coordinates for source polygon geometries use their WGS84 geometric centroids; source point geometries are retained as points.

| Held-out country | Candidate samples | Candidate sites | Candidate bins | Positive 16-label bins | Predicted bins | Scored bins | Refused bins |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DK | 91 | 1 | 24 | 24 | 24 | 24 | 0 |
| FI | 1797 | 28 | 435 | 435 | 435 | 435 | 0 |
| NO | 3544 | 52 | 1178 | 1177 | 1084 | 1084 | 94 |

| Country | Method | Attempted predictions | Scored bins | Scored sites | Site-macro MAE | Site-macro Hellinger |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| DK | training_mean | 24 | 24 | 1 | 0.037484 | 0.423937 |
| DK | nearest_site | 24 | 24 | 1 | 0.029809 | 0.353519 |
| DK | inverse_distance_squared | 24 | 24 | 1 | 0.033022 | 0.387704 |
| DK | clr_rbf_ridge | 24 | 24 | 1 | 0.039220 | 0.393744 |
| FI | training_mean | 435 | 435 | 28 | 0.038799 | 0.338505 |
| FI | nearest_site | 435 | 435 | 28 | 0.033223 | 0.289538 |
| FI | inverse_distance_squared | 435 | 435 | 28 | 0.034375 | 0.306323 |
| FI | clr_rbf_ridge | 435 | 435 | 28 | 0.082477 | 0.620855 |
| NO | training_mean | 1084 | 1084 | 52 | 0.030190 | 0.287670 |
| NO | nearest_site | 1084 | 1084 | 52 | 0.032280 | 0.327944 |
| NO | inverse_distance_squared | 1084 | 1084 | 52 | 0.027012 | 0.260268 |
| NO | clr_rbf_ridge | 1084 | 1084 | 52 | 0.034496 | 0.323876 |

Site-macro scores average bins within each physical site and then weight sites equally within country. Denmark has one physical site group and cannot estimate between-site Danish variation. Country-held-out scores are descriptive transfer results from this captured EPD subset, not evidence for all Nordic landscapes or all time periods. `coverage.csv` retains site-level age/count candidate bins and separates positive closed-axis outcomes, predicted bins, scored bins, empty/refused target outcomes, and eligible bins without a prediction.

## Source and limits

The Danish, Finnish, Norwegian and Swedish cohorts come from European Pollen Database datasets distributed through Neotoma. The [Neotoma source review](../../../../public/pollenomics-data/sources/neotoma.md) records EPD reuse under CC BY 4.0 with Neotoma, EPD, and original investigator attribution. Dataset identifiers, DOIs, and contributors are retained in `cohort.csv` and `training-sources.csv`. No PPE, fall-speed, basin-area, or vegetation-reference assumption is needed for observed-pollen prediction; those inputs remain blocked for LRA and measured-vegetation claims.

All selected candidates have one source-owned comparable sample-age claim after the declared chronology rule: when several comparable claims exist, use the unique source-flagged default for its age type; otherwise refuse the sample. Neotoma permits one default chronology per age type, so a radiocarbon and a calibrated chronology can both be flagged without contradicting each other ([Neotoma chronology manual](https://open.neotomadb.org/manual/chronology-age-related-tables-1.html)). The corrected source projection removes false cross-age-type conflicts while retaining genuine same-age-type conflicts. Sample age type labels remain in the input profiles. Source uncertainty bounds vary by record and are not propagated into the exploratory fixed 500-year bins.

Target bins lacking two positive-count training sites, bins with no positive count on the fixed 16-label axis, and predictions without target outcomes remain unscored; the CSV files retain the actual prediction and scoring denominators. Spatial coordinates from polygon geometry centroids are approximate source locations. No independent vegetation truth was used.

## Reproduction

From the repository root, run `PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src .venv/bin/python -m bijux_pollenomics_dev.source_completion.nordic_direct_pollen prepare --relational-root data/neotoma/relational --raw-root data/neotoma/raw/neotoma_pollen_dataset_downloads --workdir artifacts/nordic-direct-pollen`, then run `predict` separately for `DK`, `FI` and `NO`, then run `score` with `--relational-root data/neotoma/relational --workdir artifacts/nordic-direct-pollen --publish-dir docs/report/regions/nordic/direct-pollen`. The prediction commands do not read the held-out outcome inputs. Input and prediction hashes are retained in `manifest.json`.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained prior-exposed country-held-out study predicts a closed16literal-label observed-pollen response using four fixed methods with target-country exclusion and separate prediction/scoring reads.

**Unsupported claim.** Pollen prediction is not LRA vegetation reconstruction, measured-vegetation validation, confirmatory testing or a claim about all Nordic landscapes and periods.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer.

**Remaining input or review.** Physical LRA parameters/geometry and independent vegetation truth remain absent; sample chronology uncertainty is not propagated by fixed point-age bins.

**Cause category.** Exposed descriptive geographic transfer on a fixed pollen subcomposition.

**Consequence.** Site-macro scores weight physical sites equally and cannot supply between-site Danish uncertainty from one site or ecological meaning to outside-axis counts.

**Precise next acceptance route.** Replay the named prepare/predict/score stages with target-country exclusion and retained refusals, and qualify any new untouched target with its own frozen protocol before examining outcomes.

**Negative or refused result.** Norway retains94unscored candidate bins, including empty outcome or insufficient-support cases; outside-axis labels are not interpreted as absent vegetation.

**Matched denominator.** DK91samples/1site/24scored bins;FI1,797/28/435;NO3,544/52/1,084scored of1,178candidate bins. Four methods share the same selected16-label response.

Qualified authored reader SHA-256: `be05e7fdaf846dfb1f049964cd72e64975b7e04f7d40858c75d876bcb4adcff4`.

- [Retained qualification evidence: docs/report/regions/nordic/direct-pollen/manifest.json](manifest.json) (SHA-256 `43ec4aa62c1c93c0b3af0da2733706eb68a9685bd3f37b18a3041d22e7382573`).

- [Retained qualification evidence: docs/report/regions/nordic/direct-pollen/scores.csv](scores.csv) (SHA-256 `b85963e3b2e0386541dfcebf0e14530571d1bcc22f630f0720e43592e44ef2d8`).

- [Retained qualification evidence: docs/report/regions/nordic/direct-pollen/coverage.csv](coverage.csv) (SHA-256 `634a78011031e180290304d9843e42a36e3d59c24f4a1c396b41dcf7a96df9a1`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

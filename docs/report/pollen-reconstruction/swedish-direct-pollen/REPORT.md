# Swedish Neotoma direct-pollen prediction

This is a prior-exposed exploratory whole-site-held-out prediction of a declared 16-taxon exact-name pollen subcomposition. It is a statistical observed-pollen comparison, not REVEALS/LOVE, an LRA result, a vegetation-accuracy estimate, or a confirmatory test.

The three independent Neotoma site IDs are held out one at a time. At each of 13 shared 500 calibrated-BP bins, the target coordinate is allowed and its pollen counts are omitted from that fold's prediction job. The prediction file is saved and hashed before the separate scoring job opens its target count profile. The fixed candidates are training mean, nearest site, inverse-distance-squared, and the existing CLR/WGS84 RBF-ridge with half-count replacement on training cells only, median positive training distance and ridge 0.01. No candidate selection uses these outcomes.

Missing Neotoma NISP rows are interpreted as zero cells in the count matrix following the [documented Neotoma workflow](https://open.neotomadb.org/Current_Workshop/simple_workflow.html), which uses `pivot_wider(..., values_fill = 0)` for count matrices. The response is closed over the 16 exact taxon labels present in all three native inventories, without a taxon crosswalk. Those taxa contain 45–57% of each site's recorded NISP; all excluded labels/counts are enumerated in `exclusions.csv`. Scores apply only to this subcomposition.

All four candidates cover the same 39 held-out site-bin targets. Site-macro scores average bins within each lake and then weight the three lakes equally. With three sites, aggregate uncertainty/generalization claims are limited. The two southern sites are close to each other while Abborrtjärnen is much farther north; this is an extremely small and geographically unbalanced test.

| Candidate | Attempted | Scored | Site-macro MAE (fraction) | Site-macro Hellinger |
|---|---:|---:|---:|---:|
| training_mean | 39 | 39 | 0.057177 | 0.406399 |
| nearest_site | 39 | 39 | 0.055371 | 0.395725 |
| inverse_distance_squared | 39 | 39 | 0.060032 | 0.418512 |
| clr_rbf_ridge | 39 | 39 | 0.059476 | 0.413601 |

## Source and readiness

The [EPD policy](https://epdweblog.org/epd_data_home/epd_policy/) states that EPD data available through Neotoma may be reused under CC BY 4.0 with Neotoma, EPD, and original investigator attribution. Dataset DOIs and contributor names are retained in `cohort.csv`. The direct-pollen channel is eligible under that rule. Separate LRA readiness remains false because source-backed basin geometry/radius, PPE, fall speeds and dispersal choices have not been admitted. No vegetation reference was opened or used.

Native ages are sample-owned calibrated radiocarbon years BP under one Neotoma chronology ID per dataset; sample older/younger uncertainty bounds are null. Fixed 500-year bins are an exploratory aggregation choice. The existing question bundle remains relevant to Rootsi workbook age labels, rights and workbook-to-Neotoma relationships; it does not block this Neotoma-only prediction.

### Exact-name LandClim II parameter intersection

The [published LandClim II parameter table](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv) has six literal names among this study's 16 closed labels. Its source fall speeds and pollen productivity estimates are:

| Native label | Fall speed (m/s) | PPE (SD) |
| --- | ---: | ---: |
| Betula | 0.024 | 5.106 (0.303) |
| Ulmus | 0.032 | 1.27 (0.05) |
| Salix | 0.022 | 1.182 (0.077) |
| Cyperaceae | 0.035 | 0.962 (0.05) |
| Filipendula | 0.006 | 3 (0.285) |
| Plantago lanceolata | 0.029 | 2.33 (0.201) |

Summing only these six labels in the prepared site bins yields
50,208/129,750 native NISP at [Abborrtjärnen](prepared/dataset-19913.json)
(38.7%), 12,456/68,668 at [Bussjösjön](prepared/dataset-53995.json)
(18.1%) and 11,102/42,548 at [Bökesjön](prepared/dataset-54001.json)
(26.1%). These figures are a bounded exact-name support diagnostic. They do
not authorize an LRA fit, identify a historical basin edge or define a complete
vegetation denominator. The separate [author parameter binding](../../source-relations/neotoma/author-parameter-binding/README.md)
concerns a different 31-target lookup and is not interchangeable with this
six-name intersection.

## Reproduction

The source and configuration hashes are recorded in `input-manifest.json`. From the repository root, reproduce into a new local output directory with `.venv/bin/python -m bijux_pollenomics_dev.source_completion.swedish_direct_pollen prepare --data-root data/neotoma/raw/neotoma_pollen_dataset_downloads --workdir artifacts/swedish-direct-pollen --config docs/report/pollen-reconstruction/swedish-direct-pollen/config.json`; run `predict --target-dataset-id 19913`, `53995`, and `54001` with the same workdir and config; then run `score --workdir artifacts/swedish-direct-pollen`. The source files are EPD datasets accessed through Neotoma and identified by DOI and contributors in `cohort.csv`. The tracked cohort, prepared site profiles, frozen predictions, score tables and exclusion rows in this directory preserve the published result independently of that local output directory.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-bound conditional reconstruction or exposed pollen development wrapper; own source assumptions and exact scored/refused populations must be preserved alongside account links.

**Supported claim.** Four fixed statistical predictors compare a closed 16-label observed-pollen response under whole-physical-site holdout; all score the same 39 targets. Nearest-site site-macro MAE 0.055371 fraction is the smallest retained development mean, without selecting a new model.

**Unsupported claim.** REVEALS/LOVE or LRA reconstruction, measured vegetation accuracy, untouched confirmation, full pollen-assemblage coverage, a closed raw-core grain denominator or generalized spatial uncertainty.

**Actual verification performed.** The source reader, configuration/input manifest, score and exclusion outputs were inspected. The retained workflow saves/hashes predictions before a separate job opens target counts and applies half-count replacement only to CLR training cells. This qualification runs no predictions or scoring and supplies no independent numerical oracle.

**Remaining input or review.** The 3 lakes are very small and geographically unbalanced support; all outcomes were previously exposed. Missing native NISP cells are interpreted as zero under the stated matrix workflow, not observed taxon absence. Sample age bounds are null; basin/PPE/fall-speed/dispersal admission and independent vegetation truth remain separate from public direct-pollen use.

**Cause category.** data | assumption | comparability | qualified review

**Consequence.** Keep scores within the 16-label subcomposition and declared point bins. The six-name public parameter intersection is a separate support diagnostic and cannot authorize LRA or transfer the 31-author-target response denominator.

**Precise next acceptance route.** Qualify missing-cell/age/bin and source-group assumptions, freeze a new evaluation on previously unexposed physical groups, and retain all excluded labels. Admit time-matched basin/transport/PPE and measured vegetation separately before LRA or ecological accuracy claims.

**Negative or refused result.** All 39 targets are scored but inverse-distance and CLR means are poorer than the training mean. The 16-label response retains only about 45–57% of each site’s reported NISP. The 6-name parameter subset retains 50,208/129,750,12,456/68,668 and 11,102/42,548 grains; missing age bounds and LRA readiness remain unresolved.

**Matched denominator.** 3 native physical lakes and 228 source samples;13 shared 500-calibrated-BP bins ×3 sites =39 targets for each of 4 methods;16 exact labels. Scores average within site then give 3 sites equal weight. These are distinct from the later 31-target country response and its all-bin support.

Qualified authored reader SHA-256: `dbc126e485a0b975cdd8c1341345887882210ee56f32b8ba64df79f6a95e6a36`.

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-direct-pollen/config.json](config.json) (SHA-256 `9e330aec087180acb11638f544e773f53b6ffc1444da4e4d9840e53ad1849fd0`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-direct-pollen/input-manifest.json](input-manifest.json) (SHA-256 `7fd3e2a94aecbc99c23df84f888368cf23dba42121eba92b1c4eb582ae4a991f`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-direct-pollen/scores.csv](scores.csv) (SHA-256 `3ac45ac3f764ce3784b0d6afb36fe5217d56d8670cbab19a3bb9e6df8ada439b`).

- [Retained qualification evidence: docs/report/pollen-reconstruction/swedish-direct-pollen/exclusions.csv](exclusions.csv) (SHA-256 `f12714ca2532842a5248d86f27efcc0ea8f48d736ce7b2f4aee243590b78f26e`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

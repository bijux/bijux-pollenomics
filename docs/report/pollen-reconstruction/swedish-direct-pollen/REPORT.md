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

The [published LandClim II parameter table](../../../../data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv) has six literal names among this study's 16 closed labels. Its source fall speeds and pollen productivity estimates are:

| Native label | Fall speed (m/s) | PPE (SD) |
| --- | ---: | ---: |
| Betula | 0.024 | 5.106 (0.303) |
| Ulmus | 0.032 | 1.27 (0.05) |
| Salix | 0.022 | 1.182 (0.077) |
| Cyperaceae | 0.035 | 0.962 (0.05) |
| Filipendula | 0.006 | 3 (0.285) |
| Plantago lanceolata | 0.029 | 2.33 (0.201) |

Summing only these six labels in the [prepared site bins](prepared/) yields 50,208/129,750 native NISP at Abborrtjärnen (38.7%), 12,456/68,668 at Bussjösjön (18.1%) and 11,102/42,548 at Bökesjön (26.1%). These figures are a bounded exact-name support diagnostic. They do not authorize an LRA fit, identify a historical basin edge or define a complete vegetation denominator. The separate [author parameter binding](../../source-relations/neotoma/author-parameter-binding/README.md) concerns a different 31-target lookup and is not interchangeable with this six-name intersection.

## Reproduction

The source and configuration hashes are recorded in `input-manifest.json`. From the repository root, reproduce into a new local output directory with `.venv/bin/python -m bijux_pollenomics_dev.source_completion.swedish_direct_pollen prepare --data-root data/neotoma/raw/neotoma_pollen_dataset_downloads --workdir artifacts/swedish-direct-pollen --config docs/report/pollen-reconstruction/swedish-direct-pollen/config.json`; run `predict --target-dataset-id 19913`, `53995`, and `54001` with the same workdir and config; then run `score --workdir artifacts/swedish-direct-pollen`. The source files are EPD datasets accessed through Neotoma and identified by DOI and contributors in `cohort.csv`. The tracked cohort, prepared site profiles, frozen predictions, score tables and exclusion rows in this directory preserve the published result independently of that local output directory.

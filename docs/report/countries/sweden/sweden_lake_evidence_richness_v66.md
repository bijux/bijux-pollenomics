# Sweden lake evidence richness

This report ranks Sweden lake candidates by the richness of tracked pollen, archaeology, human aDNA, and domesticated-animal aDNA evidence around each lake. The ranking keeps lake identity diagnostics visible so duplicate names, source coordinate spread, and explicit source-position warnings are not hidden inside one synthetic lake label. Coordinates now resolve to one representative source-backed point per lake candidate so map checks land on a published source point rather than a synthetic centroid.

## Methodology

- Candidate derivation: Candidates come from Sweden-scoped Neotoma and LandClim pollen points whose names or site descriptions identify lake-like basins. Points merge only when their cleaned lake names match and their coordinates stay within 2 km, so nearby but differently named lakes remain distinct. Each candidate keeps one source-backed representative coordinate chosen from the supporting points instead of a synthetic arithmetic centroid. Duplicate names, coordinate spread, and source position notes remain explicit as ambiguity diagnostics.
- Distance bands: 10 km, 20 km, 30 km, 40 km, 50 km
- Identity diagnostics: cleaned-name matching within 2.0 km, coordinate-spread flag at 0.75 km, and explicit source-position notes when raw source notes say the lake position is uncertain.
- Coordinate targeting: each lake keeps one representative source-backed point chosen from its supporting pollen records using the method recorded in the registry CSV and JSON payload.
- Archaeology note: SEAD contributes site-level point counts. RAÄ contributes coarse 1-degree density cells, so the RAÄ term captures archaeology richness around the lake rather than precise site-by-site distance.
- Animal note: Domesticated animal aDNA remains sparse in the current Sweden bundle. The ranking keeps that sparsity visible instead of inflating it.

## Aggregate Ranking

| Rank | Lake | Coordinates | Aggregate score | Top-20 scenario presence | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.5170 | 6/6 | source_coordinate_spread | landclim-sites, neotoma-pollen | 2 | 42 | 0 |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.5157 | 6/6 | source_coordinate_spread | landclim-sites, neotoma-pollen | 2 | 42 | 0 |
| 3 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.5076 | 6/6 | none | landclim-sites, neotoma-pollen | 1 | 37 | 0 |
| 4 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.5032 | 6/6 | none | landclim-sites, neotoma-pollen | 1 | 38 | 0 |
| 5 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.4689 | 5/6 | none | landclim-sites, neotoma-pollen | 0 | 38 | 0 |
| 6 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.4638 | 6/6 | none | neotoma-pollen | 5 | 15 | 0 |
| 7 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.3823 | 5/6 | none | neotoma-pollen | 2 | 4 | 0 |
| 8 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 0.3688 | 4/6 | duplicate_sweden_name | neotoma-pollen | 2 | 18 | 0 |
| 9 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.3624 | 5/6 | none | landclim-sites, neotoma-pollen | 0 | 8 | 0 |
| 10 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3614 | 6/6 | none | landclim-sites, neotoma-pollen | 0 | 7 | 0 |
| 11 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 0.3603 | 4/6 | duplicate_sweden_name | neotoma-pollen | 0 | 19 | 0 |
| 12 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.3568 | 5/6 | duplicate_sweden_name | landclim-sites | 0 | 10 | 0 |
| 13 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3567 | 5/6 | none | landclim-sites, neotoma-pollen | 0 | 5 | 0 |
| 14 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.3548 | 4/6 | none | landclim-sites, neotoma-pollen | 0 | 7 | 0 |
| 15 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.3516 | 5/6 | duplicate_sweden_name | landclim-sites, neotoma-pollen | 0 | 5 | 0 |
| 16 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 0.3511 | 4/6 | duplicate_sweden_name | landclim-sites | 0 | 18 | 0 |
| 17 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3483 | 4/6 | none | neotoma-pollen | 4 | 23 | 0 |
| 18 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 0.3434 | 4/6 | none | landclim-sites, neotoma-pollen | 0 | 25 | 0 |
| 19 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | 0.3410 | 3/6 | source_coordinate_spread | landclim-sites, neotoma-pollen | 0 | 9 | 0 |
| 20 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.3402 | 3/6 | source_coordinate_spread, source_name_variants | landclim-sites, neotoma-pollen | 0 | 3 | 0 |

## Scenario Consensus

| Consensus rank | Lake | Coordinates | Top-20 scenario presence | Best scenario rank | Mean scenario rank | Aggregate rank | Coordinate method |
| ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 6/6 | 1 | 2.50 | 1 | source_coordinate_medoid |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 6/6 | 2 | 3.50 | 2 | source_coordinate_medoid |
| 3 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 6/6 | 2 | 3.67 | 3 | source_coordinate_medoid |
| 4 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 6/6 | 3 | 5.17 | 4 | source_coordinate_medoid |
| 5 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 6/6 | 2 | 5.17 | 6 | shared_source_coordinate |
| 6 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 6/6 | 10 | 13.17 | 10 | source_coordinate_medoid |
| 7 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 5/6 | 1 | 6.17 | 5 | source_coordinate_medoid |
| 8 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 5/6 | 8 | 14.33 | 9 | source_coordinate_medoid |
| 9 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 5/6 | 2 | 15.00 | 7 | shared_source_coordinate |
| 10 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 5/6 | 9 | 15.17 | 13 | source_coordinate_medoid |
| 11 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 5/6 | 7 | 17.00 | 12 | shared_source_coordinate |
| 12 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 5/6 | 10 | 17.50 | 15 | source_coordinate_medoid |
| 13 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 4/6 | 9 | 16.00 | 14 | source_coordinate_medoid |
| 14 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 4/6 | 9 | 17.17 | 11 | shared_source_coordinate |
| 15 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 4/6 | 6 | 17.83 | 8 | shared_source_coordinate |
| 16 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 4/6 | 14 | 17.83 | 17 | shared_source_coordinate |
| 17 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 4/6 | 7 | 19.50 | 16 | shared_source_coordinate |
| 18 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 4/6 | 8 | 21.00 | 18 | source_coordinate_medoid |
| 19 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 3/6 | 16 | 21.17 | 20 | source_coordinate_medoid |
| 20 | Åbodasjön | [57.085556, 14.478611](https://www.google.com/maps/search/?api=1&query=57.085556,14.478611) | 3/6 | 13 | 22.17 | 22 | source_coordinate_medoid |

## 10 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.5122 | source_coordinate_spread | 0 | 0 | 0 | 19 | 6654 | 3 | 3 |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.5122 | source_coordinate_spread | 0 | 0 | 0 | 19 | 6654 | 3 | 3 |
| 3 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.5122 | none | 0 | 0 | 0 | 19 | 6654 | 3 | 3 |
| 4 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.5043 | none | 0 | 0 | 0 | 18 | 6654 | 3 | 3 |
| 5 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.3904 | none | 2 | 32 | 0 | 0 | 10501 | 0 | 3 |
| 6 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | 0.3498 | source_coordinate_spread | 0 | 0 | 0 | 2 | 12008 | 2 | 3 |
| 7 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.3416 | duplicate_sweden_name | 0 | 0 | 0 | 4 | 8569 | 3 | 3 |
| 8 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 0.3344 | none | 0 | 0 | 0 | 9 | 5719 | 0 | 2 |
| 9 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.3326 | none | 0 | 0 | 0 | 3 | 8912 | 1 | 3 |
| 10 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 0.3299 | duplicate_sweden_name | 0 | 0 | 0 | 4 | 14902 | 2 | 3 |
| 11 | Vuolep Njakajaure (68.333333, 18.750000) | [68.333333, 18.750000](https://www.google.com/maps/search/?api=1&query=68.333333,18.750000) | 0.3296 | source_coordinate_spread | 0 | 0 | 0 | 1 | 214 | 4 | 3 |
| 12 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3258 | none | 0 | 0 | 0 | 1 | 8067 | 1 | 3 |
| 13 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3247 | none | 0 | 0 | 0 | 2 | 8912 | 1 | 3 |
| 14 | Badsjön (68.333333, 18.750000) | [68.333333, 18.750000](https://www.google.com/maps/search/?api=1&query=68.333333,18.750000) | 0.3212 | duplicate_sweden_name | 0 | 0 | 0 | 1 | 214 | 4 | 3 |
| 15 | Åbodasjön | [57.085556, 14.478611](https://www.google.com/maps/search/?api=1&query=57.085556,14.478611) | 0.3146 | none | 0 | 0 | 0 | 0 | 18884 | 1 | 3 |
| 16 | Sämbosjön (57.163130, 12.414260) | [57.163130, 12.414260](https://www.google.com/maps/search/?api=1&query=57.163130,12.414260) | 0.3120 | duplicate_sweden_name | 0 | 0 | 0 | 5 | 8569 | 2 | 3 |
| 17 | Tibetanus | [68.333333, 18.700000](https://www.google.com/maps/search/?api=1&query=68.333333,18.700000) | 0.3087 | none | 0 | 0 | 0 | 1 | 214 | 4 | 3 |
| 18 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.3081 | duplicate_sweden_name | 0 | 0 | 0 | 1 | 9853 | 1 | 3 |
| 19 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.3080 | source_coordinate_spread, source_name_variants | 0 | 0 | 0 | 0 | 8067 | 1 | 3 |
| 20 | Färshesjön | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | 0.3023 | none | 0 | 0 | 0 | 2 | 12008 | 2 | 3 |

## 20 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.5644 | source_coordinate_spread | 2 | 3 | 0 | 42 | 9859 | 3 | 4 |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.5644 | source_coordinate_spread | 2 | 3 | 0 | 42 | 9859 | 3 | 4 |
| 3 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.5307 | none | 1 | 2 | 0 | 38 | 9859 | 3 | 4 |
| 4 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.5272 | none | 1 | 2 | 0 | 37 | 9859 | 3 | 4 |
| 5 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.4776 | none | 5 | 81 | 0 | 15 | 10501 | 1 | 4 |
| 6 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 0.4411 | duplicate_sweden_name | 2 | 32 | 0 | 18 | 14316 | 2 | 4 |
| 7 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.3989 | none | 0 | 0 | 0 | 38 | 6654 | 0 | 2 |
| 8 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.3911 | none | 2 | 32 | 0 | 4 | 14316 | 2 | 4 |
| 9 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 0.3872 | duplicate_sweden_name | 0 | 0 | 0 | 19 | 14902 | 4 | 3 |
| 10 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.3729 | duplicate_sweden_name | 0 | 0 | 0 | 5 | 28737 | 1 | 3 |
| 11 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.3676 | duplicate_sweden_name | 0 | 0 | 0 | 10 | 14902 | 4 | 3 |
| 12 | Sämbosjön (57.163130, 12.414260) | [57.163130, 12.414260](https://www.google.com/maps/search/?api=1&query=57.163130,12.414260) | 0.3658 | duplicate_sweden_name | 0 | 0 | 0 | 13 | 14902 | 4 | 3 |
| 13 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3655 | none | 0 | 0 | 0 | 7 | 15245 | 2 | 3 |
| 14 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.3586 | none | 0 | 0 | 0 | 8 | 28737 | 0 | 2 |
| 15 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3570 | none | 4 | 6 | 0 | 23 | 13558 | 0 | 3 |
| 16 | Vingölen | [57.133710, 15.937730](https://www.google.com/maps/search/?api=1&query=57.133710,15.937730) | 0.3563 | none | 0 | 0 | 0 | 1 | 24492 | 4 | 3 |
| 17 | Skärsgölarna | [57.016667, 16.116667](https://www.google.com/maps/search/?api=1&query=57.016667,16.116667) | 0.3524 | none | 0 | 0 | 0 | 2 | 24492 | 3 | 3 |
| 18 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 0.3492 | none | 0 | 0 | 0 | 25 | 5719 | 0 | 2 |
| 19 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | 0.3489 | source_coordinate_spread | 0 | 0 | 0 | 9 | 12008 | 2 | 3 |
| 20 | Kroksjön | [56.273460, 15.008430](https://www.google.com/maps/search/?api=1&query=56.273460,15.008430) | 0.3483 | none | 0 | 0 | 0 | 12 | 16666 | 3 | 3 |

## 30 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.6196 | none | 11 | 15 | 0 | 122 | 7880 | 4 | 4 |
| 2 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.5002 | none | 11 | 158 | 0 | 34 | 14316 | 3 | 4 |
| 3 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.4809 | source_coordinate_spread | 3 | 4 | 0 | 64 | 9859 | 4 | 4 |
| 4 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.4809 | source_coordinate_spread | 3 | 4 | 0 | 64 | 9859 | 4 | 4 |
| 5 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.4809 | none | 3 | 4 | 0 | 64 | 9859 | 4 | 4 |
| 6 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.4796 | none | 3 | 4 | 0 | 63 | 9859 | 4 | 4 |
| 7 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.4120 | none | 3 | 58 | 0 | 26 | 14316 | 4 | 4 |
| 8 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.4055 | none | 0 | 0 | 0 | 19 | 28737 | 3 | 3 |
| 9 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.4016 | none | 0 | 0 | 0 | 40 | 20658 | 2 | 3 |
| 10 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 0.3837 | duplicate_sweden_name | 0 | 0 | 0 | 30 | 32401 | 4 | 3 |
| 11 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 0.3778 | duplicate_sweden_name | 2 | 32 | 0 | 23 | 14316 | 3 | 4 |
| 12 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3773 | none | 0 | 0 | 0 | 14 | 21899 | 3 | 3 |
| 13 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.3739 | duplicate_sweden_name | 0 | 0 | 0 | 19 | 28737 | 2 | 3 |
| 14 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3685 | none | 9 | 66 | 0 | 51 | 13558 | 0 | 3 |
| 15 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 0.3653 | duplicate_sweden_name | 2 | 32 | 0 | 23 | 14316 | 3 | 4 |
| 16 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.3646 | source_coordinate_spread, source_name_variants | 0 | 0 | 0 | 38 | 12071 | 2 | 3 |
| 17 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.3592 | duplicate_sweden_name | 0 | 0 | 0 | 29 | 19907 | 4 | 3 |
| 18 | Västragylet | [56.350000, 14.883330](https://www.google.com/maps/search/?api=1&query=56.350000,14.883330) | 0.3524 | none | 0 | 0 | 0 | 14 | 16666 | 6 | 3 |
| 19 | Ran Viken | [56.281450, 14.290560](https://www.google.com/maps/search/?api=1&query=56.281450,14.290560) | 0.3479 | none | 1 | 1 | 0 | 34 | 19729 | 2 | 4 |
| 20 | Skärsgölarna | [57.016667, 16.116667](https://www.google.com/maps/search/?api=1&query=57.016667,16.116667) | 0.3465 | none | 0 | 0 | 0 | 8 | 24492 | 4 | 3 |

## 40 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.6155 | none | 13 | 31 | 0 | 168 | 11085 | 4 | 4 |
| 2 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.5148 | none | 11 | 158 | 0 | 45 | 14316 | 4 | 4 |
| 3 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.5083 | none | 11 | 158 | 0 | 44 | 30224 | 4 | 4 |
| 4 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.4713 | none | 3 | 4 | 0 | 108 | 9859 | 4 | 4 |
| 5 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.4659 | source_coordinate_spread | 3 | 4 | 0 | 102 | 9859 | 4 | 4 |
| 6 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.4606 | source_coordinate_spread | 3 | 4 | 0 | 96 | 9859 | 4 | 4 |
| 7 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.4570 | none | 3 | 4 | 0 | 92 | 9859 | 4 | 4 |
| 8 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.4184 | none | 0 | 0 | 0 | 21 | 28737 | 7 | 3 |
| 9 | Lindhultsgöl | [57.143611, 14.466111](https://www.google.com/maps/search/?api=1&query=57.143611,14.466111) | 0.4079 | none | 1 | 6 | 0 | 16 | 46236 | 4 | 4 |
| 10 | Ran Viken | [56.281450, 14.290560](https://www.google.com/maps/search/?api=1&query=56.281450,14.290560) | 0.4036 | none | 3 | 6 | 0 | 50 | 29588 | 5 | 4 |
| 11 | Mullsjön | [58.317610, 14.211360](https://www.google.com/maps/search/?api=1&query=58.317610,14.211360) | 0.4030 | none | 4 | 59 | 0 | 39 | 30970 | 2 | 4 |
| 12 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.4004 | none | 0 | 0 | 0 | 36 | 32716 | 4 | 3 |
| 13 | Åbodasjön | [57.085556, 14.478611](https://www.google.com/maps/search/?api=1&query=57.085556,14.478611) | 0.3989 | none | 1 | 6 | 0 | 20 | 46236 | 3 | 4 |
| 14 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3842 | none | 11 | 91 | 0 | 76 | 13558 | 0 | 3 |
| 15 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3772 | none | 0 | 0 | 0 | 44 | 24473 | 2 | 3 |
| 16 | Skärsgölarna | [57.016667, 16.116667](https://www.google.com/maps/search/?api=1&query=57.016667,16.116667) | 0.3727 | none | 1 | 32 | 0 | 23 | 24492 | 4 | 4 |
| 17 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3716 | none | 0 | 0 | 0 | 41 | 23125 | 3 | 3 |
| 18 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 0.3716 | duplicate_sweden_name | 2 | 32 | 0 | 35 | 21637 | 3 | 4 |
| 19 | Björksjödamm | [57.709000, 12.346410](https://www.google.com/maps/search/?api=1&query=57.709000,12.346410) | 0.3714 | none | 1 | 1 | 0 | 49 | 46255 | 1 | 4 |
| 20 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.3693 | duplicate_sweden_name | 0 | 0 | 0 | 43 | 37406 | 4 | 3 |

## 50 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.6324 | none | 13 | 31 | 0 | 201 | 19997 | 5 | 4 |
| 2 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.5763 | none | 12 | 30 | 0 | 172 | 11085 | 4 | 4 |
| 3 | Mullsjön | [58.317610, 14.211360](https://www.google.com/maps/search/?api=1&query=58.317610,14.211360) | 0.5668 | none | 11 | 158 | 0 | 76 | 40833 | 4 | 4 |
| 4 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.5621 | source_coordinate_spread | 12 | 30 | 0 | 153 | 11085 | 4 | 4 |
| 5 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.5569 | source_coordinate_spread | 12 | 30 | 0 | 146 | 11085 | 4 | 4 |
| 6 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.5466 | none | 11 | 158 | 0 | 55 | 38291 | 4 | 4 |
| 7 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 0.5352 | duplicate_sweden_name | 11 | 158 | 0 | 54 | 25127 | 4 | 4 |
| 8 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.5237 | none | 9 | 25 | 0 | 137 | 9859 | 4 | 4 |
| 9 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 0.5234 | duplicate_sweden_name | 11 | 158 | 0 | 55 | 25127 | 4 | 4 |
| 10 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.5104 | none | 11 | 158 | 0 | 60 | 38291 | 4 | 4 |
| 11 | Ljungsjön | [57.734290, 13.332690](https://www.google.com/maps/search/?api=1&query=57.734290,13.332690) | 0.4330 | none | 7 | 78 | 0 | 39 | 46860 | 1 | 4 |
| 12 | Ran Viken | [56.281450, 14.290560](https://www.google.com/maps/search/?api=1&query=56.281450,14.290560) | 0.4279 | none | 3 | 6 | 0 | 74 | 35437 | 7 | 4 |
| 13 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.4193 | none | 0 | 0 | 0 | 25 | 28737 | 9 | 3 |
| 14 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.4144 | none | 0 | 0 | 0 | 84 | 33942 | 4 | 3 |
| 15 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.4060 | none | 0 | 0 | 0 | 60 | 44837 | 2 | 3 |
| 16 | Odensjön | [56.003940, 13.275650](https://www.google.com/maps/search/?api=1&query=56.003940,13.275650) | 0.4046 | none | 3 | 5 | 0 | 138 | 37147 | 4 | 4 |
| 17 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.4007 | none | 0 | 0 | 0 | 58 | 37147 | 4 | 3 |
| 18 | Åbodasjön | [57.085556, 14.478611](https://www.google.com/maps/search/?api=1&query=57.085556,14.478611) | 0.3978 | none | 1 | 6 | 0 | 23 | 46236 | 5 | 4 |
| 19 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 0.3975 | none | 0 | 0 | 0 | 178 | 13996 | 0 | 2 |
| 20 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.3939 | duplicate_sweden_name | 0 | 0 | 0 | 36 | 43376 | 5 | 3 |

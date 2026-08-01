# Sweden lake evidence richness

This report ranks Sweden lake candidates by the richness of tracked pollen, archaeology, human aDNA, and domesticated-animal aDNA evidence around each lake. The ranking keeps lake identity diagnostics visible so duplicate names and registry naming cautions are not hidden inside one synthetic lake label.

Coordinates resolve to one representative source-backed point per lake candidate so map checks land on a published source point rather than a synthetic centroid.

## Methodology

- Candidate derivation: Candidates come from Sweden-scoped Neotoma and LandClim pollen points whose names or site descriptions identify lake-like basins. Points merge only when their cleaned lake names match and their coordinates stay within 2 km, so nearby but differently named lakes remain distinct. Each candidate keeps one source-backed representative coordinate chosen from the supporting points instead of a synthetic arithmetic centroid. Duplicate names, coordinate spread, and source position notes remain explicit as ambiguity diagnostics.
- Distance bands: 10 km, 20 km, 30 km, 40 km, 50 km
- Identity diagnostics: cleaned-name matching within 2.0 km, coordinate-spread flag at 0.75 km, and explicit source-position notes when raw source notes say the lake position is uncertain
- Coordinate targeting: each lake keeps one representative source-backed point chosen from its supporting pollen records using the method recorded in the registry CSV and JSON payload
- Human aDNA weighting: human aDNA contributes 0.20 of each band score, direct pollen contributes 0.20, nearby pollen contributes 0.10, and archaeology contributes 0.25
- Ranking decision rule: aggregate and band ranks use one blended score without an explicit decision chain
- Temporal alignment rule: time-aware chronology remains visible where available, but the ranking does not currently promote chronology overlap as a separate rule
- Source temporal coverage: Neotoma 81/99 numeric-interval records (BP site spans available; chronology rows absent in checked-in raw capture; use Neotoma to compare pollen context around lakes; only promote it into chronology-aware support when a numeric interval is actually present.), LandClim 190/198 numeric-interval records (LandClim sequence points carry explicit temporal posture and REVEALS model cells are published as separate, filterable time-window records.), SEAD 777/2007 numeric-interval records (partial chronology coverage)

- Archaeology note: SEAD contributes site-level point counts. RAÄ contributes coarse 1-degree density cells, so the RAÄ term captures archaeology richness around the lake rather than precise site-by-site distance.
- Pollen note: Direct pollen signal reflects the quality of the lake-linked pollen records rather than a synthetic lake average.
- Animal note: Domesticated animal aDNA remains sparse in the current Sweden bundle. The ranking keeps that sparsity visible instead of inflating it.

## Interpretation guardrails

- Human aDNA remains the gatekeeper layer: lakes without at least one nearby human locality inside 50 km do not stay in the ranked candidate set.
- Spatial context is not the same as chronology support: source layers with zero numeric intervals remain visible for surrounding evidence density, but they do not contribute chronology-overlap strength.
- Partial chronology remains explicit: Neotoma records with BP intervals can strengthen time-aware comparisons, while unresolved or label-only records stay visible without being promoted to same-period evidence.

## Aggregate Ranking

| Rank | Lake | Coordinates | Lake registry id | Name status | Aggregate score | Top-20 scenario presence | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | not_available | not_available | 0.4875 | 7/7 | source_coordinate_spread | landclim-sites, neotoma-pollen | 2 | 42 | 0 |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | not_available | not_available | 0.4864 | 7/7 | source_coordinate_spread | landclim-sites, neotoma-pollen | 2 | 42 | 0 |
| 3 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | not_available | not_available | 0.4770 | 7/7 | none | landclim-sites, neotoma-pollen | 1 | 37 | 0 |
| 4 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | not_available | not_available | 0.4731 | 7/7 | none | landclim-sites, neotoma-pollen | 1 | 38 | 0 |
| 5 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | not_available | not_available | 0.4467 | 7/7 | none | landclim-sites, neotoma-pollen | 0 | 38 | 0 |
| 6 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | not_available | not_available | 0.4240 | 7/7 | none | neotoma-pollen | 5 | 15 | 0 |
| 7 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | not_available | not_available | 0.3396 | 7/7 | none | neotoma-pollen | 4 | 23 | 0 |
| 8 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | not_available | not_available | 0.3387 | 6/7 | none | neotoma-pollen | 2 | 4 | 0 |
| 9 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | not_available | not_available | 0.3261 | 6/7 | none | landclim-sites, neotoma-pollen | 0 | 5 | 0 |
| 10 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | not_available | not_available | 0.3216 | 5/7 | duplicate_sweden_name | neotoma-pollen | 2 | 18 | 0 |
| 11 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | not_available | not_available | 0.3185 | 6/7 | none | landclim-sites, neotoma-pollen | 0 | 7 | 0 |
| 12 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | not_available | not_available | 0.3157 | 6/7 | none | landclim-sites, neotoma-pollen | 0 | 7 | 0 |
| 13 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | not_available | not_available | 0.3129 | 5/7 | none | landclim-sites, neotoma-pollen | 0 | 8 | 0 |
| 14 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | not_available | not_available | 0.3109 | 6/7 | source_coordinate_spread, source_name_variants | landclim-sites, neotoma-pollen | 0 | 3 | 0 |
| 15 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | not_available | not_available | 0.3072 | 4/7 | none | landclim-sites, neotoma-pollen | 0 | 25 | 0 |
| 16 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | not_available | not_available | 0.3060 | 5/7 | duplicate_sweden_name | landclim-sites | 0 | 18 | 0 |
| 17 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | not_available | not_available | 0.3035 | 4/7 | duplicate_sweden_name | landclim-sites, neotoma-pollen | 0 | 5 | 0 |
| 18 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | not_available | not_available | 0.3012 | 4/7 | source_coordinate_spread | landclim-sites, neotoma-pollen | 0 | 9 | 0 |
| 19 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | not_available | not_available | 0.2987 | 4/7 | duplicate_sweden_name | landclim-sites | 0 | 10 | 0 |
| 20 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | not_available | not_available | 0.2944 | 4/7 | duplicate_sweden_name | neotoma-pollen | 0 | 19 | 0 |

## Scenario Consensus

| Consensus rank | Lake | Coordinates | Lake registry id | Name status | Top-20 scenario presence | Best scenario rank | Mean scenario rank | Aggregate rank | Coordinate method |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | not_available | not_available | 7/7 | 1 | 2.29 | 1 | source_coordinate_medoid |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | not_available | not_available | 7/7 | 2 | 3.43 | 2 | source_coordinate_medoid |
| 3 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | not_available | not_available | 7/7 | 2 | 3.86 | 3 | source_coordinate_medoid |
| 4 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | not_available | not_available | 7/7 | 3 | 4.71 | 4 | source_coordinate_medoid |
| 5 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | not_available | not_available | 7/7 | 1 | 5.29 | 5 | source_coordinate_medoid |
| 6 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | not_available | not_available | 7/7 | 1 | 5.43 | 6 | shared_source_coordinate |
| 7 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | not_available | not_available | 7/7 | 2 | 8.71 | 7 | shared_source_coordinate |
| 8 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | not_available | not_available | 6/7 | 8 | 11.67 | 9 | source_coordinate_medoid |
| 9 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | not_available | not_available | 6/7 | 10 | 12.67 | 11 | source_coordinate_medoid |
| 10 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | not_available | not_available | 6/7 | 7 | 13.50 | 12 | source_coordinate_medoid |
| 11 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | not_available | not_available | 6/7 | 2 | 14.57 | 8 | shared_source_coordinate |
| 12 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | not_available | not_available | 6/7 | 11 | 15.83 | 14 | source_coordinate_medoid |
| 13 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | not_available | not_available | 5/7 | 10 | 15.17 | 13 | source_coordinate_medoid |
| 14 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | not_available | not_available | 5/7 | 7 | 17.14 | 10 | shared_source_coordinate |
| 15 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | not_available | not_available | 5/7 | 8 | 19.14 | 16 | shared_source_coordinate |
| 16 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | not_available | not_available | 4/7 | 8 | 16.33 | 15 | source_coordinate_medoid |
| 17 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | not_available | not_available | 4/7 | 12 | 17.83 | 17 | source_coordinate_medoid |
| 18 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | not_available | not_available | 4/7 | 6 | 18.14 | 18 | source_coordinate_medoid |
| 19 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | not_available | not_available | 4/7 | 10 | 21.00 | 19 | shared_source_coordinate |
| 20 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | not_available | not_available | 4/7 | 11 | 22.50 | 20 | shared_source_coordinate |

## Fieldwork Shortlist

| Fieldwork rank | Lake | Coordinates | Lake registry id | Name status | Shortlist score | Sampling posture | Human context | Sampling fit | Area km² | Human localities within 20 km | Evidence families within 20 km |
| ---: | --- | --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | not_available | not_available | 0.6996 | not_scored | core_human_adna_context | 0.0000 | Not available | 5 | 4 |
| 2 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | not_available | not_available | 0.4007 | not_scored | core_human_adna_context | 0.0000 | Not available | 4 | 3 |
| 3 | Ljungsjön | [57.734290, 13.332690](https://www.google.com/maps/search/?api=1&query=57.734290,13.332690) | not_available | not_available | 0.3006 | not_scored | core_human_adna_context | 0.0000 | Not available | 1 | 3 |
| 4 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | not_available | not_available | 0.4524 | not_scored | near_human_adna_context | 0.0000 | Not available | 2 | 4 |
| 5 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | not_available | not_available | 0.4523 | not_scored | near_human_adna_context | 0.0000 | Not available | 2 | 4 |
| 6 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | not_available | not_available | 0.4311 | not_scored | near_human_adna_context | 0.0000 | Not available | 1 | 4 |
| 7 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | not_available | not_available | 0.4306 | not_scored | near_human_adna_context | 0.0000 | Not available | 1 | 4 |
| 8 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | not_available | not_available | 0.3689 | not_scored | near_human_adna_context | 0.0000 | Not available | 2 | 4 |
| 9 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | not_available | not_available | 0.3660 | not_scored | near_human_adna_context | 0.0000 | Not available | 2 | 4 |
| 10 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | not_available | not_available | 0.3682 | not_scored | extended_human_adna_context | 0.0000 | Not available | 0 | 2 |
| 11 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | not_available | not_available | 0.2481 | not_scored | extended_human_adna_context | 0.0000 | Not available | 0 | 3 |
| 12 | Ran Viken | [56.281450, 14.290560](https://www.google.com/maps/search/?api=1&query=56.281450,14.290560) | not_available | not_available | 0.1955 | not_scored | extended_human_adna_context | 0.0000 | Not available | 0 | 2 |
| 13 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | not_available | not_available | 0.3126 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 3 |
| 14 | Gilltjärnen (60.083333, 15.833333) | [60.083333, 15.833333](https://www.google.com/maps/search/?api=1&query=60.083333,15.833333) | not_available | not_available | 0.2808 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 2 |
| 15 | Åbodasjön | [57.085556, 14.478611](https://www.google.com/maps/search/?api=1&query=57.085556,14.478611) | not_available | not_available | 0.2225 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 3 |
| 16 | Lindhultsgöl | [57.143611, 14.466111](https://www.google.com/maps/search/?api=1&query=57.143611,14.466111) | not_available | not_available | 0.2195 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 3 |
| 17 | Klotjärnen (61.821250, 16.404720) | [61.821250, 16.404720](https://www.google.com/maps/search/?api=1&query=61.821250,16.404720) | not_available | not_available | 0.2165 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 3 |
| 18 | Skärsgölarna | [57.016667, 16.116667](https://www.google.com/maps/search/?api=1&query=57.016667,16.116667) | not_available | not_available | 0.2157 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 3 |
| 19 | Klotjärnen (61.816667, 16.533333) | [61.816667, 16.533333](https://www.google.com/maps/search/?api=1&query=61.816667,16.533333) | not_available | not_available | 0.2155 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 3 |
| 20 | Färshesjön | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | not_available | not_available | 0.2132 | not_scored | outer_human_adna_context | 0.0000 | Not available | 0 | 3 |

## 10 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.4581 | source_coordinate_spread | 0 | 0 | 0 | 19 | 6654 | 3 | 3 |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.4581 | source_coordinate_spread | 0 | 0 | 0 | 19 | 6654 | 3 | 3 |
| 3 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.4554 | none | 0 | 0 | 0 | 19 | 6654 | 3 | 3 |
| 4 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.4522 | none | 0 | 0 | 0 | 18 | 6654 | 3 | 3 |
| 5 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.3690 | none | 2 | 32 | 0 | 0 | 10501 | 0 | 3 |
| 6 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | 0.3034 | source_coordinate_spread | 0 | 0 | 0 | 2 | 12008 | 2 | 3 |
| 7 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.3032 | none | 0 | 0 | 0 | 3 | 8912 | 1 | 3 |
| 8 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 0.3024 | none | 0 | 0 | 0 | 9 | 5719 | 0 | 2 |
| 9 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3001 | none | 0 | 0 | 0 | 1 | 8067 | 1 | 3 |
| 10 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.2969 | duplicate_sweden_name | 0 | 0 | 0 | 4 | 8569 | 3 | 3 |
| 11 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.2945 | none | 0 | 0 | 0 | 2 | 8912 | 1 | 3 |
| 12 | Vuolep Njakajaure (68.333333, 18.750000) | [68.333333, 18.750000](https://www.google.com/maps/search/?api=1&query=68.333333,18.750000) | 0.2899 | source_coordinate_spread | 0 | 0 | 0 | 1 | 214 | 4 | 3 |
| 13 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.2846 | none | 0 | 0 | 0 | 4 | 6654 | 0 | 2 |
| 14 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.2815 | source_coordinate_spread, source_name_variants | 0 | 0 | 0 | 0 | 8067 | 1 | 3 |
| 15 | Badsjön (68.333333, 18.750000) | [68.333333, 18.750000](https://www.google.com/maps/search/?api=1&query=68.333333,18.750000) | 0.2815 | duplicate_sweden_name | 0 | 0 | 0 | 1 | 214 | 4 | 3 |
| 16 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.2802 | none | 1 | 1 | 0 | 6 | 13558 | 0 | 3 |
| 17 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 0.2790 | duplicate_sweden_name | 0 | 0 | 0 | 4 | 14902 | 2 | 3 |
| 18 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.2787 | duplicate_sweden_name | 0 | 0 | 0 | 1 | 9853 | 1 | 3 |
| 19 | Sämbosjön (57.163130, 12.414260) | [57.163130, 12.414260](https://www.google.com/maps/search/?api=1&query=57.163130,12.414260) | 0.2713 | duplicate_sweden_name | 0 | 0 | 0 | 5 | 8569 | 2 | 3 |
| 20 | Ljungsjön | [57.734290, 13.332690](https://www.google.com/maps/search/?api=1&query=57.734290,13.332690) | 0.2693 | none | 1 | 1 | 0 | 3 | 8587 | 0 | 3 |

## 20 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.5340 | source_coordinate_spread | 2 | 3 | 0 | 42 | 9859 | 3 | 4 |
| 2 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.5340 | source_coordinate_spread | 2 | 3 | 0 | 42 | 9859 | 3 | 4 |
| 3 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.4996 | none | 1 | 2 | 0 | 38 | 9859 | 3 | 4 |
| 4 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.4947 | none | 1 | 2 | 0 | 37 | 9859 | 3 | 4 |
| 5 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.4395 | none | 5 | 81 | 0 | 15 | 10501 | 1 | 4 |
| 6 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.3829 | none | 0 | 0 | 0 | 38 | 6654 | 0 | 2 |
| 7 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 0.3802 | duplicate_sweden_name | 2 | 32 | 0 | 18 | 14316 | 2 | 4 |
| 8 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.3454 | none | 2 | 32 | 0 | 4 | 14316 | 2 | 4 |
| 9 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3440 | none | 4 | 6 | 0 | 23 | 13558 | 0 | 3 |
| 10 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3190 | none | 0 | 0 | 0 | 7 | 15245 | 2 | 3 |
| 11 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 0.3152 | duplicate_sweden_name | 0 | 0 | 0 | 19 | 14902 | 4 | 3 |
| 12 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.3118 | duplicate_sweden_name | 0 | 0 | 0 | 5 | 28737 | 1 | 3 |
| 13 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 0.3109 | none | 0 | 0 | 0 | 25 | 5719 | 0 | 2 |
| 14 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.3094 | none | 0 | 0 | 0 | 7 | 8912 | 2 | 3 |
| 15 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.3076 | none | 0 | 0 | 0 | 8 | 28737 | 0 | 2 |
| 16 | Färskesjön (56.166667, 15.866667) | [56.166667, 15.866667](https://www.google.com/maps/search/?api=1&query=56.166667,15.866667) | 0.3056 | source_coordinate_spread | 0 | 0 | 0 | 9 | 12008 | 2 | 3 |
| 17 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3051 | none | 0 | 0 | 0 | 5 | 8067 | 1 | 3 |
| 18 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.3049 | duplicate_sweden_name | 0 | 0 | 0 | 10 | 14902 | 4 | 3 |
| 19 | Sämbosjön (57.163130, 12.414260) | [57.163130, 12.414260](https://www.google.com/maps/search/?api=1&query=57.163130,12.414260) | 0.2995 | duplicate_sweden_name | 0 | 0 | 0 | 13 | 14902 | 4 | 3 |
| 20 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.2994 | source_coordinate_spread, source_name_variants | 0 | 0 | 0 | 3 | 8067 | 2 | 3 |

## 30 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.5854 | none | 11 | 15 | 0 | 122 | 7880 | 4 | 4 |
| 2 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.4657 | source_coordinate_spread | 3 | 4 | 0 | 64 | 9859 | 4 | 4 |
| 3 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.4650 | source_coordinate_spread | 3 | 4 | 0 | 64 | 9859 | 4 | 4 |
| 4 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.4630 | none | 3 | 4 | 0 | 63 | 9859 | 4 | 4 |
| 5 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.4629 | none | 3 | 4 | 0 | 64 | 9859 | 4 | 4 |
| 6 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.4555 | none | 11 | 158 | 0 | 34 | 14316 | 3 | 4 |
| 7 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3670 | none | 9 | 66 | 0 | 51 | 13558 | 0 | 3 |
| 8 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3623 | none | 0 | 0 | 0 | 40 | 20658 | 2 | 3 |
| 9 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.3564 | none | 3 | 58 | 0 | 26 | 14316 | 4 | 4 |
| 10 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.3423 | none | 0 | 0 | 0 | 19 | 28737 | 3 | 3 |
| 11 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.3378 | source_coordinate_spread, source_name_variants | 0 | 0 | 0 | 38 | 12071 | 2 | 3 |
| 12 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 0.3292 | duplicate_sweden_name | 2 | 32 | 0 | 23 | 14316 | 3 | 4 |
| 13 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3240 | none | 0 | 0 | 0 | 14 | 21899 | 3 | 3 |
| 14 | Storasjö (56.933333, 15.266667) | [56.933333, 15.266667](https://www.google.com/maps/search/?api=1&query=56.933333,15.266667) | 0.3173 | duplicate_sweden_name | 0 | 0 | 0 | 19 | 28737 | 2 | 3 |
| 15 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 0.3167 | duplicate_sweden_name | 2 | 32 | 0 | 23 | 14316 | 3 | 4 |
| 16 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.3076 | none | 0 | 0 | 0 | 17 | 15245 | 2 | 3 |
| 17 | Ran Viken | [56.281450, 14.290560](https://www.google.com/maps/search/?api=1&query=56.281450,14.290560) | 0.3064 | none | 1 | 1 | 0 | 34 | 19729 | 2 | 4 |
| 18 | Lillsjön (57.083330, 12.533330) | [57.083330, 12.533330](https://www.google.com/maps/search/?api=1&query=57.083330,12.533330) | 0.3028 | duplicate_sweden_name | 0 | 0 | 0 | 30 | 32401 | 4 | 3 |
| 19 | Sambösjön (57.133333, 12.416667) | [57.133333, 12.416667](https://www.google.com/maps/search/?api=1&query=57.133333,12.416667) | 0.2966 | duplicate_sweden_name | 0 | 0 | 0 | 29 | 19907 | 4 | 3 |
| 20 | Storasjö (56.916667, 15.283333) | [56.916667, 15.283333](https://www.google.com/maps/search/?api=1&query=56.916667,15.283333) | 0.2886 | duplicate_sweden_name | 0 | 0 | 0 | 13 | 28737 | 2 | 3 |

## 40 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.5898 | none | 13 | 31 | 0 | 168 | 11085 | 4 | 4 |
| 2 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.4724 | none | 11 | 158 | 0 | 45 | 14316 | 4 | 4 |
| 3 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.4587 | none | 3 | 4 | 0 | 108 | 9859 | 4 | 4 |
| 4 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.4522 | source_coordinate_spread | 3 | 4 | 0 | 102 | 9859 | 4 | 4 |
| 5 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.4490 | none | 11 | 158 | 0 | 44 | 30224 | 4 | 4 |
| 6 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.4476 | source_coordinate_spread | 3 | 4 | 0 | 96 | 9859 | 4 | 4 |
| 7 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.4445 | none | 3 | 4 | 0 | 92 | 9859 | 4 | 4 |
| 8 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3866 | none | 11 | 91 | 0 | 76 | 13558 | 0 | 3 |
| 9 | Mullsjön | [58.317610, 14.211360](https://www.google.com/maps/search/?api=1&query=58.317610,14.211360) | 0.3635 | none | 4 | 59 | 0 | 39 | 30970 | 2 | 4 |
| 10 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.3502 | none | 0 | 0 | 0 | 21 | 28737 | 7 | 3 |
| 11 | Ran Viken | [56.281450, 14.290560](https://www.google.com/maps/search/?api=1&query=56.281450,14.290560) | 0.3487 | none | 3 | 6 | 0 | 50 | 29588 | 5 | 4 |
| 12 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3431 | none | 0 | 0 | 0 | 44 | 24473 | 2 | 3 |
| 13 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.3420 | none | 0 | 0 | 0 | 36 | 32716 | 4 | 3 |
| 14 | Lindhultsgöl | [57.143611, 14.466111](https://www.google.com/maps/search/?api=1&query=57.143611,14.466111) | 0.3369 | none | 1 | 6 | 0 | 16 | 46236 | 4 | 4 |
| 15 | Åbodasjön | [57.085556, 14.478611](https://www.google.com/maps/search/?api=1&query=57.085556,14.478611) | 0.3318 | none | 1 | 6 | 0 | 20 | 46236 | 3 | 4 |
| 16 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.3311 | source_coordinate_spread, source_name_variants | 0 | 0 | 0 | 46 | 20658 | 2 | 3 |
| 17 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3285 | none | 0 | 0 | 0 | 41 | 23125 | 3 | 3 |
| 18 | Skärsgölarna | [57.016667, 16.116667](https://www.google.com/maps/search/?api=1&query=57.016667,16.116667) | 0.3248 | none | 1 | 32 | 0 | 23 | 24492 | 4 | 4 |
| 19 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 0.3242 | duplicate_sweden_name | 2 | 32 | 0 | 35 | 21637 | 3 | 4 |
| 20 | Holtjärnen | [60.650000, 14.916667](https://www.google.com/maps/search/?api=1&query=60.650000,14.916667) | 0.3185 | none | 0 | 0 | 0 | 115 | 8528 | 0 | 2 |

## 50 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bökesjön | [55.575556, 13.437500](https://www.google.com/maps/search/?api=1&query=55.575556,13.437500) | 0.6000 | none | 13 | 31 | 0 | 201 | 19997 | 5 | 4 |
| 2 | Krageholmssjön | [55.500000, 13.733333](https://www.google.com/maps/search/?api=1&query=55.500000,13.733333) | 0.5626 | none | 12 | 30 | 0 | 172 | 11085 | 4 | 4 |
| 3 | Bjäresjösjön (55.459167, 13.751944) | [55.459167, 13.751944](https://www.google.com/maps/search/?api=1&query=55.459167,13.751944) | 0.5560 | source_coordinate_spread | 12 | 30 | 0 | 153 | 11085 | 4 | 4 |
| 4 | Bjärsjöholmssjön (55.454444, 13.766389) | [55.454444, 13.766389](https://www.google.com/maps/search/?api=1&query=55.454444,13.766389) | 0.5533 | source_coordinate_spread | 12 | 30 | 0 | 146 | 11085 | 4 | 4 |
| 5 | Bussjösjön | [55.466667, 13.816667](https://www.google.com/maps/search/?api=1&query=55.466667,13.816667) | 0.5231 | none | 9 | 25 | 0 | 137 | 9859 | 4 | 4 |
| 6 | Mullsjön | [58.317610, 14.211360](https://www.google.com/maps/search/?api=1&query=58.317610,14.211360) | 0.5158 | none | 11 | 158 | 0 | 76 | 40833 | 4 | 4 |
| 7 | Åsbotorpsjön | [58.409810, 13.819960](https://www.google.com/maps/search/?api=1&query=58.409810,13.819960) | 0.4876 | none | 11 | 158 | 0 | 55 | 38291 | 4 | 4 |
| 8 | Flarken (58.583333, 13.666667) | [58.583333, 13.666667](https://www.google.com/maps/search/?api=1&query=58.583333,13.666667) | 0.4872 | duplicate_sweden_name | 11 | 158 | 0 | 54 | 25127 | 4 | 4 |
| 9 | Flarken (58.556790, 13.673190) | [58.556790, 13.673190](https://www.google.com/maps/search/?api=1&query=58.556790,13.673190) | 0.4752 | duplicate_sweden_name | 11 | 158 | 0 | 55 | 25127 | 4 | 4 |
| 10 | Bjärsjon | [58.334560, 13.656065](https://www.google.com/maps/search/?api=1&query=58.334560,13.656065) | 0.4501 | none | 11 | 158 | 0 | 60 | 38291 | 4 | 4 |
| 11 | Ljungsjön | [57.734290, 13.332690](https://www.google.com/maps/search/?api=1&query=57.734290,13.332690) | 0.3836 | none | 7 | 78 | 0 | 39 | 46860 | 1 | 4 |
| 12 | Sigvalde Träsk | [57.342480, 18.525960](https://www.google.com/maps/search/?api=1&query=57.342480,18.525960) | 0.3816 | none | 12 | 92 | 0 | 84 | 13558 | 0 | 3 |
| 13 | Ran Viken | [56.281450, 14.290560](https://www.google.com/maps/search/?api=1&query=56.281450,14.290560) | 0.3659 | none | 3 | 6 | 0 | 74 | 35437 | 7 | 4 |
| 14 | Flinkasjön | [56.250000, 13.250000](https://www.google.com/maps/search/?api=1&query=56.250000,13.250000) | 0.3636 | none | 0 | 0 | 0 | 84 | 33942 | 4 | 3 |
| 15 | Avegöl | [57.683333, 14.500000](https://www.google.com/maps/search/?api=1&query=57.683333,14.500000) | 0.3586 | none | 0 | 0 | 0 | 60 | 44837 | 2 | 3 |
| 16 | Odensjön | [56.003940, 13.275650](https://www.google.com/maps/search/?api=1&query=56.003940,13.275650) | 0.3564 | none | 3 | 5 | 0 | 138 | 37147 | 4 | 4 |
| 17 | Skärsgölarna | [57.016667, 16.116667](https://www.google.com/maps/search/?api=1&query=57.016667,16.116667) | 0.3547 | none | 2 | 33 | 0 | 61 | 24492 | 4 | 4 |
| 18 | Trummen | [56.866667, 14.833333](https://www.google.com/maps/search/?api=1&query=56.866667,14.833333) | 0.3518 | none | 0 | 0 | 0 | 25 | 28737 | 9 | 3 |
| 19 | Värsjö Utmark | [56.316667, 13.433333](https://www.google.com/maps/search/?api=1&query=56.316667,13.433333) | 0.3454 | none | 0 | 0 | 0 | 58 | 37147 | 4 | 3 |
| 20 | Kansjön (57.633333, 14.533333) | [57.633333, 14.533333](https://www.google.com/maps/search/?api=1&query=57.633333,14.533333) | 0.3437 | source_coordinate_spread, source_name_variants | 0 | 0 | 0 | 56 | 34336 | 3 | 3 |

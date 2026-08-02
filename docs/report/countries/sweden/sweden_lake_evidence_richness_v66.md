# Sweden lake evidence richness

This report ranks Sweden lake candidates by the richness of tracked pollen, archaeology, human aDNA, and domesticated-animal aDNA evidence around each lake. The ranking keeps lake identity diagnostics visible so duplicate names and registry naming cautions are not hidden inside one synthetic lake label.

Coordinates resolve to representative points drawn from official SMHI SVAR lake polygons, so map checks land on the lake itself rather than on a synthetic centroid or on one supporting pollen record.

## Methodology

- Candidate derivation: Candidates come from the Sweden lake registry published through SMHI SVAR. Each candidate uses a representative point derived from the official lake polygon instead of a pollen-point centroid. Only lakes with at least one human aDNA locality within 50 km remain in the ranked set. Registry names that clearly describe engineered water bodies or wetlands instead of sampling lakes are kept out of the shortlist.
- Distance bands: 10 km, 20 km, 30 km, 40 km, 50 km
- Identity diagnostics: duplicate Sweden lake names stay explicit, and registry names that do not come from the official register field remain flagged for review
- Coordinate targeting: each lake keeps one representative point derived from the official lake polygon, with registry identifiers and name status carried into the CSV, JSON, and map popups
- Human aDNA weighting: human aDNA contributes 0.59 of each band score, direct pollen contributes 0.14, nearby pollen contributes 0.07, and archaeology contributes 0.07
- Ranking decision rule: Aggregate and band ranks sort first by human aDNA locality and sample coverage, then by direct pollen support, then by broader pollen and archaeology context, with sampling fit and blended score used as later tie-breakers.
- Temporal alignment rule: Neotoma pollen and SEAD archaeology remain lake-anchored context layers, but their stronger chronology contribution comes only from records with numeric BP intervals that overlap nearby human locality windows.
- Time-navigation coverage: 26/26 ranked lakes have numeric navigation context; 15/26 have direct numeric pollen chronology. The map publishes 235 source-family/window summaries within 50 km, with nearby context kept separate from lake-owned chronology
- Source temporal coverage: Neotoma 81/99 numeric-interval records (BP site spans available; chronology rows absent in checked-in raw capture; use Neotoma to compare pollen context around lakes; only promote it into chronology-aware support when a numeric interval is actually present.), LandClim 190/198 numeric-interval records (LandClim sequence points carry explicit temporal posture and REVEALS model cells are published as separate, filterable time-window records.), SEAD 777/2007 numeric-interval records (partial chronology coverage)
- Sampling note: Lake suitability remains separate from evidence density. Very small basins stay visible but score lower, while registry names that clearly point to wetlands, pits, ponds, or engineered water bodies do not enter the ranked shortlist.
- Archaeology note: SEAD contributes site-level point counts and gains stronger weight when those site spans are numerically comparable and overlap nearby human locality windows. RAÄ contributes coarse density cells, so the archaeology term still measures surrounding evidence richness rather than exact site-to-lake proximity.
- Pollen note: Direct pollen signal reflects lake-basin pollen records placed on or very near the official lake. Nearby pollen signal then adds broader pollen context within the active distance band, with extra credit when those pollen records carry comparable chronology that overlaps nearby human localities.
- Animal note: Domesticated animal aDNA remains a secondary contextual signal. Human aDNA is the decisive ranking term, direct pollen is the next tie-break, and archaeology resolves ties among similarly sampled lakes.

## Interpretation guardrails

- Human aDNA remains the gatekeeper layer: lakes without at least one nearby human locality inside 50 km do not stay in the ranked candidate set.
- Spatial context is not the same as chronology support: source layers with zero numeric intervals remain visible for surrounding evidence density, but they do not contribute chronology-overlap strength.
- Nearby time context is not lake chronology: map windows summarize numeric pollen, SEAD, or aDNA records within 50 km and label that role explicitly. Direct lake pollen chronology remains a separate field in the CSV and JSON.
- Partial chronology remains explicit: Neotoma records with BP intervals can strengthen time-aware comparisons, while unresolved or label-only records stay visible without being promoted to same-period evidence.

## Aggregate Ranking

| Rank | Lake | Coordinates | Lake registry id | Name status | Aggregate score | Top-20 scenario presence | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 0.7070 | 7/7 | none | neotoma-pollen | 5 | 15 | 0 |
| 2 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 0.4204 | 7/7 | none | landclim-sites, neotoma-pollen | 1 | 37 | 0 |
| 3 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 636053-166363 | water_surface_name | 0.3981 | 7/7 | none | neotoma-pollen | 4 | 23 | 0 |
| 4 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 615375-137087 | water_surface_name | 0.3843 | 7/7 | none | landclim-sites, neotoma-pollen | 1 | 37 | 0 |
| 5 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 649459-137568 | water_surface_name | 0.3726 | 7/7 | none | landclim-sites, neotoma-pollen | 2 | 18 | 0 |
| 6 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 614958-137018 | water_surface_name | 0.3505 | 7/7 | none | landclim-sites, neotoma-pollen | 2 | 42 | 0 |
| 7 | Havgårdssjön | [55.483143, 13.357760](https://www.google.com/maps/search/?api=1&query=55.483143,13.357760) | 615365-134524 | water_surface_name | 0.3454 | 6/7 | none | none | 5 | 48 | 0 |
| 8 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 646681-140779 | water_surface_name | 0.2534 | 7/7 | none | neotoma-pollen | 0 | 8 | 0 |
| 9 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 622492-150312 | water_surface_name | 0.2364 | 7/7 | none | landclim-sites, neotoma-pollen | 0 | 9 | 0 |
| 10 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 632901-141943 | water_surface_name | 0.2155 | 7/7 | none | landclim-sites | 0 | 2 | 0 |
| 11 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 666346-150259 | water_surface_name | 0.2037 | 7/7 | none | landclim-sites, neotoma-pollen | 0 | 2 | 0 |
| 12 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 685496-153902 | water_surface_name | 0.1976 | 7/7 | none | landclim-sites | 0 | 8 | 0 |
| 13 | Lindhultsgöl | [57.145223, 14.467660](https://www.google.com/maps/search/?api=1&query=57.145223,14.467660) | 633608-141894 | water_surface_name | 0.1867 | 6/7 | none | landclim-sites | 0 | 0 | 0 |
| 14 | Rummehölj | [57.017085, 16.089132](https://www.google.com/maps/search/?api=1&query=57.017085,16.089132) | 632142-151758 | water_surface_name | 0.1849 | 6/7 | none | landclim-sites | 0 | 1 | 0 |
| 15 | Norr-Lången | [61.810118, 16.426007](https://www.google.com/maps/search/?api=1&query=61.810118,16.426007) | 685509-153253 | water_surface_name | 0.1668 | 6/7 | none | neotoma-pollen | 0 | 13 | 0 |
| 16 | Östra Ringsjön | [55.868570, 13.549973](https://www.google.com/maps/search/?api=1&query=55.868570,13.549973) | 619626-135565 | water_surface_name | 0.1619 | 6/7 | none | none | 0 | 16 | 0 |
| 17 | Lilla Sjö | [56.281643, 13.924259](https://www.google.com/maps/search/?api=1&query=56.281643,13.924259) | 624044-138336 | water_surface_name | 0.1608 | 6/7 | none | neotoma-pollen | 0 | 10 | 0 |
| 18 | Bergakyllen | [57.186058, 16.143141](https://www.google.com/maps/search/?api=1&query=57.186058,16.143141) | 633992-152030 | water_surface_name | 0.1586 | 5/7 | none | neotoma-pollen | 0 | 1 | 0 |
| 19 | Klogöl | [57.195047, 16.149861](https://www.google.com/maps/search/?api=1&query=57.195047,16.149861) | 634119-152099 | water_surface_name | 0.1585 | 5/7 | none | neotoma-pollen | 0 | 1 | 0 |
| 20 | Långetjärn | [57.723622, 12.359070](https://www.google.com/maps/search/?api=1&query=57.723622,12.359070) | 640460-129466 | water_surface_name | 0.1583 | 6/7 | none | neotoma-pollen | 0 | 4 | 0 |

## Scenario Consensus

| Consensus rank | Lake | Coordinates | Lake registry id | Name status | Top-20 scenario presence | Best scenario rank | Mean scenario rank | Aggregate rank | Coordinate method |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 7/7 | 1 | 1.86 | 1 | svar_polygon_representative_point |
| 2 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 7/7 | 2 | 3.43 | 2 | svar_polygon_representative_point |
| 3 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 615375-137087 | water_surface_name | 7/7 | 2 | 4.29 | 4 | svar_polygon_representative_point |
| 4 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 649459-137568 | water_surface_name | 7/7 | 1 | 4.29 | 5 | svar_polygon_representative_point |
| 5 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 636053-166363 | water_surface_name | 7/7 | 3 | 4.57 | 3 | svar_polygon_representative_point |
| 6 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 614958-137018 | water_surface_name | 7/7 | 4 | 5.86 | 6 | svar_polygon_representative_point |
| 7 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 646681-140779 | water_surface_name | 7/7 | 2 | 8.86 | 8 | svar_polygon_representative_point |
| 8 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 622492-150312 | water_surface_name | 7/7 | 6 | 9.71 | 9 | svar_polygon_representative_point |
| 9 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 632901-141943 | water_surface_name | 7/7 | 8 | 10.29 | 10 | svar_polygon_representative_point |
| 10 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 685496-153902 | water_surface_name | 7/7 | 10 | 12.29 | 12 | svar_polygon_representative_point |
| 11 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 666346-150259 | water_surface_name | 7/7 | 9 | 13.71 | 11 | svar_polygon_representative_point |
| 12 | Havgårdssjön | [55.483143, 13.357760](https://www.google.com/maps/search/?api=1&query=55.483143,13.357760) | 615365-134524 | water_surface_name | 6/7 | 3 | 7.43 | 7 | svar_polygon_representative_point |
| 13 | Lindhultsgöl | [57.145223, 14.467660](https://www.google.com/maps/search/?api=1&query=57.145223,14.467660) | 633608-141894 | water_surface_name | 6/7 | 13 | 13.83 | 13 | svar_polygon_representative_point |
| 14 | Rummehölj | [57.017085, 16.089132](https://www.google.com/maps/search/?api=1&query=57.017085,16.089132) | 632142-151758 | water_surface_name | 6/7 | 10 | 14.00 | 14 | svar_polygon_representative_point |
| 15 | Lilla Sjö | [56.281643, 13.924259](https://www.google.com/maps/search/?api=1&query=56.281643,13.924259) | 624044-138336 | water_surface_name | 6/7 | 10 | 15.83 | 17 | svar_polygon_representative_point |
| 16 | Östra Ringsjön | [55.868570, 13.549973](https://www.google.com/maps/search/?api=1&query=55.868570,13.549973) | 619626-135565 | water_surface_name | 6/7 | 9 | 16.71 | 16 | svar_polygon_representative_point |
| 17 | Norr-Lången | [61.810118, 16.426007](https://www.google.com/maps/search/?api=1&query=61.810118,16.426007) | 685509-153253 | water_surface_name | 6/7 | 14 | 17.14 | 15 | svar_polygon_representative_point |
| 18 | Långetjärn | [57.723622, 12.359070](https://www.google.com/maps/search/?api=1&query=57.723622,12.359070) | 640460-129466 | water_surface_name | 6/7 | 14 | 18.43 | 20 | svar_polygon_representative_point |
| 19 | Bergakyllen | [57.186058, 16.143141](https://www.google.com/maps/search/?api=1&query=57.186058,16.143141) | 633992-152030 | water_surface_name | 5/7 | 14 | 16.83 | 18 | svar_polygon_representative_point |
| 20 | Klogöl | [57.195047, 16.149861](https://www.google.com/maps/search/?api=1&query=57.195047,16.149861) | 634119-152099 | water_surface_name | 5/7 | 15 | 17.83 | 19 | svar_polygon_representative_point |

## Fieldwork Shortlist

| Fieldwork rank | Lake | Coordinates | Lake registry id | Name status | Shortlist score | Sampling posture | Human context | Sampling fit | Area km² | Human localities within 20 km | Evidence families within 20 km |
| ---: | --- | --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 649459-137568 | water_surface_name | 0.5936 | sampling_lake_candidate | near_human_adna_context | 0.8680 | 0.166 | 2 | 4 |
| 2 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 0.5734 | sampling_lake_candidate | near_human_adna_context | 1.0000 | 0.759 | 1 | 4 |
| 3 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 615375-137087 | water_surface_name | 0.5487 | sampling_lake_candidate | near_human_adna_context | 1.0000 | 2.051 | 1 | 4 |
| 4 | Havgårdssjön | [55.483143, 13.357760](https://www.google.com/maps/search/?api=1&query=55.483143,13.357760) | 615365-134524 | water_surface_name | 0.3945 | sampling_lake_candidate | near_human_adna_context | 1.0000 | 0.502 | 5 | 3 |
| 5 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 0.7867 | compact_lake_candidate | core_human_adna_context | 0.6300 | 0.133 | 5 | 4 |
| 6 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 636053-166363 | water_surface_name | 0.4817 | compact_lake_candidate | core_human_adna_context | 0.6300 | 0.087 | 4 | 4 |
| 7 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 614958-137018 | water_surface_name | 0.4162 | small_lake_review | near_human_adna_context | 0.2700 | 0.022 | 2 | 4 |
| 8 | Finjasjön | [56.135794, 13.702733](https://www.google.com/maps/search/?api=1&query=56.135794,13.702733) | 622731-136920 | water_surface_name | 0.1906 | sampling_lake_candidate | extended_human_adna_context | 1.0000 | 10.497 | 0 | 2 |
| 9 | Örevattnet | [58.552564, 11.600740](https://www.google.com/maps/search/?api=1&query=58.552564,11.600740) | 649958-125585 | water_surface_name | 0.1793 | sampling_lake_candidate | extended_human_adna_context | 0.8680 | 0.325 | 0 | 2 |
| 10 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 622492-150312 | water_surface_name | 0.4368 | sampling_lake_candidate | outer_human_adna_context | 0.8680 | 0.459 | 0 | 3 |
| 11 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 646681-140779 | water_surface_name | 0.3447 | sampling_lake_candidate | outer_human_adna_context | 1.0000 | 3.918 | 0 | 3 |
| 12 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 685496-153902 | water_surface_name | 0.3442 | sampling_lake_candidate | outer_human_adna_context | 1.0000 | 2.439 | 0 | 3 |
| 13 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 632901-141943 | water_surface_name | 0.3399 | sampling_lake_candidate | outer_human_adna_context | 1.0000 | 0.545 | 0 | 3 |
| 14 | Långetjärn | [57.723622, 12.359070](https://www.google.com/maps/search/?api=1&query=57.723622,12.359070) | 640460-129466 | water_surface_name | 0.2987 | sampling_lake_candidate | outer_human_adna_context | 0.8680 | 0.194 | 0 | 3 |
| 15 | Östra Ringsjön | [55.868570, 13.549973](https://www.google.com/maps/search/?api=1&query=55.868570,13.549973) | 619626-135565 | water_surface_name | 0.1806 | sampling_lake_candidate | outer_human_adna_context | 0.9400 | 24.728 | 0 | 2 |
| 16 | Värsjön | [56.312348, 13.469780](https://www.google.com/maps/search/?api=1&query=56.312348,13.469780) | 624606-135677 | water_surface_name | 0.1729 | sampling_lake_candidate | outer_human_adna_context | 1.0000 | 2.661 | 0 | 2 |
| 17 | Jämningen | [56.297527, 14.314794](https://www.google.com/maps/search/?api=1&query=56.297527,14.314794) | 624245-140812 | water_surface_name | 0.1595 | sampling_lake_candidate | outer_human_adna_context | 0.8680 | 0.436 | 0 | 2 |
| 18 | Kyrksjön | [58.956460, 15.070704](https://www.google.com/maps/search/?api=1&query=58.956460,15.070704) | 653734-145755 | water_surface_name | 0.1529 | sampling_lake_candidate | outer_human_adna_context | 0.8680 | 0.219 | 0 | 2 |
| 19 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 666346-150259 | water_surface_name | 0.3643 | compact_lake_candidate | outer_human_adna_context | 0.6300 | 0.102 | 0 | 3 |
| 20 | Norr-Lången | [61.810118, 16.426007](https://www.google.com/maps/search/?api=1&query=61.810118,16.426007) | 685509-153253 | water_surface_name | 0.2797 | compact_lake_candidate | outer_human_adna_context | 0.6300 | 0.115 | 0 | 3 |

## 10 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.7117 | none | 2 | 32 | 0 | 0 | 10501 | 1 | 4 |
| 2 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 0.3192 | none | 0 | 0 | 0 | 18 | 6654 | 16 | 3 |
| 3 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 0.2848 | none | 1 | 1 | 0 | 6 | 13558 | 2 | 4 |
| 4 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 0.2698 | none | 0 | 0 | 0 | 19 | 6654 | 16 | 3 |
| 5 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.2520 | none | 0 | 0 | 0 | 4 | 6654 | 5 | 3 |
| 6 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 0.2375 | none | 0 | 0 | 0 | 2 | 12008 | 4 | 3 |
| 7 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.2251 | none | 0 | 0 | 0 | 1 | 10501 | 3 | 3 |
| 8 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 0.2039 | none | 0 | 0 | 0 | 0 | 18884 | 6 | 3 |
| 9 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 0.2001 | none | 0 | 0 | 0 | 1 | 12100 | 2 | 3 |
| 10 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 0.1894 | none | 0 | 0 | 0 | 3 | 3464 | 3 | 3 |
| 11 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 0.1769 | none | 0 | 0 | 0 | 3 | 3815 | 1 | 3 |
| 12 | Rummehölj | [57.017085, 16.089132](https://www.google.com/maps/search/?api=1&query=57.017085,16.089132) | 0.1746 | none | 0 | 0 | 0 | 0 | 24492 | 4 | 3 |
| 13 | Lindhultsgöl | [57.145223, 14.467660](https://www.google.com/maps/search/?api=1&query=57.145223,14.467660) | 0.1718 | none | 0 | 0 | 0 | 0 | 8067 | 6 | 3 |
| 14 | Norr-Lången | [61.810118, 16.426007](https://www.google.com/maps/search/?api=1&query=61.810118,16.426007) | 0.1578 | none | 0 | 0 | 0 | 3 | 3464 | 3 | 3 |
| 15 | Bergakyllen | [57.186058, 16.143141](https://www.google.com/maps/search/?api=1&query=57.186058,16.143141) | 0.1478 | none | 0 | 0 | 0 | 1 | 12484 | 3 | 3 |
| 16 | Klogöl | [57.195047, 16.149861](https://www.google.com/maps/search/?api=1&query=57.195047,16.149861) | 0.1478 | none | 0 | 0 | 0 | 1 | 12484 | 3 | 3 |
| 17 | Långetjärn | [57.723622, 12.359070](https://www.google.com/maps/search/?api=1&query=57.723622,12.359070) | 0.1477 | none | 0 | 0 | 0 | 0 | 8569 | 1 | 3 |
| 18 | Lilla Sjö | [56.281643, 13.924259](https://www.google.com/maps/search/?api=1&query=56.281643,13.924259) | 0.1298 | none | 0 | 0 | 0 | 4 | 19729 | 1 | 3 |
| 19 | Östra Ringsjön | [55.868570, 13.549973](https://www.google.com/maps/search/?api=1&query=55.868570,13.549973) | 0.1202 | none | 0 | 0 | 0 | 1 | 6654 | 12 | 2 |
| 20 | Värsjön | [56.312348, 13.469780](https://www.google.com/maps/search/?api=1&query=56.312348,13.469780) | 0.1194 | none | 0 | 0 | 0 | 2 | 8912 | 9 | 2 |

## 20 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.7245 | none | 5 | 81 | 0 | 15 | 10501 | 2 | 4 |
| 2 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.4780 | none | 2 | 32 | 0 | 18 | 14316 | 4 | 4 |
| 3 | Havgårdssjön | [55.483143, 13.357760](https://www.google.com/maps/search/?api=1&query=55.483143,13.357760) | 0.4394 | none | 5 | 6 | 0 | 48 | 6654 | 6 | 3 |
| 4 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 0.4083 | none | 2 | 3 | 0 | 42 | 9859 | 20 | 4 |
| 5 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 0.3968 | none | 1 | 2 | 0 | 37 | 9859 | 20 | 4 |
| 6 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 0.3841 | none | 4 | 6 | 0 | 23 | 13558 | 2 | 4 |
| 7 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.3429 | none | 1 | 1 | 0 | 37 | 6654 | 6 | 4 |
| 8 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 0.2365 | none | 0 | 0 | 0 | 9 | 12008 | 4 | 3 |
| 9 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 0.2055 | none | 0 | 0 | 0 | 2 | 27226 | 2 | 3 |
| 10 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 0.2005 | none | 0 | 0 | 0 | 2 | 18884 | 6 | 3 |
| 11 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 0.1873 | none | 0 | 0 | 0 | 8 | 3464 | 3 | 3 |
| 12 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 0.1816 | none | 0 | 0 | 0 | 8 | 14316 | 1 | 3 |
| 13 | Rummehölj | [57.017085, 16.089132](https://www.google.com/maps/search/?api=1&query=57.017085,16.089132) | 0.1793 | none | 0 | 0 | 0 | 1 | 24492 | 7 | 3 |
| 14 | Lindhultsgöl | [57.145223, 14.467660](https://www.google.com/maps/search/?api=1&query=57.145223,14.467660) | 0.1727 | none | 0 | 0 | 0 | 0 | 18884 | 6 | 3 |
| 15 | Norr-Lången | [61.810118, 16.426007](https://www.google.com/maps/search/?api=1&query=61.810118,16.426007) | 0.1587 | none | 0 | 0 | 0 | 13 | 3464 | 3 | 3 |
| 16 | Bergakyllen | [57.186058, 16.143141](https://www.google.com/maps/search/?api=1&query=57.186058,16.143141) | 0.1526 | none | 0 | 0 | 0 | 1 | 12484 | 6 | 3 |
| 17 | Klogöl | [57.195047, 16.149861](https://www.google.com/maps/search/?api=1&query=57.195047,16.149861) | 0.1526 | none | 0 | 0 | 0 | 1 | 12484 | 6 | 3 |
| 18 | Långetjärn | [57.723622, 12.359070](https://www.google.com/maps/search/?api=1&query=57.723622,12.359070) | 0.1496 | none | 0 | 0 | 0 | 4 | 8569 | 1 | 3 |
| 19 | Lilla Sjö | [56.281643, 13.924259](https://www.google.com/maps/search/?api=1&query=56.281643,13.924259) | 0.1366 | none | 0 | 0 | 0 | 10 | 19729 | 4 | 3 |
| 20 | Östra Ringsjön | [55.868570, 13.549973](https://www.google.com/maps/search/?api=1&query=55.868570,13.549973) | 0.1358 | none | 0 | 0 | 0 | 16 | 15566 | 15 | 2 |

## 30 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6905 | none | 11 | 158 | 0 | 34 | 14316 | 5 | 4 |
| 2 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.5920 | none | 11 | 15 | 0 | 126 | 7880 | 24 | 4 |
| 3 | Havgårdssjön | [55.483143, 13.357760](https://www.google.com/maps/search/?api=1&query=55.483143,13.357760) | 0.5153 | none | 13 | 31 | 0 | 115 | 7880 | 22 | 3 |
| 4 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 0.4653 | none | 9 | 66 | 0 | 51 | 13558 | 3 | 4 |
| 5 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 0.3936 | none | 3 | 4 | 0 | 67 | 9859 | 25 | 4 |
| 6 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 0.3419 | none | 3 | 4 | 0 | 64 | 9859 | 25 | 4 |
| 7 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.3413 | none | 2 | 32 | 0 | 23 | 14316 | 5 | 4 |
| 8 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 0.2288 | none | 0 | 0 | 0 | 10 | 12008 | 4 | 3 |
| 9 | Finjasjön | [56.135794, 13.702733](https://www.google.com/maps/search/?api=1&query=56.135794,13.702733) | 0.2187 | none | 2 | 5 | 0 | 40 | 29588 | 27 | 3 |
| 10 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 0.2088 | none | 0 | 0 | 0 | 8 | 27471 | 11 | 3 |
| 11 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 0.2014 | none | 0 | 0 | 0 | 7 | 27226 | 2 | 3 |
| 12 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 0.1873 | none | 0 | 0 | 0 | 22 | 9015 | 3 | 3 |
| 13 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 0.1866 | none | 0 | 0 | 0 | 21 | 14316 | 4 | 3 |
| 14 | Lindhultsgöl | [57.145223, 14.467660](https://www.google.com/maps/search/?api=1&query=57.145223,14.467660) | 0.1833 | none | 0 | 0 | 0 | 10 | 27471 | 11 | 3 |
| 15 | Rummehölj | [57.017085, 16.089132](https://www.google.com/maps/search/?api=1&query=57.017085,16.089132) | 0.1750 | none | 0 | 0 | 0 | 8 | 24492 | 8 | 3 |
| 16 | Bergakyllen | [57.186058, 16.143141](https://www.google.com/maps/search/?api=1&query=57.186058,16.143141) | 0.1583 | none | 0 | 0 | 0 | 9 | 24492 | 8 | 3 |
| 17 | Klogöl | [57.195047, 16.149861](https://www.google.com/maps/search/?api=1&query=57.195047,16.149861) | 0.1580 | none | 0 | 0 | 0 | 8 | 24492 | 8 | 3 |
| 18 | Norr-Lången | [61.810118, 16.426007](https://www.google.com/maps/search/?api=1&query=61.810118,16.426007) | 0.1555 | none | 0 | 0 | 0 | 25 | 6745 | 3 | 3 |
| 19 | Långetjärn | [57.723622, 12.359070](https://www.google.com/maps/search/?api=1&query=57.723622,12.359070) | 0.1551 | none | 0 | 0 | 0 | 23 | 13574 | 2 | 3 |
| 20 | Lilla Sjö | [56.281643, 13.924259](https://www.google.com/maps/search/?api=1&query=56.281643,13.924259) | 0.1536 | none | 0 | 0 | 0 | 26 | 19729 | 14 | 3 |

## 40 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6905 | none | 11 | 158 | 0 | 44 | 30224 | 6 | 4 |
| 2 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.6707 | none | 13 | 31 | 0 | 165 | 11085 | 41 | 4 |
| 3 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 0.5566 | none | 11 | 91 | 0 | 76 | 13558 | 3 | 4 |
| 4 | Havgårdssjön | [55.483143, 13.357760](https://www.google.com/maps/search/?api=1&query=55.483143,13.357760) | 0.5028 | none | 13 | 31 | 0 | 148 | 7880 | 28 | 3 |
| 5 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 0.4020 | none | 4 | 59 | 0 | 39 | 30970 | 5 | 4 |
| 6 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 0.3733 | none | 3 | 4 | 0 | 101 | 9859 | 26 | 4 |
| 7 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.3389 | none | 2 | 32 | 0 | 37 | 21637 | 5 | 4 |
| 8 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 0.3225 | none | 3 | 4 | 0 | 102 | 9859 | 26 | 4 |
| 9 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 0.2612 | none | 1 | 6 | 0 | 20 | 46236 | 21 | 4 |
| 10 | Lilla Sjö | [56.281643, 13.924259](https://www.google.com/maps/search/?api=1&query=56.281643,13.924259) | 0.2442 | none | 3 | 6 | 0 | 52 | 29588 | 23 | 4 |
| 11 | Finjasjön | [56.135794, 13.702733](https://www.google.com/maps/search/?api=1&query=56.135794,13.702733) | 0.2394 | none | 3 | 6 | 0 | 58 | 29588 | 39 | 3 |
| 12 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 0.2363 | none | 2 | 2 | 0 | 32 | 13765 | 3 | 4 |
| 13 | Lindhultsgöl | [57.145223, 14.467660](https://www.google.com/maps/search/?api=1&query=57.145223,14.467660) | 0.2339 | none | 1 | 6 | 0 | 16 | 46236 | 20 | 4 |
| 14 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 0.2300 | none | 0 | 0 | 0 | 23 | 12008 | 6 | 3 |
| 15 | Östra Ringsjön | [55.868570, 13.549973](https://www.google.com/maps/search/?api=1&query=55.868570,13.549973) | 0.2079 | none | 2 | 5 | 0 | 112 | 37147 | 24 | 3 |
| 16 | Jämningen | [56.297527, 14.314794](https://www.google.com/maps/search/?api=1&query=56.297527,14.314794) | 0.2068 | none | 3 | 6 | 0 | 49 | 29588 | 24 | 3 |
| 17 | Norr-Lången | [61.810118, 16.426007](https://www.google.com/maps/search/?api=1&query=61.810118,16.426007) | 0.2044 | none | 2 | 2 | 0 | 30 | 13765 | 3 | 4 |
| 18 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 0.1981 | none | 0 | 0 | 0 | 14 | 27226 | 2 | 3 |
| 19 | Långetjärn | [57.723622, 12.359070](https://www.google.com/maps/search/?api=1&query=57.723622,12.359070) | 0.1917 | none | 1 | 1 | 0 | 48 | 46255 | 2 | 4 |
| 20 | Rummehölj | [57.017085, 16.089132](https://www.google.com/maps/search/?api=1&query=57.017085,16.089132) | 0.1698 | none | 0 | 0 | 0 | 22 | 24492 | 8 | 3 |

## 50 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.7829 | none | 11 | 158 | 0 | 55 | 25127 | 6 | 4 |
| 2 | Mullsjön | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 0.7579 | none | 11 | 158 | 0 | 76 | 40833 | 9 | 4 |
| 3 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6890 | none | 11 | 158 | 0 | 60 | 38291 | 6 | 4 |
| 4 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.6576 | none | 13 | 31 | 0 | 201 | 19997 | 42 | 4 |
| 5 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 0.6224 | none | 12 | 30 | 0 | 170 | 11085 | 37 | 4 |
| 6 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 0.5698 | none | 12 | 30 | 0 | 155 | 11085 | 37 | 4 |
| 7 | Sigvaldeträsk | [57.341825, 18.527093](https://www.google.com/maps/search/?api=1&query=57.341825,18.527093) | 0.5516 | none | 11 | 91 | 0 | 84 | 13558 | 3 | 4 |
| 8 | Havgårdssjön | [55.483143, 13.357760](https://www.google.com/maps/search/?api=1&query=55.483143,13.357760) | 0.5007 | none | 13 | 31 | 0 | 182 | 11085 | 35 | 3 |
| 9 | Östra Ringsjön | [55.868570, 13.549973](https://www.google.com/maps/search/?api=1&query=55.868570,13.549973) | 0.4333 | none | 10 | 16 | 0 | 205 | 37147 | 54 | 3 |
| 10 | Rummehölj | [57.017085, 16.089132](https://www.google.com/maps/search/?api=1&query=57.017085,16.089132) | 0.2934 | none | 2 | 33 | 0 | 61 | 24492 | 12 | 4 |
| 11 | Lilla Sjö | [56.281643, 13.924259](https://www.google.com/maps/search/?api=1&query=56.281643,13.924259) | 0.2690 | none | 3 | 6 | 0 | 73 | 29588 | 50 | 4 |
| 12 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 0.2629 | none | 1 | 6 | 0 | 23 | 46236 | 31 | 4 |
| 13 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 0.2583 | none | 1 | 1 | 0 | 31 | 12008 | 8 | 4 |
| 14 | Bergakyllen | [57.186058, 16.143141](https://www.google.com/maps/search/?api=1&query=57.186058,16.143141) | 0.2393 | none | 1 | 32 | 0 | 23 | 24492 | 8 | 4 |
| 15 | Klogöl | [57.195047, 16.149861](https://www.google.com/maps/search/?api=1&query=57.195047,16.149861) | 0.2393 | none | 1 | 32 | 0 | 23 | 24492 | 8 | 4 |
| 16 | Lindhultsgöl | [57.145223, 14.467660](https://www.google.com/maps/search/?api=1&query=57.145223,14.467660) | 0.2360 | none | 1 | 6 | 0 | 23 | 46236 | 30 | 4 |
| 17 | Stömnesjön | [61.807180, 16.512573](https://www.google.com/maps/search/?api=1&query=61.807180,16.512573) | 0.2339 | none | 2 | 2 | 0 | 37 | 13765 | 3 | 4 |
| 18 | Finjasjön | [56.135794, 13.702733](https://www.google.com/maps/search/?api=1&query=56.135794,13.702733) | 0.2336 | none | 3 | 6 | 0 | 86 | 37147 | 42 | 3 |
| 19 | Ungtjärnen | [60.089033, 15.850291](https://www.google.com/maps/search/?api=1&query=60.089033,15.850291) | 0.2265 | none | 1 | 1 | 0 | 24 | 31574 | 3 | 4 |
| 20 | Jämningen | [56.297527, 14.314794](https://www.google.com/maps/search/?api=1&query=56.297527,14.314794) | 0.2106 | none | 3 | 6 | 0 | 69 | 35437 | 34 | 3 |

# Sweden lake evidence richness

This report ranks Sweden lake candidates by the richness of tracked pollen, archaeology, human aDNA, and domesticated-animal aDNA evidence around each lake. The ranking keeps lake identity diagnostics visible so duplicate names and registry naming cautions are not hidden inside one synthetic lake label.

Coordinates resolve to representative points drawn from official SMHI SVAR lake polygons, so map checks land on the lake itself rather than on a synthetic centroid or on one supporting pollen record.

## Methodology

- Candidate derivation: Candidates come from the Sweden lake registry published through SMHI SVAR. Each candidate uses a representative point derived from the official lake polygon instead of a pollen-point centroid. Only lakes with at least one human aDNA locality within 50 km remain in the ranked set. Registry names that clearly describe engineered water bodies or wetlands instead of sampling lakes are kept out of the shortlist.
- Distance bands: 10 km, 20 km, 30 km, 40 km, 50 km
- Identity diagnostics: duplicate Sweden lake names stay explicit, and registry names that do not come from the official register field remain flagged for review
- Coordinate targeting: each lake keeps one representative point derived from the official lake polygon, with registry identifiers and name status carried into the CSV, JSON, and map popups
- Human aDNA weighting: human aDNA contributes 0.52 of each band score, pollen contributes 0.22, and archaeology contributes 0.09
- Sampling note: Lake suitability remains separate from evidence density. Very small basins stay visible but score lower, while registry names that clearly point to wetlands, pits, ponds, or engineered water bodies do not enter the ranked shortlist.
- Archaeology note: SEAD contributes site-level point counts. RAÄ contributes coarse density cells, so the archaeology term measures surrounding evidence richness rather than exact site-to-lake proximity.
- Pollen note: Direct pollen signal reflects lake-basin pollen records placed on or very near the official lake, while nearby pollen signal captures additional pollen context within the active distance band.
- Animal note: Domesticated animal aDNA remains a secondary contextual signal. Human aDNA is the decisive ranking term, pollen is secondary, and archaeology resolves ties among similarly sampled lakes.

## Aggregate Ranking

| Rank | Lake | Coordinates | Lake registry id | Name status | Aggregate score | Top-20 scenario presence | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 645548-136373 | water_surface_name | 0.5569 | 5/7 | duplicate_sweden_name | none | 9 | 15 | 0 |
| 2 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 644831-136156 | water_surface_name | 0.5548 | 7/7 | duplicate_sweden_name | none | 9 | 15 | 0 |
| 3 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 645008-136594 | water_surface_name | 0.5452 | 4/7 | none | none | 9 | 15 | 0 |
| 4 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 646918-136677 | water_surface_name | 0.4816 | 7/7 | none | none | 11 | 19 | 0 |
| 5 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 645452-135906 | water_surface_name | 0.4482 | 3/7 | duplicate_sweden_name | none | 9 | 15 | 0 |
| 6 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 646105-135775 | water_surface_name | 0.4473 | 6/7 | duplicate_sweden_name | none | 10 | 13 | 0 |
| 7 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 0.4422 | 7/7 | none | neotoma-pollen | 5 | 15 | 0 |
| 8 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 646727-136543 | water_surface_name | 0.4232 | 4/7 | none | none | 11 | 19 | 0 |
| 9 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 661929-160809 | water_surface_name | 0.4222 | 4/7 | none | none | 10 | 37 | 1 |
| 10 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 0.4135 | 5/7 | none | landclim-sites, neotoma-pollen | 1 | 37 | 0 |
| 11 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 644206-137422 | water_surface_name | 0.4053 | 4/7 | none | none | 9 | 15 | 0 |
| 12 | Lejondalssjön | [59.541673, 17.687602](https://www.google.com/maps/search/?api=1&query=59.541673,17.687602) | 660523-160785 | water_surface_name | 0.3858 | 3/7 | none | none | 8 | 26 | 1 |
| 13 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 645824-135079 | water_surface_name | 0.3853 | 5/7 | none | none | 7 | 10 | 0 |
| 14 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 615375-137087 | water_surface_name | 0.3834 | 3/7 | none | landclim-sites, neotoma-pollen | 1 | 37 | 0 |
| 15 | Valloxen | [59.736717, 17.842415](https://www.google.com/maps/search/?api=1&query=59.736717,17.842415) | 662383-161313 | water_surface_name | 0.3662 | 3/7 | none | none | 10 | 35 | 1 |
| 16 | Stora Eketången | [58.213563, 13.255281](https://www.google.com/maps/search/?api=1&query=58.213563,13.255281) | 645713-135007 | water_surface_name | 0.3660 | 3/7 | none | none | 7 | 9 | 0 |
| 17 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 647133-138139 | water_surface_name | 0.3647 | 5/7 | duplicate_sweden_name | none | 2 | 8 | 0 |
| 18 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 647841-137343 | water_surface_name | 0.3642 | 4/7 | duplicate_sweden_name | none | 2 | 15 | 0 |
| 19 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 647762-137280 | water_surface_name | 0.3642 | 4/7 | duplicate_sweden_name | none | 2 | 17 | 0 |
| 20 | Rydjan | [59.607233, 17.553644](https://www.google.com/maps/search/?api=1&query=59.607233,17.553644) | 661122-159863 | water_surface_name | 0.3636 | 2/7 | none | none | 8 | 19 | 1 |

## Scenario Consensus

| Consensus rank | Lake | Coordinates | Lake registry id | Name status | Top-20 scenario presence | Best scenario rank | Mean scenario rank | Aggregate rank | Coordinate method |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 644831-136156 | water_surface_name | 7/7 | 1 | 3.86 | 2 | svar_polygon_representative_point |
| 2 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 7/7 | 1 | 7.00 | 7 | svar_polygon_representative_point |
| 3 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 646918-136677 | water_surface_name | 7/7 | 1 | 8.29 | 4 | svar_polygon_representative_point |
| 4 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 646105-135775 | water_surface_name | 6/7 | 3 | 13.57 | 6 | svar_polygon_representative_point |
| 5 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 5/7 | 1 | 14.00 | 10 | svar_polygon_representative_point |
| 6 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 645548-136373 | water_surface_name | 5/7 | 1 | 15.57 | 1 | svar_polygon_representative_point |
| 7 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 647133-138139 | water_surface_name | 5/7 | 2 | 25.86 | 17 | svar_polygon_representative_point |
| 8 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 645824-135079 | water_surface_name | 5/7 | 12 | 48.29 | 13 | svar_polygon_representative_point |
| 9 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 645008-136594 | water_surface_name | 4/7 | 1 | 20.86 | 3 | svar_polygon_representative_point |
| 10 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 644206-137422 | water_surface_name | 4/7 | 5 | 27.29 | 11 | svar_polygon_representative_point |
| 11 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 647841-137343 | water_surface_name | 4/7 | 11 | 30.14 | 18 | svar_polygon_representative_point |
| 12 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 647762-137280 | water_surface_name | 4/7 | 10 | 30.43 | 19 | svar_polygon_representative_point |
| 13 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 661929-160809 | water_surface_name | 4/7 | 5 | 60.86 | 9 | svar_polygon_representative_point |
| 14 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 646727-136543 | water_surface_name | 4/7 | 2 | 86.57 | 8 | svar_polygon_representative_point |
| 15 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 645452-135906 | water_surface_name | 3/7 | 5 | 28.83 | 5 | svar_polygon_representative_point |
| 16 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 647843-137307 | water_surface_name | 3/7 | 8 | 36.43 | 31 | svar_polygon_representative_point |
| 17 | Valloxen | [59.736717, 17.842415](https://www.google.com/maps/search/?api=1&query=59.736717,17.842415) | 662383-161313 | water_surface_name | 3/7 | 8 | 52.86 | 15 | svar_polygon_representative_point |
| 18 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 615375-137087 | water_surface_name | 3/7 | 5 | 54.71 | 14 | svar_polygon_representative_point |
| 19 | Lejondalssjön | [59.541673, 17.687602](https://www.google.com/maps/search/?api=1&query=59.541673,17.687602) | 660523-160785 | water_surface_name | 3/7 | 4 | 59.71 | 12 | svar_polygon_representative_point |
| 20 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 649459-137568 | water_surface_name | 3/7 | 1 | 67.29 | 30 | svar_polygon_representative_point |

## Fieldwork Shortlist

| Fieldwork rank | Lake | Coordinates | Lake registry id | Name status | Shortlist score | Sampling posture | Sampling fit | Area km² | Human localities within 20 km | Evidence families within 20 km |
| ---: | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 644831-136156 | water_surface_name | 0.5911 | sampling_lake_candidate | 1.0000 | 0.603 | 9 | 2 |
| 2 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 0.5601 | sampling_lake_candidate | 1.0000 | 0.759 | 1 | 4 |
| 3 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 645548-136373 | water_surface_name | 0.5497 | compact_lake_candidate | 0.6300 | 0.063 | 9 | 3 |
| 4 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 646918-136677 | water_surface_name | 0.5397 | sampling_lake_candidate | 0.9400 | 27.926 | 11 | 3 |
| 5 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 615375-137087 | water_surface_name | 0.5375 | sampling_lake_candidate | 1.0000 | 2.051 | 1 | 4 |
| 6 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 646105-135775 | water_surface_name | 0.5230 | sampling_lake_candidate | 1.0000 | 0.957 | 10 | 3 |
| 7 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 0.5012 | compact_lake_candidate | 0.6300 | 0.133 | 5 | 4 |
| 8 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 645008-136594 | water_surface_name | 0.4879 | small_lake_review | 0.3600 | 0.038 | 9 | 2 |
| 9 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 649459-137568 | water_surface_name | 0.4862 | sampling_lake_candidate | 0.8680 | 0.166 | 2 | 4 |
| 10 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 661929-160809 | water_surface_name | 0.4843 | sampling_lake_candidate | 0.8680 | 0.191 | 10 | 3 |
| 11 | Lejondalssjön | [59.541673, 17.687602](https://www.google.com/maps/search/?api=1&query=59.541673,17.687602) | 660523-160785 | water_surface_name | 0.4644 | sampling_lake_candidate | 1.0000 | 2.717 | 8 | 2 |
| 12 | Valloxen | [59.736717, 17.842415](https://www.google.com/maps/search/?api=1&query=59.736717,17.842415) | 662383-161313 | water_surface_name | 0.4621 | sampling_lake_candidate | 1.0000 | 2.787 | 10 | 3 |
| 13 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 647133-138139 | water_surface_name | 0.4610 | sampling_lake_candidate | 1.0000 | 0.504 | 2 | 3 |
| 14 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 644206-137422 | water_surface_name | 0.4592 | sampling_lake_candidate | 0.8680 | 0.155 | 9 | 2 |
| 15 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 646727-136543 | water_surface_name | 0.4494 | compact_lake_candidate | 0.6300 | 0.104 | 11 | 3 |
| 16 | Yddingesjön | [55.544521, 13.251816](https://www.google.com/maps/search/?api=1&query=55.544521,13.251816) | 616141-133891 | water_surface_name | 0.4470 | sampling_lake_candidate | 1.0000 | 1.961 | 9 | 3 |
| 17 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 645824-135079 | water_surface_name | 0.4442 | sampling_lake_candidate | 0.8680 | 0.290 | 7 | 2 |
| 18 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 647841-137343 | water_surface_name | 0.4408 | sampling_lake_candidate | 0.8680 | 0.325 | 2 | 3 |
| 19 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 647762-137280 | water_surface_name | 0.4408 | sampling_lake_candidate | 0.8680 | 0.211 | 2 | 3 |
| 20 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 647843-137307 | water_surface_name | 0.4403 | sampling_lake_candidate | 1.0000 | 1.199 | 2 | 3 |

## 10 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 0.5819 | none | 9 | 126 | 0 | 10 | 10501 | 0 | 2 |
| 2 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 0.5739 | duplicate_sweden_name | 8 | 125 | 0 | 9 | 10501 | 0 | 2 |
| 3 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.5143 | duplicate_sweden_name | 7 | 99 | 0 | 6 | 10501 | 0 | 2 |
| 4 | Lejondalssjön | [59.541673, 17.687602](https://www.google.com/maps/search/?api=1&query=59.541673,17.687602) | 0.3572 | none | 7 | 24 | 0 | 7 | 27450 | 0 | 2 |
| 5 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 0.3522 | none | 7 | 24 | 0 | 11 | 27450 | 0 | 2 |
| 6 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 0.3475 | none | 0 | 0 | 0 | 18 | 6654 | 16 | 3 |
| 7 | Rydjan | [59.607233, 17.553644](https://www.google.com/maps/search/?api=1&query=59.607233,17.553644) | 0.3290 | none | 7 | 24 | 0 | 8 | 27450 | 0 | 2 |
| 8 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 0.3220 | duplicate_sweden_name | 4 | 75 | 0 | 5 | 10501 | 0 | 2 |
| 9 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 0.2905 | none | 0 | 0 | 0 | 19 | 6654 | 16 | 3 |
| 10 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.2752 | none | 0 | 0 | 0 | 4 | 6654 | 5 | 3 |
| 11 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.2630 | none | 2 | 32 | 0 | 0 | 10501 | 1 | 4 |
| 12 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 0.2608 | none | 0 | 0 | 0 | 2 | 12008 | 4 | 3 |
| 13 | Åbodasjön | [57.085667, 14.482671](https://www.google.com/maps/search/?api=1&query=57.085667,14.482671) | 0.2454 | none | 0 | 0 | 0 | 0 | 18884 | 6 | 3 |
| 14 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.2410 | none | 0 | 0 | 0 | 1 | 10501 | 3 | 3 |
| 15 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 0.2361 | none | 2 | 32 | 0 | 1 | 10501 | 1 | 3 |
| 16 | Ämten (58.435871, 13.664187) | [58.435871, 13.664187](https://www.google.com/maps/search/?api=1&query=58.435871,13.664187) | 0.2361 | duplicate_sweden_name | 2 | 32 | 0 | 1 | 10501 | 1 | 3 |
| 17 | Flämsjön (58.451139, 13.674129) | [58.451139, 13.674129](https://www.google.com/maps/search/?api=1&query=58.451139,13.674129) | 0.2348 | duplicate_sweden_name | 2 | 32 | 0 | 0 | 10501 | 1 | 3 |
| 18 | Ungen | [60.100336, 15.838505](https://www.google.com/maps/search/?api=1&query=60.100336,15.838505) | 0.2327 | none | 0 | 0 | 0 | 1 | 8227 | 2 | 3 |
| 19 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.2300 | none | 2 | 32 | 0 | 0 | 10501 | 1 | 3 |
| 20 | Araslövssjön | [56.059934, 14.119041](https://www.google.com/maps/search/?api=1&query=56.059934,14.119041) | 0.2263 | none | 3 | 6 | 0 | 16 | 29588 | 0 | 2 |

## 20 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.6374 | none | 11 | 158 | 0 | 19 | 10501 | 2 | 3 |
| 2 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 0.6095 | none | 11 | 158 | 0 | 19 | 10501 | 1 | 3 |
| 3 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.5581 | duplicate_sweden_name | 10 | 127 | 0 | 13 | 10501 | 1 | 3 |
| 4 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.5323 | duplicate_sweden_name | 9 | 126 | 0 | 15 | 19088 | 0 | 2 |
| 5 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 0.5241 | none | 9 | 126 | 0 | 15 | 22903 | 0 | 2 |
| 6 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 0.5066 | duplicate_sweden_name | 9 | 126 | 0 | 15 | 10501 | 1 | 3 |
| 7 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 0.4811 | none | 9 | 126 | 0 | 15 | 19088 | 0 | 2 |
| 8 | Valloxen | [59.736717, 17.842415](https://www.google.com/maps/search/?api=1&query=59.736717,17.842415) | 0.4715 | none | 10 | 31 | 1 | 35 | 38213 | 0 | 3 |
| 9 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 0.4687 | duplicate_sweden_name | 9 | 126 | 0 | 15 | 10501 | 0 | 2 |
| 10 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 0.4622 | none | 10 | 31 | 1 | 37 | 38213 | 0 | 3 |
| 11 | Säbysjön (59.709756, 17.818598) | [59.709756, 17.818598](https://www.google.com/maps/search/?api=1&query=59.709756,17.818598) | 0.4603 | duplicate_sweden_name | 10 | 31 | 1 | 34 | 38213 | 0 | 3 |
| 12 | Börringesjön | [55.485153, 13.313577](https://www.google.com/maps/search/?api=1&query=55.485153,13.313577) | 0.4397 | none | 11 | 28 | 0 | 55 | 7880 | 6 | 3 |
| 13 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 0.4265 | none | 7 | 99 | 0 | 10 | 17822 | 0 | 2 |
| 14 | Brantshammarssjön | [59.731067, 17.733493](https://www.google.com/maps/search/?api=1&query=59.731067,17.733493) | 0.4246 | none | 10 | 31 | 1 | 42 | 38213 | 0 | 3 |
| 15 | Stora Eketången | [58.213563, 13.255281](https://www.google.com/maps/search/?api=1&query=58.213563,13.255281) | 0.4069 | none | 7 | 99 | 0 | 9 | 17822 | 0 | 2 |
| 16 | Norrviken (59.497651, 17.966775) | [59.497651, 17.966775](https://www.google.com/maps/search/?api=1&query=59.497651,17.966775) | 0.4069 | duplicate_sweden_name | 10 | 27 | 0 | 49 | 38213 | 0 | 2 |
| 17 | Översjön (59.455344, 17.845430) | [59.455344, 17.845430](https://www.google.com/maps/search/?api=1&query=59.455344,17.845430) | 0.4018 | duplicate_sweden_name | 10 | 27 | 0 | 58 | 38213 | 0 | 2 |
| 18 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.4010 | none | 5 | 81 | 0 | 15 | 10501 | 2 | 4 |
| 19 | Edssjön | [59.502036, 17.876831](https://www.google.com/maps/search/?api=1&query=59.502036,17.876831) | 0.3983 | none | 10 | 27 | 0 | 35 | 38213 | 0 | 2 |
| 20 | Åmossarna (55.431689, 13.155614) | [55.431689, 13.155614](https://www.google.com/maps/search/?api=1&query=55.431689,13.155614) | 0.3947 | duplicate_sweden_name | 11 | 28 | 0 | 55 | 7880 | 1 | 3 |

## 30 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6421 | none | 11 | 158 | 0 | 34 | 14316 | 5 | 4 |
| 2 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 0.6145 | duplicate_sweden_name | 11 | 158 | 0 | 31 | 14316 | 6 | 3 |
| 3 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.6109 | duplicate_sweden_name | 11 | 158 | 0 | 31 | 26409 | 1 | 3 |
| 4 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.6066 | duplicate_sweden_name | 11 | 158 | 0 | 21 | 26409 | 1 | 3 |
| 5 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.6051 | none | 11 | 158 | 0 | 34 | 14316 | 3 | 3 |
| 6 | Vingasjön | [58.381062, 13.582006](https://www.google.com/maps/search/?api=1&query=58.381062,13.582006) | 0.6041 | none | 11 | 158 | 0 | 36 | 14316 | 5 | 3 |
| 7 | Husgärdessjön | [58.393140, 13.605399](https://www.google.com/maps/search/?api=1&query=58.393140,13.605399) | 0.6037 | none | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 8 | Ökullasjön | [58.389091, 13.617191](https://www.google.com/maps/search/?api=1&query=58.389091,13.617191) | 0.6037 | none | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 9 | Bysjön (58.405310, 13.608083) | [58.405310, 13.608083](https://www.google.com/maps/search/?api=1&query=58.405310,13.608083) | 0.6037 | duplicate_sweden_name | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 10 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 0.6033 | duplicate_sweden_name | 11 | 158 | 0 | 34 | 14316 | 5 | 3 |
| 11 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 0.6024 | duplicate_sweden_name | 11 | 158 | 0 | 32 | 14316 | 5 | 3 |
| 12 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 0.6008 | none | 11 | 158 | 0 | 22 | 34978 | 1 | 3 |
| 13 | Måsjön (58.401821, 13.625023) | [58.401821, 13.625023](https://www.google.com/maps/search/?api=1&query=58.401821,13.625023) | 0.5847 | duplicate_sweden_name | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 14 | Gårdssjön (58.398292, 13.626305) | [58.398292, 13.626305](https://www.google.com/maps/search/?api=1&query=58.398292,13.626305) | 0.5847 | duplicate_sweden_name | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 15 | Tåsjön (58.395428, 13.633404) | [58.395428, 13.633404](https://www.google.com/maps/search/?api=1&query=58.395428,13.633404) | 0.5842 | duplicate_sweden_name | 11 | 158 | 0 | 34 | 14316 | 5 | 3 |
| 16 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 0.5840 | none | 11 | 158 | 0 | 34 | 21637 | 3 | 3 |
| 17 | Djupasjön (58.224080, 13.853942) | [58.224080, 13.853942](https://www.google.com/maps/search/?api=1&query=58.224080,13.853942) | 0.5828 | duplicate_sweden_name | 11 | 158 | 0 | 20 | 30970 | 3 | 3 |
| 18 | Stora Eketången | [58.213563, 13.255281](https://www.google.com/maps/search/?api=1&query=58.213563,13.255281) | 0.5814 | none | 11 | 158 | 0 | 21 | 34978 | 1 | 3 |
| 19 | Hallasjön (58.220512, 13.245042) | [58.220512, 13.245042](https://www.google.com/maps/search/?api=1&query=58.220512,13.245042) | 0.5809 | duplicate_sweden_name | 11 | 158 | 0 | 20 | 34978 | 1 | 3 |
| 20 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 0.5791 | duplicate_sweden_name | 11 | 158 | 0 | 26 | 26409 | 1 | 3 |

## 40 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.6528 | none | 13 | 31 | 0 | 165 | 11085 | 41 | 4 |
| 2 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6364 | none | 11 | 158 | 0 | 44 | 30224 | 6 | 4 |
| 3 | Havstenasjön | [58.404997, 13.843492](https://www.google.com/maps/search/?api=1&query=58.404997,13.843492) | 0.6289 | none | 11 | 158 | 0 | 47 | 14316 | 6 | 4 |
| 4 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.6116 | duplicate_sweden_name | 11 | 158 | 0 | 47 | 38793 | 5 | 3 |
| 5 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.6062 | duplicate_sweden_name | 11 | 158 | 0 | 34 | 46860 | 2 | 3 |
| 6 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 0.6050 | duplicate_sweden_name | 11 | 158 | 0 | 46 | 22903 | 6 | 3 |
| 7 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.6040 | none | 11 | 158 | 0 | 46 | 30224 | 6 | 3 |
| 8 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 0.6040 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 9 | Ämten (58.435871, 13.664187) | [58.435871, 13.664187](https://www.google.com/maps/search/?api=1&query=58.435871,13.664187) | 0.6040 | duplicate_sweden_name | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 10 | Flämsjön (58.451139, 13.674129) | [58.451139, 13.674129](https://www.google.com/maps/search/?api=1&query=58.451139,13.674129) | 0.6037 | duplicate_sweden_name | 11 | 158 | 0 | 44 | 21637 | 6 | 3 |
| 11 | Vingasjön | [58.381062, 13.582006](https://www.google.com/maps/search/?api=1&query=58.381062,13.582006) | 0.5941 | none | 11 | 158 | 0 | 47 | 21637 | 6 | 3 |
| 12 | Bysjön (58.405310, 13.608083) | [58.405310, 13.608083](https://www.google.com/maps/search/?api=1&query=58.405310,13.608083) | 0.5938 | duplicate_sweden_name | 11 | 158 | 0 | 46 | 21637 | 6 | 3 |
| 13 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 0.5935 | duplicate_sweden_name | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 14 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 0.5935 | duplicate_sweden_name | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 15 | Husgärdessjön | [58.393140, 13.605399](https://www.google.com/maps/search/?api=1&query=58.393140,13.605399) | 0.5935 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 16 | Ökullasjön | [58.389091, 13.617191](https://www.google.com/maps/search/?api=1&query=58.389091,13.617191) | 0.5935 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 17 | Eggbysjön | [58.424749, 13.648948](https://www.google.com/maps/search/?api=1&query=58.424749,13.648948) | 0.5935 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 18 | Lilla Bjursjön (58.492963, 13.678407) | [58.492963, 13.678407](https://www.google.com/maps/search/?api=1&query=58.492963,13.678407) | 0.5929 | duplicate_sweden_name | 11 | 158 | 0 | 43 | 21637 | 6 | 3 |
| 19 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 0.5927 | none | 11 | 158 | 0 | 44 | 34978 | 2 | 3 |
| 20 | Stora Bjursjön (58.498962, 13.682803) | [58.498962, 13.682803](https://www.google.com/maps/search/?api=1&query=58.498962,13.682803) | 0.5925 | duplicate_sweden_name | 11 | 158 | 0 | 42 | 21637 | 6 | 3 |

## 50 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.7139 | none | 11 | 158 | 0 | 55 | 25127 | 6 | 4 |
| 2 | Mullsjön (58.317875, 14.210785) | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 0.6916 | duplicate_sweden_name | 11 | 158 | 0 | 76 | 40833 | 9 | 4 |
| 3 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6241 | none | 11 | 158 | 0 | 60 | 38291 | 6 | 4 |
| 4 | Havstenasjön | [58.404997, 13.843492](https://www.google.com/maps/search/?api=1&query=58.404997,13.843492) | 0.6232 | none | 11 | 158 | 0 | 57 | 38291 | 6 | 4 |
| 5 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.6221 | none | 13 | 31 | 0 | 201 | 19997 | 42 | 4 |
| 6 | Sandhemssjön | [57.998654, 13.784093](https://www.google.com/maps/search/?api=1&query=57.998654,13.784093) | 0.6198 | none | 12 | 159 | 0 | 57 | 46860 | 8 | 3 |
| 7 | Stråken (57.972145, 13.830699) | [57.972145, 13.830699](https://www.google.com/maps/search/?api=1&query=57.972145,13.830699) | 0.6196 | duplicate_sweden_name | 12 | 159 | 0 | 56 | 46860 | 8 | 3 |
| 8 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.6146 | duplicate_sweden_name | 12 | 159 | 0 | 53 | 46860 | 5 | 3 |
| 9 | Hallsjön (58.546718, 13.698131) | [58.546718, 13.698131](https://www.google.com/maps/search/?api=1&query=58.546718,13.698131) | 0.6144 | duplicate_sweden_name | 11 | 158 | 0 | 56 | 21637 | 6 | 4 |
| 10 | Grimstorpasjön | [57.996442, 13.772821](https://www.google.com/maps/search/?api=1&query=57.996442,13.772821) | 0.6093 | none | 12 | 159 | 0 | 57 | 46860 | 8 | 3 |
| 11 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 0.6057 | none | 12 | 159 | 0 | 66 | 46860 | 4 | 3 |
| 12 | Alvasjön (58.083087, 14.121502) | [58.083087, 14.121502](https://www.google.com/maps/search/?api=1&query=58.083087,14.121502) | 0.6051 | duplicate_sweden_name | 11 | 158 | 0 | 67 | 30970 | 14 | 3 |
| 13 | Bredsjön (58.051700, 14.056272) | [58.051700, 14.056272](https://www.google.com/maps/search/?api=1&query=58.051700,14.056272) | 0.6049 | duplicate_sweden_name | 11 | 158 | 0 | 66 | 30970 | 14 | 3 |
| 14 | Gimmesjön | [58.070218, 13.881275](https://www.google.com/maps/search/?api=1&query=58.070218,13.881275) | 0.6035 | none | 12 | 159 | 0 | 61 | 30970 | 9 | 3 |
| 15 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.5991 | duplicate_sweden_name | 11 | 158 | 0 | 55 | 46860 | 6 | 3 |
| 16 | Hornsjön (57.979319, 14.022368) | [57.979319, 14.022368](https://www.google.com/maps/search/?api=1&query=57.979319,14.022368) | 0.5970 | duplicate_sweden_name | 11 | 158 | 0 | 59 | 30970 | 17 | 3 |
| 17 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 0.5961 | duplicate_sweden_name | 11 | 158 | 0 | 61 | 38291 | 6 | 3 |
| 18 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.5955 | none | 11 | 158 | 0 | 60 | 46860 | 6 | 3 |
| 19 | Nordvättnen | [58.056502, 14.071951](https://www.google.com/maps/search/?api=1&query=58.056502,14.071951) | 0.5946 | none | 11 | 158 | 0 | 67 | 30970 | 14 | 3 |
| 20 | Sörvättnen | [58.048397, 14.072735](https://www.google.com/maps/search/?api=1&query=58.048397,14.072735) | 0.5946 | none | 11 | 158 | 0 | 67 | 30970 | 14 | 3 |

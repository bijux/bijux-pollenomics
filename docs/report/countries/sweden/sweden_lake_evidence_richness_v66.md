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
- Sampling note: Lake suitability remains separate from evidence density. Very small basins stay visible but score lower, while registry names that clearly point to wetlands, pits, ponds, or engineered water bodies do not enter the ranked shortlist.
- Archaeology note: SEAD contributes site-level point counts and gains stronger weight when those site spans are numerically comparable and overlap nearby human locality windows. RAÄ contributes coarse density cells, so the archaeology term still measures surrounding evidence richness rather than exact site-to-lake proximity.
- Pollen note: Direct pollen signal reflects lake-basin pollen records placed on or very near the official lake. Nearby pollen signal then adds broader pollen context within the active distance band, with extra credit when those pollen records carry comparable chronology that overlaps nearby human localities.
- Animal note: Domesticated animal aDNA remains a secondary contextual signal. Human aDNA is the decisive ranking term, direct pollen is the next tie-break, and archaeology resolves ties among similarly sampled lakes.

## Aggregate Ranking

| Rank | Lake | Coordinates | Lake registry id | Name status | Aggregate score | Top-20 scenario presence | Identity diagnostics | Pollen sources | Human localities within 20 km | SEAD sites within 20 km | Domesticated animal localities within 50 km |
| ---: | --- | --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 645548-136373 | water_surface_name | 0.5947 | 4/7 | duplicate_sweden_name | none | 9 | 15 | 0 |
| 2 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 645008-136594 | water_surface_name | 0.5875 | 3/7 | none | none | 9 | 15 | 0 |
| 3 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 644831-136156 | water_surface_name | 0.5862 | 7/7 | duplicate_sweden_name | none | 9 | 15 | 0 |
| 4 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 646918-136677 | water_surface_name | 0.5037 | 6/7 | none | none | 11 | 19 | 0 |
| 5 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 645452-135906 | water_surface_name | 0.4818 | 3/7 | duplicate_sweden_name | none | 9 | 15 | 0 |
| 6 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 646105-135775 | water_surface_name | 0.4651 | 6/7 | duplicate_sweden_name | none | 10 | 13 | 0 |
| 7 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 0.4573 | 6/7 | none | neotoma-pollen | 5 | 15 | 0 |
| 8 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 646727-136543 | water_surface_name | 0.4433 | 3/7 | none | none | 11 | 19 | 0 |
| 9 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 644206-137422 | water_surface_name | 0.4186 | 4/7 | none | none | 9 | 15 | 0 |
| 10 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 661929-160809 | water_surface_name | 0.4053 | 4/7 | none | none | 10 | 37 | 1 |
| 11 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 645824-135079 | water_surface_name | 0.3983 | 4/7 | none | none | 7 | 10 | 0 |
| 12 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 0.3859 | 4/7 | none | landclim-sites, neotoma-pollen | 1 | 37 | 0 |
| 13 | Stora Eketången | [58.213563, 13.255281](https://www.google.com/maps/search/?api=1&query=58.213563,13.255281) | 645713-135007 | water_surface_name | 0.3816 | 3/7 | none | none | 7 | 9 | 0 |
| 14 | Lejondalssjön | [59.541673, 17.687602](https://www.google.com/maps/search/?api=1&query=59.541673,17.687602) | 660523-160785 | water_surface_name | 0.3767 | 3/7 | none | none | 8 | 26 | 1 |
| 15 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 647762-137280 | water_surface_name | 0.3725 | 4/7 | duplicate_sweden_name | none | 2 | 17 | 0 |
| 16 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 647841-137343 | water_surface_name | 0.3725 | 4/7 | duplicate_sweden_name | none | 2 | 15 | 0 |
| 17 | Husgärdessjön | [58.393140, 13.605399](https://www.google.com/maps/search/?api=1&query=58.393140,13.605399) | 647609-137150 | water_surface_name | 0.3711 | 3/7 | none | none | 2 | 17 | 0 |
| 18 | Bysjön (58.405310, 13.608083) | [58.405310, 13.608083](https://www.google.com/maps/search/?api=1&query=58.405310,13.608083) | 647753-137164 | water_surface_name | 0.3710 | 4/7 | duplicate_sweden_name | none | 2 | 17 | 0 |
| 19 | Ökullasjön | [58.389091, 13.617191](https://www.google.com/maps/search/?api=1&query=58.389091,13.617191) | 647620-137198 | water_surface_name | 0.3710 | 3/7 | none | none | 2 | 16 | 0 |
| 20 | Vingasjön | [58.381062, 13.582006](https://www.google.com/maps/search/?api=1&query=58.381062,13.582006) | 647484-137007 | water_surface_name | 0.3704 | 3/7 | none | none | 2 | 16 | 0 |

## Scenario Consensus

| Consensus rank | Lake | Coordinates | Lake registry id | Name status | Top-20 scenario presence | Best scenario rank | Mean scenario rank | Aggregate rank | Coordinate method |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 644831-136156 | water_surface_name | 7/7 | 2 | 4.86 | 3 | svar_polygon_representative_point |
| 2 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 646994-137366 | water_surface_name | 6/7 | 1 | 6.67 | 7 | svar_polygon_representative_point |
| 3 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 646918-136677 | water_surface_name | 6/7 | 1 | 8.43 | 4 | svar_polygon_representative_point |
| 4 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 646105-135775 | water_surface_name | 6/7 | 3 | 11.57 | 6 | svar_polygon_representative_point |
| 5 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 645548-136373 | water_surface_name | 4/7 | 1 | 20.33 | 1 | svar_polygon_representative_point |
| 6 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 4/7 | 1 | 23.86 | 12 | svar_polygon_representative_point |
| 7 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 647133-138139 | water_surface_name | 4/7 | 2 | 24.14 | 21 | svar_polygon_representative_point |
| 8 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 644206-137422 | water_surface_name | 4/7 | 5 | 24.43 | 9 | svar_polygon_representative_point |
| 9 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 647762-137280 | water_surface_name | 4/7 | 10 | 28.86 | 15 | svar_polygon_representative_point |
| 10 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 647841-137343 | water_surface_name | 4/7 | 11 | 29.83 | 16 | svar_polygon_representative_point |
| 11 | Bysjön (58.405310, 13.608083) | [58.405310, 13.608083](https://www.google.com/maps/search/?api=1&query=58.405310,13.608083) | 647753-137164 | water_surface_name | 4/7 | 7 | 29.83 | 18 | svar_polygon_representative_point |
| 12 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 647843-137307 | water_surface_name | 4/7 | 5 | 31.71 | 29 | svar_polygon_representative_point |
| 13 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 645824-135079 | water_surface_name | 4/7 | 9 | 41.29 | 11 | svar_polygon_representative_point |
| 14 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 661929-160809 | water_surface_name | 4/7 | 5 | 72.71 | 10 | svar_polygon_representative_point |
| 15 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 645008-136594 | water_surface_name | 3/7 | 1 | 21.67 | 2 | svar_polygon_representative_point |
| 16 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 645452-135906 | water_surface_name | 3/7 | 5 | 29.50 | 5 | svar_polygon_representative_point |
| 17 | Husgärdessjön | [58.393140, 13.605399](https://www.google.com/maps/search/?api=1&query=58.393140,13.605399) | 647609-137150 | water_surface_name | 3/7 | 8 | 29.67 | 17 | svar_polygon_representative_point |
| 18 | Vingasjön | [58.381062, 13.582006](https://www.google.com/maps/search/?api=1&query=58.381062,13.582006) | 647484-137007 | water_surface_name | 3/7 | 6 | 30.17 | 20 | svar_polygon_representative_point |
| 19 | Ökullasjön | [58.389091, 13.617191](https://www.google.com/maps/search/?api=1&query=58.389091,13.617191) | 647620-137198 | water_surface_name | 3/7 | 9 | 31.67 | 19 | svar_polygon_representative_point |
| 20 | Ämten (58.435871, 13.664187) | [58.435871, 13.664187](https://www.google.com/maps/search/?api=1&query=58.435871,13.664187) | 648138-137420 | water_surface_name | 3/7 | 6 | 48.00 | 39 | svar_polygon_representative_point |

## Fieldwork Shortlist

| Fieldwork rank | Lake | Coordinates | Lake registry id | Name status | Shortlist score | Sampling posture | Sampling fit | Area km² | Human localities within 20 km | Evidence families within 20 km |
| ---: | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 616410-134992 | water_surface_name | 0.6693 | sampling_lake_candidate | 1.0000 | 0.759 | 1 | 4 |
| 2 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 644831-136156 | water_surface_name | 0.6684 | sampling_lake_candidate | 1.0000 | 0.603 | 9 | 2 |
| 3 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 615375-137087 | water_surface_name | 0.6426 | sampling_lake_candidate | 1.0000 | 2.051 | 1 | 4 |
| 4 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 646918-136677 | water_surface_name | 0.6160 | sampling_lake_candidate | 0.9400 | 27.926 | 11 | 3 |
| 5 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 646105-135775 | water_surface_name | 0.6059 | sampling_lake_candidate | 1.0000 | 0.957 | 10 | 3 |
| 6 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 649459-137568 | water_surface_name | 0.6047 | sampling_lake_candidate | 0.8680 | 0.166 | 2 | 4 |
| 7 | Ungen | [60.100336, 15.838505](https://www.google.com/maps/search/?api=1&query=60.100336,15.838505) | 666556-150149 | water_surface_name | 0.5559 | sampling_lake_candidate | 1.0000 | 2.064 | 0 | 3 |
| 8 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 647133-138139 | water_surface_name | 0.5468 | sampling_lake_candidate | 1.0000 | 0.504 | 2 | 3 |
| 9 | Lejondalssjön | [59.541673, 17.687602](https://www.google.com/maps/search/?api=1&query=59.541673,17.687602) | 660523-160785 | water_surface_name | 0.5386 | sampling_lake_candidate | 1.0000 | 2.717 | 8 | 2 |
| 10 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 661929-160809 | water_surface_name | 0.5384 | sampling_lake_candidate | 0.8680 | 0.191 | 10 | 3 |
| 11 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 644206-137422 | water_surface_name | 0.5342 | sampling_lake_candidate | 0.8680 | 0.155 | 9 | 2 |
| 12 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 622492-150312 | water_surface_name | 0.5297 | sampling_lake_candidate | 0.8680 | 0.459 | 0 | 3 |
| 13 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 647843-137307 | water_surface_name | 0.5277 | sampling_lake_candidate | 1.0000 | 1.199 | 2 | 3 |
| 14 | Valloxen | [59.736717, 17.842415](https://www.google.com/maps/search/?api=1&query=59.736717,17.842415) | 662383-161313 | water_surface_name | 0.5271 | sampling_lake_candidate | 1.0000 | 2.787 | 10 | 3 |
| 15 | Yddingesjön | [55.544521, 13.251816](https://www.google.com/maps/search/?api=1&query=55.544521,13.251816) | 616141-133891 | water_surface_name | 0.5238 | sampling_lake_candidate | 1.0000 | 1.961 | 9 | 3 |
| 16 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 645824-135079 | water_surface_name | 0.5216 | sampling_lake_candidate | 0.8680 | 0.290 | 7 | 2 |
| 17 | Bredtjärnen (60.097491, 15.811442) | [60.097491, 15.811442](https://www.google.com/maps/search/?api=1&query=60.097491,15.811442) | 666434-150066 | water_surface_name | 0.5196 | sampling_lake_candidate | 0.8680 | 0.159 | 0 | 3 |
| 18 | Mullsjön (58.317875, 14.210785) | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 646681-140779 | water_surface_name | 0.5190 | sampling_lake_candidate | 1.0000 | 3.918 | 0 | 3 |
| 19 | Börringesjön | [55.485153, 13.313577](https://www.google.com/maps/search/?api=1&query=55.485153,13.313577) | 615464-134175 | water_surface_name | 0.5184 | sampling_lake_candidate | 1.0000 | 2.765 | 11 | 3 |
| 20 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 647762-137280 | water_surface_name | 0.5181 | sampling_lake_candidate | 0.8680 | 0.211 | 2 | 3 |

## 10 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 0.6332 | none | 9 | 126 | 0 | 10 | 10501 | 0 | 2 |
| 2 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 0.6194 | duplicate_sweden_name | 8 | 125 | 0 | 9 | 10501 | 0 | 2 |
| 3 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.5466 | duplicate_sweden_name | 7 | 99 | 0 | 6 | 10501 | 0 | 2 |
| 4 | Lejondalssjön | [59.541673, 17.687602](https://www.google.com/maps/search/?api=1&query=59.541673,17.687602) | 0.3588 | none | 7 | 24 | 0 | 7 | 27450 | 0 | 2 |
| 5 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 0.3524 | none | 7 | 24 | 0 | 11 | 27450 | 0 | 2 |
| 6 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 0.3444 | duplicate_sweden_name | 4 | 75 | 0 | 5 | 10501 | 0 | 2 |
| 7 | Rydjan | [59.607233, 17.553644](https://www.google.com/maps/search/?api=1&query=59.607233,17.553644) | 0.3336 | none | 7 | 24 | 0 | 8 | 27450 | 0 | 2 |
| 8 | Krageholmssjön | [55.501715, 13.744603](https://www.google.com/maps/search/?api=1&query=55.501715,13.744603) | 0.2927 | none | 0 | 0 | 0 | 18 | 6654 | 16 | 3 |
| 9 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.2599 | none | 2 | 32 | 0 | 0 | 10501 | 1 | 4 |
| 10 | Ämten (58.435871, 13.664187) | [58.435871, 13.664187](https://www.google.com/maps/search/?api=1&query=58.435871,13.664187) | 0.2445 | duplicate_sweden_name | 2 | 32 | 0 | 1 | 10501 | 1 | 3 |
| 11 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.2442 | none | 0 | 0 | 0 | 4 | 6654 | 5 | 3 |
| 12 | Flämsjön (58.451139, 13.674129) | [58.451139, 13.674129](https://www.google.com/maps/search/?api=1&query=58.451139,13.674129) | 0.2438 | duplicate_sweden_name | 2 | 32 | 0 | 0 | 10501 | 1 | 3 |
| 13 | Bjäresjö | [55.459405, 13.751743](https://www.google.com/maps/search/?api=1&query=55.459405,13.751743) | 0.2423 | none | 0 | 0 | 0 | 19 | 6654 | 16 | 3 |
| 14 | Färskesjön | [56.159037, 15.859814](https://www.google.com/maps/search/?api=1&query=56.159037,15.859814) | 0.2314 | none | 0 | 0 | 0 | 2 | 12008 | 4 | 3 |
| 15 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 0.2296 | none | 2 | 32 | 0 | 1 | 10501 | 1 | 3 |
| 16 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.2247 | none | 2 | 32 | 0 | 0 | 10501 | 1 | 3 |
| 17 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.2211 | none | 0 | 0 | 0 | 1 | 10501 | 3 | 3 |
| 18 | Ungen | [60.100336, 15.838505](https://www.google.com/maps/search/?api=1&query=60.100336,15.838505) | 0.2206 | none | 0 | 0 | 0 | 1 | 8227 | 2 | 3 |
| 19 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 0.2204 | duplicate_sweden_name | 2 | 32 | 0 | 1 | 10501 | 1 | 3 |
| 20 | Bysjön (58.405310, 13.608083) | [58.405310, 13.608083](https://www.google.com/maps/search/?api=1&query=58.405310,13.608083) | 0.2196 | duplicate_sweden_name | 2 | 32 | 0 | 0 | 10501 | 1 | 3 |

## 20 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.6809 | none | 11 | 158 | 0 | 19 | 10501 | 2 | 3 |
| 2 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 0.6563 | none | 11 | 158 | 0 | 19 | 10501 | 1 | 3 |
| 3 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.5925 | duplicate_sweden_name | 10 | 127 | 0 | 13 | 10501 | 1 | 3 |
| 4 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.5633 | duplicate_sweden_name | 9 | 126 | 0 | 15 | 19088 | 0 | 2 |
| 5 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 0.5550 | none | 9 | 126 | 0 | 15 | 22903 | 0 | 2 |
| 6 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 0.5410 | duplicate_sweden_name | 9 | 126 | 0 | 15 | 10501 | 1 | 3 |
| 7 | Hulesjön | [58.154892, 13.530245](https://www.google.com/maps/search/?api=1&query=58.154892,13.530245) | 0.5185 | none | 9 | 126 | 0 | 15 | 19088 | 0 | 2 |
| 8 | Skårsjön (58.191521, 13.409040) | [58.191521, 13.409040](https://www.google.com/maps/search/?api=1&query=58.191521,13.409040) | 0.5102 | duplicate_sweden_name | 9 | 126 | 0 | 15 | 10501 | 0 | 2 |
| 9 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 0.4484 | none | 7 | 99 | 0 | 10 | 17822 | 0 | 2 |
| 10 | Valloxen | [59.736717, 17.842415](https://www.google.com/maps/search/?api=1&query=59.736717,17.842415) | 0.4472 | none | 10 | 31 | 1 | 35 | 38213 | 0 | 3 |
| 11 | Börringesjön | [55.485153, 13.313577](https://www.google.com/maps/search/?api=1&query=55.485153,13.313577) | 0.4410 | none | 11 | 28 | 0 | 55 | 7880 | 6 | 3 |
| 12 | Alasjön | [59.686908, 17.722590](https://www.google.com/maps/search/?api=1&query=59.686908,17.722590) | 0.4386 | none | 10 | 31 | 1 | 37 | 38213 | 0 | 3 |
| 13 | Säbysjön (59.709756, 17.818598) | [59.709756, 17.818598](https://www.google.com/maps/search/?api=1&query=59.709756,17.818598) | 0.4376 | duplicate_sweden_name | 10 | 31 | 1 | 34 | 38213 | 0 | 3 |
| 14 | Stora Eketången | [58.213563, 13.255281](https://www.google.com/maps/search/?api=1&query=58.213563,13.255281) | 0.4315 | none | 7 | 99 | 0 | 9 | 17822 | 0 | 2 |
| 15 | Kroksjön (58.224560, 13.275230) | [58.224560, 13.275230](https://www.google.com/maps/search/?api=1&query=58.224560,13.275230) | 0.4129 | duplicate_sweden_name | 7 | 99 | 0 | 10 | 17822 | 0 | 2 |
| 16 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.4119 | none | 5 | 81 | 0 | 15 | 10501 | 2 | 4 |
| 17 | Borrabosjön | [58.180380, 13.259343](https://www.google.com/maps/search/?api=1&query=58.180380,13.259343) | 0.4069 | none | 7 | 99 | 0 | 11 | 17822 | 0 | 2 |
| 18 | Brantshammarssjön | [59.731067, 17.733493](https://www.google.com/maps/search/?api=1&query=59.731067,17.733493) | 0.4046 | none | 10 | 31 | 1 | 42 | 38213 | 0 | 3 |
| 19 | Åmossarna (55.431689, 13.155614) | [55.431689, 13.155614](https://www.google.com/maps/search/?api=1&query=55.431689,13.155614) | 0.4014 | duplicate_sweden_name | 11 | 28 | 0 | 55 | 7880 | 1 | 3 |
| 20 | Norrviken (59.497651, 17.966775) | [59.497651, 17.966775](https://www.google.com/maps/search/?api=1&query=59.497651,17.966775) | 0.3994 | duplicate_sweden_name | 10 | 27 | 0 | 49 | 38213 | 0 | 2 |

## 30 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6816 | none | 11 | 158 | 0 | 34 | 14316 | 5 | 4 |
| 2 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 0.6519 | duplicate_sweden_name | 11 | 158 | 0 | 31 | 14316 | 6 | 3 |
| 3 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.6444 | duplicate_sweden_name | 11 | 158 | 0 | 31 | 26409 | 1 | 3 |
| 4 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.6424 | none | 11 | 158 | 0 | 34 | 14316 | 3 | 3 |
| 5 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.6422 | duplicate_sweden_name | 11 | 158 | 0 | 21 | 26409 | 1 | 3 |
| 6 | Vingasjön | [58.381062, 13.582006](https://www.google.com/maps/search/?api=1&query=58.381062,13.582006) | 0.6418 | none | 11 | 158 | 0 | 36 | 14316 | 5 | 3 |
| 7 | Bysjön (58.405310, 13.608083) | [58.405310, 13.608083](https://www.google.com/maps/search/?api=1&query=58.405310,13.608083) | 0.6416 | duplicate_sweden_name | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 8 | Husgärdessjön | [58.393140, 13.605399](https://www.google.com/maps/search/?api=1&query=58.393140,13.605399) | 0.6416 | none | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 9 | Ökullasjön | [58.389091, 13.617191](https://www.google.com/maps/search/?api=1&query=58.389091,13.617191) | 0.6416 | none | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 10 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 0.6414 | duplicate_sweden_name | 11 | 158 | 0 | 34 | 14316 | 5 | 3 |
| 11 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 0.6409 | duplicate_sweden_name | 11 | 158 | 0 | 32 | 14316 | 5 | 3 |
| 12 | Ullstorpasjön | [58.220133, 13.269162](https://www.google.com/maps/search/?api=1&query=58.220133,13.269162) | 0.6349 | none | 11 | 158 | 0 | 22 | 34978 | 1 | 3 |
| 13 | Gårdssjön (58.398292, 13.626305) | [58.398292, 13.626305](https://www.google.com/maps/search/?api=1&query=58.398292,13.626305) | 0.6249 | duplicate_sweden_name | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 14 | Måsjön (58.401821, 13.625023) | [58.401821, 13.625023](https://www.google.com/maps/search/?api=1&query=58.401821,13.625023) | 0.6249 | duplicate_sweden_name | 11 | 158 | 0 | 35 | 14316 | 5 | 3 |
| 15 | Tåsjön (58.395428, 13.633404) | [58.395428, 13.633404](https://www.google.com/maps/search/?api=1&query=58.395428,13.633404) | 0.6247 | duplicate_sweden_name | 11 | 158 | 0 | 34 | 14316 | 5 | 3 |
| 16 | Tresjö | [58.306216, 13.507129](https://www.google.com/maps/search/?api=1&query=58.306216,13.507129) | 0.6222 | none | 11 | 158 | 0 | 34 | 21637 | 3 | 3 |
| 17 | Djupasjön (58.224080, 13.853942) | [58.224080, 13.853942](https://www.google.com/maps/search/?api=1&query=58.224080,13.853942) | 0.6209 | duplicate_sweden_name | 11 | 158 | 0 | 20 | 30970 | 3 | 3 |
| 18 | Stora Eketången | [58.213563, 13.255281](https://www.google.com/maps/search/?api=1&query=58.213563,13.255281) | 0.6180 | none | 11 | 158 | 0 | 21 | 34978 | 1 | 3 |
| 19 | Hallasjön (58.220512, 13.245042) | [58.220512, 13.245042](https://www.google.com/maps/search/?api=1&query=58.220512,13.245042) | 0.6178 | duplicate_sweden_name | 11 | 158 | 0 | 20 | 34978 | 1 | 3 |
| 20 | Bergsjön (58.201093, 13.484551) | [58.201093, 13.484551](https://www.google.com/maps/search/?api=1&query=58.201093,13.484551) | 0.6174 | duplicate_sweden_name | 11 | 158 | 0 | 26 | 26409 | 1 | 3 |

## 40 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Havstenasjön | [58.404997, 13.843492](https://www.google.com/maps/search/?api=1&query=58.404997,13.843492) | 0.6729 | none | 11 | 158 | 0 | 47 | 14316 | 6 | 4 |
| 2 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6690 | none | 11 | 158 | 0 | 44 | 30224 | 6 | 4 |
| 3 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.6384 | duplicate_sweden_name | 11 | 158 | 0 | 47 | 38793 | 5 | 3 |
| 4 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 0.6368 | duplicate_sweden_name | 11 | 158 | 0 | 46 | 22903 | 6 | 3 |
| 5 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 0.6364 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 6 | Ämten (58.435871, 13.664187) | [58.435871, 13.664187](https://www.google.com/maps/search/?api=1&query=58.435871,13.664187) | 0.6364 | duplicate_sweden_name | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 7 | Flämsjön (58.451139, 13.674129) | [58.451139, 13.674129](https://www.google.com/maps/search/?api=1&query=58.451139,13.674129) | 0.6362 | duplicate_sweden_name | 11 | 158 | 0 | 44 | 21637 | 6 | 3 |
| 8 | Hornborgasjön | [58.317269, 13.549447](https://www.google.com/maps/search/?api=1&query=58.317269,13.549447) | 0.6341 | none | 11 | 158 | 0 | 46 | 30224 | 6 | 3 |
| 9 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.6327 | duplicate_sweden_name | 11 | 158 | 0 | 34 | 46860 | 2 | 3 |
| 10 | Häckebergasjön | [55.577162, 13.422814](https://www.google.com/maps/search/?api=1&query=55.577162,13.422814) | 0.6324 | none | 13 | 31 | 0 | 165 | 11085 | 41 | 4 |
| 11 | Vingasjön | [58.381062, 13.582006](https://www.google.com/maps/search/?api=1&query=58.381062,13.582006) | 0.6275 | none | 11 | 158 | 0 | 47 | 21637 | 6 | 3 |
| 12 | Bysjön (58.405310, 13.608083) | [58.405310, 13.608083](https://www.google.com/maps/search/?api=1&query=58.405310,13.608083) | 0.6273 | duplicate_sweden_name | 11 | 158 | 0 | 46 | 21637 | 6 | 3 |
| 13 | Eggbysjön | [58.424749, 13.648948](https://www.google.com/maps/search/?api=1&query=58.424749,13.648948) | 0.6271 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 14 | Husgärdessjön | [58.393140, 13.605399](https://www.google.com/maps/search/?api=1&query=58.393140,13.605399) | 0.6271 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 15 | Ormsjön (58.410093, 13.645479) | [58.410093, 13.645479](https://www.google.com/maps/search/?api=1&query=58.410093,13.645479) | 0.6271 | duplicate_sweden_name | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 16 | Vagnsjön (58.405652, 13.628989) | [58.405652, 13.628989](https://www.google.com/maps/search/?api=1&query=58.405652,13.628989) | 0.6271 | duplicate_sweden_name | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 17 | Ökullasjön | [58.389091, 13.617191](https://www.google.com/maps/search/?api=1&query=58.389091,13.617191) | 0.6271 | none | 11 | 158 | 0 | 45 | 21637 | 6 | 3 |
| 18 | Lilla Bjursjön (58.492963, 13.678407) | [58.492963, 13.678407](https://www.google.com/maps/search/?api=1&query=58.492963,13.678407) | 0.6268 | duplicate_sweden_name | 11 | 158 | 0 | 43 | 21637 | 6 | 3 |
| 19 | Stora Bjursjön (58.498962, 13.682803) | [58.498962, 13.682803](https://www.google.com/maps/search/?api=1&query=58.498962,13.682803) | 0.6267 | duplicate_sweden_name | 11 | 158 | 0 | 42 | 21637 | 6 | 3 |
| 20 | Karstorpasjön | [58.420082, 13.852992](https://www.google.com/maps/search/?api=1&query=58.420082,13.852992) | 0.6258 | none | 11 | 158 | 0 | 46 | 14316 | 6 | 3 |

## 50 km Ranking

| Rank | Lake | Coordinates | Score | Identity diagnostics | Human localities | Human samples | Domesticated animal localities | SEAD sites | RAÄ density count | Nearby pollen lakes | Evidence families |
| ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | Flarken | [58.556811, 13.672884](https://www.google.com/maps/search/?api=1&query=58.556811,13.672884) | 0.7473 | none | 11 | 158 | 0 | 55 | 25127 | 6 | 4 |
| 2 | Mullsjön (58.317875, 14.210785) | [58.317875, 14.210785](https://www.google.com/maps/search/?api=1&query=58.317875,14.210785) | 0.7166 | duplicate_sweden_name | 11 | 158 | 0 | 76 | 40833 | 9 | 4 |
| 3 | Havstenasjön | [58.404997, 13.843492](https://www.google.com/maps/search/?api=1&query=58.404997,13.843492) | 0.6587 | none | 11 | 158 | 0 | 57 | 38291 | 6 | 4 |
| 4 | Hallsjön (58.546718, 13.698131) | [58.546718, 13.698131](https://www.google.com/maps/search/?api=1&query=58.546718,13.698131) | 0.6553 | duplicate_sweden_name | 11 | 158 | 0 | 56 | 21637 | 6 | 4 |
| 5 | Bjärsjön | [58.334534, 13.656520](https://www.google.com/maps/search/?api=1&query=58.334534,13.656520) | 0.6524 | none | 11 | 158 | 0 | 60 | 38291 | 6 | 4 |
| 6 | Sandhemssjön | [57.998654, 13.784093](https://www.google.com/maps/search/?api=1&query=57.998654,13.784093) | 0.6449 | none | 12 | 159 | 0 | 57 | 46860 | 8 | 3 |
| 7 | Stråken (57.972145, 13.830699) | [57.972145, 13.830699](https://www.google.com/maps/search/?api=1&query=57.972145,13.830699) | 0.6448 | duplicate_sweden_name | 12 | 159 | 0 | 56 | 46860 | 8 | 3 |
| 8 | Sjötorpasjön (58.141960, 13.460319) | [58.141960, 13.460319](https://www.google.com/maps/search/?api=1&query=58.141960,13.460319) | 0.6404 | duplicate_sweden_name | 12 | 159 | 0 | 53 | 46860 | 5 | 3 |
| 9 | Grimstorpasjön | [57.996442, 13.772821](https://www.google.com/maps/search/?api=1&query=57.996442,13.772821) | 0.6357 | none | 12 | 159 | 0 | 57 | 46860 | 8 | 3 |
| 10 | Gimmesjön | [58.070218, 13.881275](https://www.google.com/maps/search/?api=1&query=58.070218,13.881275) | 0.6343 | none | 12 | 159 | 0 | 61 | 30970 | 9 | 3 |
| 11 | Vartoftasjön | [58.086896, 13.669730](https://www.google.com/maps/search/?api=1&query=58.086896,13.669730) | 0.6314 | none | 12 | 159 | 0 | 66 | 46860 | 4 | 3 |
| 12 | Alvasjön (58.083087, 14.121502) | [58.083087, 14.121502](https://www.google.com/maps/search/?api=1&query=58.083087,14.121502) | 0.6314 | duplicate_sweden_name | 11 | 158 | 0 | 67 | 30970 | 14 | 3 |
| 13 | Bredsjön (58.051700, 14.056272) | [58.051700, 14.056272](https://www.google.com/maps/search/?api=1&query=58.051700,14.056272) | 0.6313 | duplicate_sweden_name | 11 | 158 | 0 | 66 | 30970 | 14 | 3 |
| 14 | Hornsjön (57.979319, 14.022368) | [57.979319, 14.022368](https://www.google.com/maps/search/?api=1&query=57.979319,14.022368) | 0.6244 | duplicate_sweden_name | 11 | 158 | 0 | 59 | 30970 | 17 | 3 |
| 15 | Rösjön (58.256624, 13.380976) | [58.256624, 13.380976](https://www.google.com/maps/search/?api=1&query=58.256624,13.380976) | 0.6225 | duplicate_sweden_name | 11 | 158 | 0 | 55 | 46860 | 6 | 3 |
| 16 | Nordvättnen | [58.056502, 14.071951](https://www.google.com/maps/search/?api=1&query=58.056502,14.071951) | 0.6222 | none | 11 | 158 | 0 | 67 | 30970 | 14 | 3 |
| 17 | Sörvättnen | [58.048397, 14.072735](https://www.google.com/maps/search/?api=1&query=58.048397,14.072735) | 0.6222 | none | 11 | 158 | 0 | 67 | 30970 | 14 | 3 |
| 18 | Simsjön (58.355667, 13.782031) | [58.355667, 13.782031](https://www.google.com/maps/search/?api=1&query=58.355667,13.782031) | 0.6215 | duplicate_sweden_name | 11 | 158 | 0 | 61 | 38291 | 6 | 3 |
| 19 | Skärvalången | [58.420796, 13.646123](https://www.google.com/maps/search/?api=1&query=58.420796,13.646123) | 0.6198 | none | 11 | 158 | 0 | 60 | 30224 | 6 | 3 |
| 20 | Ämten (58.435871, 13.664187) | [58.435871, 13.664187](https://www.google.com/maps/search/?api=1&query=58.435871,13.664187) | 0.6196 | duplicate_sweden_name | 11 | 158 | 0 | 58 | 30224 | 6 | 3 |

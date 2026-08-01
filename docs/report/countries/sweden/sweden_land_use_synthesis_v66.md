# Southern Sweden temporal land-use synthesis

This surface joins published LandClim time windows to temporally compatible
archaeology and ancient-DNA context around six named southern Sweden targets.
It also makes the lake inclusion decision explicit instead of silently dropping
wetlands or treating every named place as a coring lake.

## Governed Target Decisions

| Requested target | Class | Decision | SVAR ID | Area km² | Reason |
| --- | --- | --- | --- | ---: | --- |
| Finjasjön | registered_lake | include_lake_review | 622731-136920 | 10.497234 | Named project lake resolved to one official SVAR lake. |
| Östra Ringsjön | registered_lake | include_lake_review | 619626-135565 | 24.728453 | Named project lake resolved to one official SVAR lake. |
| Havgårdssjön | registered_lake | include_lake_review | 615365-134524 | 0.501745 | Named project lake resolved to one official SVAR lake. |
| Bjäresjösjön | registered_lake | include_lake_review | 614958-137018 | 0.022251 | Project name Bjäresjösjön resolved to the official SVAR water-surface name Bjäresjö. |
| Gullåkra | archaeological_wetland_context | exclude_lake_ranking_include_context | not_applicable | not_applicable | The named place is Gullåkra mosse in the archaeological report and has no unique SMHI SVAR lake match. It belongs in wetland and archaeology context, not the lake-sampling ranking. |
| Vesums mossar | archaeological_wetland_context | exclude_lake_ranking_include_context | not_applicable | not_applicable | The named place is Vesums mosse in the archaeological report and has no unique SMHI SVAR lake match. It belongs in wetland and archaeology context, not the lake-sampling ranking. |

Gullåkra and Vesums mossar remain in this synthesis because the Höje å
archaeological report documents them as wetland project areas with archaeological
context. They are excluded only from the lake-sampling ranking.

## Reading The Joined Evidence

- Forest is published ET plus ST cover; open land is OL; grassland is GL; and agricultural land is AL. Values are percentage cover.
- Cerealia.t and Secale retain their published modeled pollen-cover values. They are not observed crop acreage or proof of cultivation at the named target.
- SEAD and aDNA context counts require both spatial proximity within 20 km and numeric interval overlap with the published LandClim window.
- Cross-proxy alignment is descriptive context. It does not identify a cause, migration route, farming event, or viable coring location.

## Recent And Late-Holocene Windows

| Target | Window | Forest | Open land | Agricultural land | Cerealia-type pollen | Rye pollen | SEAD sites | Human aDNA localities | Animal aDNA localities | Posture |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Bjäresjösjön | 0-100 BP | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 9 | 0 | 0 | pollen_archaeology_context |
| Bjäresjösjön | 100-350 BP | 39.375 | 60.625 | 6.969 | 6.583 | 0.387 | 13 | 0 | 0 | pollen_archaeology_context |
| Bjäresjösjön | 350-700 BP | 54.728 | 45.272 | 5.596 | 5.462 | 0.134 | 20 | 0 | 0 | pollen_archaeology_context |
| Bjäresjösjön | 700-1200 BP | 49.153 | 50.847 | 2.602 | 2.530 | 0.072 | 16 | 0 | 0 | pollen_archaeology_context |
| Finjasjön | 0-100 BP | 44.300 | 55.700 | 5.950 | 2.131 | 3.819 | 2 | 0 | 0 | pollen_archaeology_context |
| Finjasjön | 100-350 BP | 29.224 | 70.776 | 22.139 | 1.319 | 20.820 | 8 | 0 | 0 | pollen_archaeology_context |
| Finjasjön | 350-700 BP | 41.969 | 58.031 | 9.690 | 0.671 | 9.019 | 8 | 0 | 0 | pollen_archaeology_context |
| Finjasjön | 700-1200 BP | 53.805 | 46.195 | 13.259 | 0.358 | 12.901 | 3 | 0 | 0 | pollen_archaeology_context |
| Gullåkra | 0-100 BP | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 4 | 0 | 0 | pollen_archaeology_context |
| Gullåkra | 100-350 BP | 39.375 | 60.625 | 6.969 | 6.583 | 0.387 | 12 | 0 | 0 | pollen_archaeology_context |
| Gullåkra | 350-700 BP | 54.728 | 45.272 | 5.596 | 5.462 | 0.134 | 26 | 0 | 0 | pollen_archaeology_context |
| Gullåkra | 700-1200 BP | 49.153 | 50.847 | 2.602 | 2.530 | 0.072 | 21 | 1 | 0 | pollen_archaeology_human_context |
| Havgårdssjön | 0-100 BP | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 12 | 0 | 0 | pollen_archaeology_context |
| Havgårdssjön | 100-350 BP | 39.375 | 60.625 | 6.969 | 6.583 | 0.387 | 15 | 0 | 0 | pollen_archaeology_context |
| Havgårdssjön | 350-700 BP | 54.728 | 45.272 | 5.596 | 5.462 | 0.134 | 26 | 0 | 0 | pollen_archaeology_context |
| Havgårdssjön | 700-1200 BP | 49.153 | 50.847 | 2.602 | 2.530 | 0.072 | 20 | 0 | 0 | pollen_archaeology_context |
| Vesums mossar | 0-100 BP | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 4 | 0 | 0 | pollen_archaeology_context |
| Vesums mossar | 100-350 BP | 39.375 | 60.625 | 6.969 | 6.583 | 0.387 | 12 | 0 | 0 | pollen_archaeology_context |
| Vesums mossar | 350-700 BP | 54.728 | 45.272 | 5.596 | 5.462 | 0.134 | 25 | 0 | 0 | pollen_archaeology_context |
| Vesums mossar | 700-1200 BP | 49.153 | 50.847 | 2.602 | 2.530 | 0.072 | 21 | 1 | 0 | pollen_archaeology_human_context |
| Östra Ringsjön | 0-100 BP | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 0 | 0 | 0 | pollen_model_only |
| Östra Ringsjön | 100-350 BP | 39.375 | 60.625 | 6.969 | 6.583 | 0.387 | 4 | 0 | 0 | pollen_archaeology_context |
| Östra Ringsjön | 350-700 BP | 54.728 | 45.272 | 5.596 | 5.462 | 0.134 | 3 | 0 | 0 | pollen_archaeology_context |
| Östra Ringsjön | 700-1200 BP | 49.153 | 50.847 | 2.602 | 2.530 | 0.072 | 2 | 0 | 0 | pollen_archaeology_context |

The machine-readable JSON and CSV retain every published window, not only the
recent subset shown here.

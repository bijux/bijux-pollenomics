# Southern Sweden temporal land-use synthesis

This surface joins published LandClim time windows to temporally compatible
archaeology and ancient-DNA context around governed named lakes, any additional
ranked Swedish lakes, and named wetland contexts. It makes both modeled-grid
coverage and lake inclusion explicit instead of silently dropping targets.

The governed LandClim grid covers **6 of 6 targets**. The remaining
**0 targets** stay visible below with
no modeled windows rather than receiving inferred values.

## Governed Target Decisions

| Requested target | Class | Decision | SVAR ID | Area km² | LandClim coverage | Windows | Reason |
| --- | --- | --- | --- | ---: | --- | ---: | --- |
| Finjasjön | registered_lake | include_lake_review | 622731-136920 | 10.497234 | covered_by_governed_grid | 25 | Named project lake resolved to one official SVAR lake. |
| Östra Ringsjön | registered_lake | include_lake_review | 619626-135565 | 24.728453 | covered_by_governed_grid | 25 | Named project lake resolved to one official SVAR lake. |
| Havgårdssjön | registered_lake | include_lake_review | 615365-134524 | 0.501745 | covered_by_governed_grid | 25 | Named project lake resolved to one official SVAR lake. |
| Bjäresjösjön | registered_lake | include_lake_review | 614958-137018 | 0.022251 | covered_by_governed_grid | 25 | Project name Bjäresjösjön resolved to the official SVAR water-surface name Bjäresjö. |
| Gullåkra | archaeological_wetland_context | exclude_lake_ranking_include_context | not_applicable | not_applicable | covered_by_governed_grid | 25 | The named place is Gullåkra mosse in the archaeological report and has no unique SMHI SVAR lake match. It belongs in wetland and archaeology context, not the lake-sampling ranking. |
| Vesums mossar | archaeological_wetland_context | exclude_lake_ranking_include_context | not_applicable | not_applicable | covered_by_governed_grid | 25 | The named place is Vesums mosse in the archaeological report and has no unique SMHI SVAR lake match. It belongs in wetland and archaeology context, not the lake-sampling ranking. |

Gullåkra and Vesums mossar remain in this synthesis because the Höje å
archaeological report documents them as wetland project areas with archaeological
context. They are excluded only from the lake-sampling ranking.

## Reading The Joined Evidence

- Forest is published ET plus ST cover; OL is open, GL is grassland, and AL is agricultural percentage cover. no_pollen_data retains the source window while all modeled cover values are unavailable.
- High- and low-quality rows retain published Cerealia.t and Secale modeled pollen-cover values; no_pollen_data retains nulls. These are not observed crop acreage or proof of cultivation at the target.
- SEAD and aDNA context counts require both spatial proximity within 20 km and numeric interval overlap with the published LandClim window.
- Every governed named lake or wetland and every additional ranked SVAR lake stays in scope. Targets outside the governed LandClim grid retain a decision row but receive no fabricated temporal values.
- Cross-proxy alignment is descriptive context. It does not identify a cause, migration route, farming event, or viable coring location.

## Most Recent Modeled Window

| Target | Window | Quality | Forest | Open land | Agricultural land | Cerealia-type pollen | Rye pollen | SEAD sites | Human aDNA localities | Animal aDNA localities | Posture |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Bjäresjösjön | 0-100 BP | high | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 0 | 0 | 0 | pollen_model_only |
| Finjasjön | 0-100 BP | high | 44.300 | 55.700 | 5.950 | 2.131 | 3.819 | 1 | 0 | 0 | pollen_archaeology_context |
| Gullåkra | 0-100 BP | high | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 0 | 0 | 0 | pollen_model_only |
| Havgårdssjön | 0-100 BP | high | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 1 | 0 | 0 | pollen_archaeology_context |
| Vesums mossar | 0-100 BP | high | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 0 | 0 | 0 | pollen_model_only |
| Östra Ringsjön | 0-100 BP | high | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 0 | 0 | 0 | pollen_model_only |

This compact table shows one recent modeled window per covered target. The
machine-readable JSON and CSV retain all **150** published
target-window rows for time navigation and analysis.

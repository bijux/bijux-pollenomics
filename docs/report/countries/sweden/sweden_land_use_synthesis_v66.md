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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Swedish observed pollen/modeled land use/archaeological context has separate provenance and no causal or ecological validation.

**Supported claim.** This six-target product joins published modeled LandClim windows to spatially nearby numeric-interval SEAD/aDNA context and retains each named lake/wetland decision.

**Unsupported claim.** Modeled percentages are not observed crop acreage; nearby dated context is not proof of cultivation,migration,causation or viable lake coring.

**Actual verification performed.** Read the machine target decisions and 150 window rows; checked sixcovered targets,zero uncovered,25 rows per target and separate lake/wetland classes. No country-report producer or ecological validation was rerun.

**Remaining input or review.** Independent measured vegetation,qualified SEAD/aDNA chronology and source admission,and physical lake/core suitability are needed for stronger historical or sampling claims.

**Cause category.** Modeled-grid synthesis with descriptive temporal/spatial context.

**Consequence.** The four modern registered lakes and two archaeological wetlands remain separate target classes; common modeled values are not six independent vegetation measurements.

**Precise next acceptance route.** Reproduce the exact source-bound six-target product,retain refused/no-data windows and contextroles,then qualify independent matched measurements before historical accuracy or causal inference.

**Negative or refused result.** Gullåkra andVesums mossar remain excluded from lake ranking while retained as archaeological wetlands;cross-proxy causal inference and crop-acreage interpretation remain refused.

**Matched denominator.** 6 targets=4 registered lakes+2 wetland contexts;25 published windows each=150 target-window rows,6/6 gridcovered,0 uncovered;20 km context requires numeric interval overlap,not mere proximity.

- [Retained qualification evidence: docs/report/countries/sweden/sweden_land_use_synthesis_v66.json](sweden_land_use_synthesis_v66.json) (SHA-256 `c9aa7a1a57aabd0673c4411677da29b8add4a8d604c5db30aab6003a2a4d0380`).

- [Retained qualification evidence: docs/report/countries/sweden/sweden_land_use_synthesis_v66.csv](sweden_land_use_synthesis_v66.csv) (SHA-256 `a534469cf5f411bd8b017b307f94784918df070e9c5d5005f1a03b0a966ed3d5`).

- [Canonical scientific account: reports/science/sweden-lake-trajectory.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sweden-lake-trajectory.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

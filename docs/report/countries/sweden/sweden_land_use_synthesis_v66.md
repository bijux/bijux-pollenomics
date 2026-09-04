# Southern Sweden temporal land-use synthesis

This surface joins published LandClim time windows to temporally compatible
archaeology and ancient-DNA context around the complete ranked Sweden lake set
and the governed southern Sweden wetland contexts. It makes both modeled-grid
coverage and lake inclusion explicit instead of silently dropping targets.

The governed LandClim grid covers **2 of
2 targets**. The remaining
**0 targets** stay visible below with
zero modeled windows rather than receiving inferred values.

## Governed Target Decisions

| Requested target | Class | Decision | SVAR ID | Area km² | LandClim coverage | Windows | Reason |
| --- | --- | --- | --- | ---: | --- | ---: | --- |
| Gullåkra | archaeological_wetland_context | exclude_lake_ranking_include_context | not_applicable | not_applicable | covered_by_governed_grid | 25 | The named place is Gullåkra mosse in the archaeological report and has no unique SMHI SVAR lake match. It belongs in wetland and archaeology context, not the lake-sampling ranking. |
| Vesums mossar | archaeological_wetland_context | exclude_lake_ranking_include_context | not_applicable | not_applicable | covered_by_governed_grid | 25 | The named place is Vesums mosse in the archaeological report and has no unique SMHI SVAR lake match. It belongs in wetland and archaeology context, not the lake-sampling ranking. |

Gullåkra and Vesums mossar remain in this synthesis because the Höje å
archaeological report documents them as wetland project areas with archaeological
context. They are excluded only from the lake-sampling ranking.

## Reading The Joined Evidence

- Forest is published ET plus ST cover; open land is OL; grassland is GL; and agricultural land is AL. Values are percentage cover.
- Cerealia.t and Secale retain their published modeled pollen-cover values. They are not observed crop acreage or proof of cultivation at the named target.
- SEAD and aDNA context counts require both spatial proximity within 20 km and numeric interval overlap with the published LandClim window.
- Every ranked SVAR lake is evaluated. Named archaeological wetland contexts remain alongside the lake set. Targets outside the governed LandClim grid retain an explicit decision row and receive no fabricated temporal values.
- Cross-proxy alignment is descriptive context. It does not identify a cause, migration route, farming event, or viable coring location.

## Most Recent Modeled Window

| Target | Window | Forest | Open land | Agricultural land | Cerealia-type pollen | Rye pollen | SEAD sites | Human aDNA localities | Animal aDNA localities | Posture |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Gullåkra | 0-100 BP | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 4 | 0 | 0 | pollen_archaeology_context |
| Vesums mossar | 0-100 BP | 56.245 | 43.755 | 5.100 | 4.641 | 0.458 | 4 | 0 | 0 | pollen_archaeology_context |

This compact table shows one recent modeled window per covered target. The
machine-readable JSON and CSV retain all **50** published
target-window rows for time navigation and analysis.

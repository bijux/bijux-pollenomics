# Europe-plus Evidence Surface

This shared interactive map bundle was generated on `2026-09-29` from Homo
sapiens AADR `v66` plus any governed contextual and animal surfaces that
the active scope contract allows.

Europe-plus is a governed regional filter view. It keeps only Europe-plus countries from the broader publication surface and still withholds Nordic-only overlays that would overstate regional context coverage.

## Included Countries

| Country | Unique samples |
| --- | ---: |
| Sweden | 416 |
| Norway | 130 |
| Finland | 32 |
| Denmark | 653 |

## Bundle Notes

- This bundle is a generated publication artifact, not a source dataset.
- Local leaflet assets are copied into `./_map_assets` so the HTML does not depend on CDN-hosted library files.
- Basemap tiles are still requested from the active cartographic provider at runtime, so an offline browser session will not display background tiles.
- The interactive map presents the records and overlays that were generated into this bundle. Ranking artifacts are published alongside it and carry stricter evidence boundaries than the map view itself.
- Default basemap: `street`
- The opening extent centers the European frame while keeping enough margin for future expansion into non-Nordic Europe-plus countries.

## Output Files

- Interactive map: [`europe-plus_map.html`](./europe-plus_map.html)
- Combined GeoJSON: [`europe-plus_samples.geojson`](./europe-plus_samples.geojson)
- Machine-readable summary: [`europe-plus_summary.json`](./europe-plus_summary.json)
- Map publication contract JSON: [`europe-plus_map_publication_contract.json`](./europe-plus_map_publication_contract.json)
- Map publication contract markdown: [`europe-plus_map_publication_contract.md`](./europe-plus_map_publication_contract.md)
- Point traceability JSON: [`europe-plus_point_traceability.json`](./europe-plus_point_traceability.json)
- Point traceability markdown: [`europe-plus_point_traceability.md`](./europe-plus_point_traceability.md)
- Nordic country boundaries: [`nordic_country_boundaries.geojson`](./nordic_country_boundaries.geojson)
- Animal locality GeoJSON: [`europe-plus_animal_localities.geojson`](./europe-plus_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`europe-plus_domesticated_animal_localities.geojson`](./europe-plus_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`europe-plus_comparator_animal_localities.geojson`](./europe-plus_comparator_animal_localities.geojson)
- Wild and progenitor animal locality GeoJSON: [`europe-plus_progenitor_animal_localities.geojson`](./europe-plus_progenitor_animal_localities.geojson)
- Animal atlas evidence CSV: [`europe-plus_animal_atlas_evidence.csv`](./europe-plus_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`europe-plus_animal_atlas_evidence.json`](./europe-plus_animal_atlas_evidence.json)
- Animal point traceability JSON: [`europe-plus_animal_point_traceability.json`](./europe-plus_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`europe-plus_map_assets.json`](./europe-plus_map_assets.json)
- Animal source-sample chronology accountability: [`europe-plus_animal_sample_chronology_context.json`](./europe-plus_animal_sample_chronology_context.json)
- Candidate site ranking CSV: [`europe-plus_candidate_sites.csv`](./europe-plus_candidate_sites.csv)
- Candidate site ranking JSON: [`europe-plus_candidate_sites.json`](./europe-plus_candidate_sites.json)
- Candidate site ranking markdown: [`europe-plus_candidate_sites.md`](./europe-plus_candidate_sites.md)
- Candidate site sensitivity JSON: [`europe-plus_candidate_site_sensitivity.json`](./europe-plus_candidate_site_sensitivity.json)
- Candidate site sensitivity markdown: [`europe-plus_candidate_site_sensitivity.md`](./europe-plus_candidate_site_sensitivity.md)
- Candidate ranking engine manifest: [`europe-plus_candidate_ranking_engine_manifest.json`](./europe-plus_candidate_ranking_engine_manifest.json)
- Atlas evidence surface JSON: [`europe-plus_evidence_surface.json`](./europe-plus_evidence_surface.json)
- Atlas evidence surface markdown: [`europe-plus_evidence_surface.md`](./europe-plus_evidence_surface.md)
- Atlas scientific review JSON: [`europe-plus_scientific_review.json`](./europe-plus_scientific_review.json)
- Atlas scientific review markdown: [`europe-plus_scientific_review.md`](./europe-plus_scientific_review.md)

JavaScript data chunks, runtime and optional controllers are listed in the [complete file inventory](./europe-plus_summary.json).

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `2` |
| Cat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Sheep source-sample chronology | `shared_world_scale_layer` |  | `4` |
| Pig source-sample chronology | `shared_world_scale_layer` |  | `2` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |

## Governed Filters

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch

## Scope Caveats

- Europe-plus is derived from the world publication surface by governed country filtering, not by a second evidence pipeline.
- Nordic-only pollen, archaeology, and fieldwork overlays remain absent here on purpose.
- Future non-Nordic Europe-plus additions should arrive by country onboarding, not by custom one-off bundle logic.


## Animal aDNA Layers

- Total animal locality points: `8`
- Shipped animal species: `3`
- Domesticated-core species layers: `2`
- Comparator species layers: `0`

### Layer Groups

- Domesticated-core animal evidence
- Comparator animal evidence
- Wild and progenitor animal evidence

### Public Animal Filters

- Species focus
- Animal scope
- Coordinate confidence
- Temporal window
- Nordic animal leads only

### Animal Inspection Surfaces

- Animal evidence summary panel
- Citation-aware animal popups
- Species and confidence legend sections

### Visible Coordinate Confidence

| Coordinate confidence | Visible mapped points |
| --- | ---: |
| approximate | 6 |
| source_reported_two_decimal_degrees | 2 |

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Wild or progenitor evidence remains visible in its own scope and is not farming support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| cattle | Bos taurus | wild_or_progenitor_context | 4 |
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The retained Europe-plus bundle filters the world publication surface to four currently represented countries and keeps source metadata, animal context and traceability alongside a shared map engine.

**Unsupported claim.** The bundle is not a second independent source collection, genotype-aware analysis, excavation recommendation, historical ecological reconstruction or vegetation validation.

**Actual verification performed.** The retained saved atlas consumer at 1b338ee91 reconciles all 1,481 normalized source records. Native map assembly at that source passed in 333.12 seconds, RSS 5,366,333,440 B; independent decoded preservation and search references passed in 35.10 seconds, RSS 708,460,544 B. All unrelated scientific payloads, dates and coordinates are preserved. Current world/Europe index factories pass; Nordic qualification is reused only after exact code, bootstrap, controller, wire and semantic equality. Actual served runtime passes 27 cases, including four contextual Qinghai dates and a recovered horse owner. Seventeen targeted reader guards pass. Prior failures and their corrections are retained; no model or source census replay. Current saved-source followthrough at `179de88d1` independently verifies all 121 corpus inputs, three sidecars and nine identity copies, unchanged 335 world/13 per-region nodes and 430 runtime files. Its 24-product consumer and independent readback pass original 60 s limits (producer 1 GiB/16 MiB; observer 512 MiB/8 MiB). Within these map products only matching input identities change; four goat provenance packets add reported paper references without specimen selection. Earlier map/index/browser qualifications retain their original epochs.

**Remaining input or review.** Source chronology, biological/locality authority and rights need their own decisions. The current shared runtime has narrow World served-temporal qualification; external provider behavior, broader browser cases and latency remain separate.

**Cause category.** Regional publication selection of metadata and context.

**Consequence.** Visible markers identify retained publication records, while Nordic-only overlays are withheld rather than generalized beyond their governed scope.

**Precise next acceptance route.** Use the source-bound current Europe-plus bundle and exact source/point identities; review any proposed scientific use separately, and measure additional provider/browser/latency behavior only for its declared claim.

**Negative or refused result.** Approximate locations and comparator/wild-progenitor animals remain cautioned; unsupported species and sampling recommendations remain refused.

**Matched denominator.** Four-country display:1,231 human samples (SE416/NO130/FI32/DK653), eight animal locality points across three species; these are publication populations, not independent ecological samples.

- [Retained qualification evidence: docs/report/regions/europe-plus/europe-plus_summary.json](europe-plus_summary.json) (SHA-256 `e44f7d7da8d577e3a43a59bc05a94dec912920806279a751c6a980c955713be8`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

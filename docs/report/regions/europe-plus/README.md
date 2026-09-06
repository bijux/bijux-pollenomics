# Europe-plus Evidence Surface

This shared interactive map bundle was generated on `2026-09-06` from Homo
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
- Static atlas data chunk: [`europe-plus.atlas-provenance.0000.395ff9dddcbce4eb.js`](./europe-plus.atlas-provenance.0000.395ff9dddcbce4eb.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0001.4143e98620875ed2.js`](./europe-plus.atlas-nodes.0001.4143e98620875ed2.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0002.406d2e86bd214ba4.js`](./europe-plus.atlas-nodes.0002.406d2e86bd214ba4.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0003.7b0a013a05c6c18d.js`](./europe-plus.atlas-nodes.0003.7b0a013a05c6c18d.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0004.8001580c68e784a2.js`](./europe-plus.atlas-nodes.0004.8001580c68e784a2.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0005.9d6e61b64f8f8218.js`](./europe-plus.atlas-nodes.0005.9d6e61b64f8f8218.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0006.83936a1f784df045.js`](./europe-plus.atlas-nodes.0006.83936a1f784df045.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0007.c9cf983afb5e10f7.js`](./europe-plus.atlas-nodes.0007.c9cf983afb5e10f7.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0008.e3ba31b94ab6cbbe.js`](./europe-plus.atlas-nodes.0008.e3ba31b94ab6cbbe.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0009.85dd390ff1e6a34e.js`](./europe-plus.atlas-nodes.0009.85dd390ff1e6a34e.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0010.dae3e58e28b48c70.js`](./europe-plus.atlas-nodes.0010.dae3e58e28b48c70.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0011.6db5d092913b9711.js`](./europe-plus.atlas-nodes.0011.6db5d092913b9711.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0012.44104b52ab8eaa5b.js`](./europe-plus.atlas-nodes.0012.44104b52ab8eaa5b.js)
- Static atlas data chunk: [`europe-plus.atlas-nodes.0013.69b78cf37b9fd2a4.js`](./europe-plus.atlas-nodes.0013.69b78cf37b9fd2a4.js)
- Static atlas data chunk: [`europe-plus.atlas-edges.0014.739cee982bf61a20.js`](./europe-plus.atlas-edges.0014.739cee982bf61a20.js)
- Static atlas data chunk: [`europe-plus.atlas-sequences.0015.7f2bb80b5a23fc03.js`](./europe-plus.atlas-sequences.0015.7f2bb80b5a23fc03.js)
- Static atlas data chunk: [`europe-plus.atlas-indexes.0016.94310381852b6a76.js`](./europe-plus.atlas-indexes.0016.94310381852b6a76.js)
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

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
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


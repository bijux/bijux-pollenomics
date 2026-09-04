# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-04` from Homo
sapiens AADR `v66` plus any governed contextual and animal surfaces that
the active scope contract allows.

Nordic is the regional detail surface. It keeps the shared human and animal evidence layers, then adds Nordic-only environmental, archaeology, boundary, and fieldwork overlays that remain interpretable at this scale.

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
- Default basemap: `voyager`
- The opening extent stays tight on Nordic countries so lake, site, and archaeology context reads as map content rather than background noise.

## Output Files

- Interactive map: [`nordic_map.html`](./nordic_map.html)
- Combined GeoJSON: [`nordic_samples.geojson`](./nordic_samples.geojson)
- Machine-readable summary: [`nordic_summary.json`](./nordic_summary.json)
- Map publication contract JSON: [`nordic_map_publication_contract.json`](./nordic_map_publication_contract.json)
- Map publication contract markdown: [`nordic_map_publication_contract.md`](./nordic_map_publication_contract.md)
- Point traceability JSON: [`nordic_point_traceability.json`](./nordic_point_traceability.json)
- Point traceability markdown: [`nordic_point_traceability.md`](./nordic_point_traceability.md)
- LandClim pollen site GeoJSON: [`nordic_pollen_site_sequences.geojson`](./nordic_pollen_site_sequences.geojson)
- Neotoma pollen GeoJSON: [`nordic_pollen_sites.geojson`](./nordic_pollen_sites.geojson)
- Sweden archaeology site discovery GeoJSON: [`sweden_archaeology_site_discovery.geojson`](./sweden_archaeology_site_discovery.geojson)
- Sweden archaeology site discovery registry: [`sweden_archaeology_site_discovery.json`](./sweden_archaeology_site_discovery.json)
- Sweden archaeology site discovery table: [`sweden_archaeology_site_discovery.csv`](./sweden_archaeology_site_discovery.csv)
- Sweden archaeology site discovery guide: [`sweden_archaeology_site_discovery.md`](./sweden_archaeology_site_discovery.md)
- Nordic country boundaries: [`nordic_country_boundaries.geojson`](./nordic_country_boundaries.geojson)
- LandClim REVEALS temporal grid GeoJSON: [`nordic_reveals_temporal_grid_cells.geojson`](./nordic_reveals_temporal_grid_cells.geojson)
- RAÄ archaeology layer metadata: [`sweden_archaeology_layer.json`](./sweden_archaeology_layer.json)
- Animal locality GeoJSON: [`nordic_animal_localities.geojson`](./nordic_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`nordic_domesticated_animal_localities.geojson`](./nordic_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`nordic_comparator_animal_localities.geojson`](./nordic_comparator_animal_localities.geojson)
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.2eddab14e7f1c22f.js`](./nordic.atlas-provenance.0000.2eddab14e7f1c22f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.39f5328123ee0676.js`](./nordic.atlas-nodes.0001.39f5328123ee0676.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.8b244a9f60e62305.js`](./nordic.atlas-nodes.0002.8b244a9f60e62305.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.8c247993821f70f7.js`](./nordic.atlas-nodes.0003.8c247993821f70f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.2048a291e07b041d.js`](./nordic.atlas-nodes.0004.2048a291e07b041d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.b593e1d4a3c599bb.js`](./nordic.atlas-nodes.0005.b593e1d4a3c599bb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.d71f66b9777cd391.js`](./nordic.atlas-nodes.0006.d71f66b9777cd391.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.682a0e08eacf3120.js`](./nordic.atlas-nodes.0007.682a0e08eacf3120.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.4eab010e9becb091.js`](./nordic.atlas-nodes.0008.4eab010e9becb091.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.28e919ea8e760d4e.js`](./nordic.atlas-nodes.0009.28e919ea8e760d4e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.e3b051a313295d55.js`](./nordic.atlas-nodes.0010.e3b051a313295d55.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.3b1c64ba3fdbd682.js`](./nordic.atlas-nodes.0011.3b1c64ba3fdbd682.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.aada6aec1ee0bbdb.js`](./nordic.atlas-nodes.0012.aada6aec1ee0bbdb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.aca885a46218684c.js`](./nordic.atlas-nodes.0013.aca885a46218684c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.8797b1c7a66f4045.js`](./nordic.atlas-nodes.0014.8797b1c7a66f4045.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.8785e47cf21eb84c.js`](./nordic.atlas-nodes.0015.8785e47cf21eb84c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.c7dd605d15a33e6d.js`](./nordic.atlas-nodes.0016.c7dd605d15a33e6d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.b48f30cbaeb276ae.js`](./nordic.atlas-nodes.0017.b48f30cbaeb276ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.f39a7457c1e1317d.js`](./nordic.atlas-nodes.0018.f39a7457c1e1317d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.2301d9023ecdd1cb.js`](./nordic.atlas-nodes.0019.2301d9023ecdd1cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.e8abfb7b1a088f15.js`](./nordic.atlas-nodes.0020.e8abfb7b1a088f15.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.3b64a7290331617d.js`](./nordic.atlas-nodes.0021.3b64a7290331617d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.d7d3a1a4df58e814.js`](./nordic.atlas-nodes.0022.d7d3a1a4df58e814.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.8c3553da40413e21.js`](./nordic.atlas-nodes.0023.8c3553da40413e21.js)
- Static atlas data chunk: [`nordic.atlas-edges.0024.244f710ccfc88b83.js`](./nordic.atlas-edges.0024.244f710ccfc88b83.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0025.19499c64b5594043.js`](./nordic.atlas-sequences.0025.19499c64b5594043.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0026.c0f1b0ab94e9e199.js`](./nordic.atlas-indexes.0026.c0f1b0ab94e9e199.js)
- Candidate site ranking CSV: [`nordic_candidate_sites.csv`](./nordic_candidate_sites.csv)
- Candidate site ranking JSON: [`nordic_candidate_sites.json`](./nordic_candidate_sites.json)
- Candidate site ranking markdown: [`nordic_candidate_sites.md`](./nordic_candidate_sites.md)
- Candidate site sensitivity JSON: [`nordic_candidate_site_sensitivity.json`](./nordic_candidate_site_sensitivity.json)
- Candidate site sensitivity markdown: [`nordic_candidate_site_sensitivity.md`](./nordic_candidate_site_sensitivity.md)
- Candidate ranking engine manifest: [`nordic_candidate_ranking_engine_manifest.json`](./nordic_candidate_ranking_engine_manifest.json)
- Atlas evidence surface JSON: [`nordic_evidence_surface.json`](./nordic_evidence_surface.json)
- Atlas evidence surface markdown: [`nordic_evidence_surface.md`](./nordic_evidence_surface.md)
- Atlas scientific review JSON: [`nordic_scientific_review.json`](./nordic_scientific_review.json)
- Atlas scientific review markdown: [`nordic_scientific_review.md`](./nordic_scientific_review.md)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | Pollen sequences staged from the LandClim normalization bundle. | `490` |
| Neotoma pollen sites | `scope_specific_overlay` | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `200` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `10379` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |
| LandClim REVEALS time-window grids | `scope_specific_overlay` | Time-window-specific REVEALS grid estimates from published LandClim PANGAEA datasets. | `2515` |

## Governed Filters

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch
- Animal species focus when animal layers are present
- Animal scope when animal layers are present
- Animal coordinate confidence when animal layers are present
- Animal temporal windows when animal layers are present
- Nordic animal leads only when animal layers are present

## Scope Caveats

- Nordic-specific overlays describe the current Nordic recovery slice and must not be generalized outward.
- Animal points can remain visible even when their Nordic relevance is regional rather than one exact country.
- Approximate or inferred coordinates remain visible with explicit warnings instead of being silently dropped.


## Animal aDNA Layers

- Total animal locality points: `2`
- Shipped animal species: `1`
- Domesticated-core species layers: `1`
- Comparator species layers: `0`

### Layer Groups

- Domesticated-core animal evidence
- Comparator animal evidence

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
| exact | 2 |

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| horse | Equus caballus | domesticated_core | 2 |


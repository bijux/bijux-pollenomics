# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-05` from Homo
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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.5092d520424d4bf4.js`](./nordic.atlas-provenance.0000.5092d520424d4bf4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.ad285cf1890d8e0a.js`](./nordic.atlas-nodes.0001.ad285cf1890d8e0a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.492399b2c4e9a3e0.js`](./nordic.atlas-nodes.0002.492399b2c4e9a3e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.657b7b516b04f6ed.js`](./nordic.atlas-nodes.0003.657b7b516b04f6ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.df18bbe5a46f2178.js`](./nordic.atlas-nodes.0004.df18bbe5a46f2178.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.5c8af8ae7b9769b1.js`](./nordic.atlas-nodes.0005.5c8af8ae7b9769b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.fe080233bdd24fda.js`](./nordic.atlas-nodes.0006.fe080233bdd24fda.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.5c0d6f9c7ce4e971.js`](./nordic.atlas-nodes.0007.5c0d6f9c7ce4e971.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.0288d6980ccdbd89.js`](./nordic.atlas-nodes.0008.0288d6980ccdbd89.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.e974300588256696.js`](./nordic.atlas-nodes.0009.e974300588256696.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.005bda9e3c4ffd84.js`](./nordic.atlas-nodes.0010.005bda9e3c4ffd84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.9c076f0cac4eed10.js`](./nordic.atlas-nodes.0011.9c076f0cac4eed10.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.12bd5760375df3dc.js`](./nordic.atlas-nodes.0012.12bd5760375df3dc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.66e5b312a8396705.js`](./nordic.atlas-nodes.0013.66e5b312a8396705.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.fea15a19202152c8.js`](./nordic.atlas-nodes.0014.fea15a19202152c8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.6c20eddf0318f3b6.js`](./nordic.atlas-nodes.0015.6c20eddf0318f3b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.3353ff7cff747a4b.js`](./nordic.atlas-nodes.0016.3353ff7cff747a4b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.318465c7c042122f.js`](./nordic.atlas-nodes.0017.318465c7c042122f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.9d36e9688f9edc8f.js`](./nordic.atlas-nodes.0018.9d36e9688f9edc8f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.4b1878e15b653602.js`](./nordic.atlas-nodes.0019.4b1878e15b653602.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.05022997a8524d35.js`](./nordic.atlas-nodes.0020.05022997a8524d35.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.4066ded336b6c95d.js`](./nordic.atlas-nodes.0021.4066ded336b6c95d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.54ed4b2c05619ffa.js`](./nordic.atlas-nodes.0022.54ed4b2c05619ffa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.fe98f0a5f43872fa.js`](./nordic.atlas-nodes.0023.fe98f0a5f43872fa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.3c70322c736568ee.js`](./nordic.atlas-nodes.0024.3c70322c736568ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.f5e0f7da9da77142.js`](./nordic.atlas-nodes.0025.f5e0f7da9da77142.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.5e328100967dfc77.js`](./nordic.atlas-nodes.0026.5e328100967dfc77.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.930af5a040355c0d.js`](./nordic.atlas-nodes.0027.930af5a040355c0d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.1b958674303537b4.js`](./nordic.atlas-nodes.0028.1b958674303537b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.293b3508b1eb2ab8.js`](./nordic.atlas-nodes.0029.293b3508b1eb2ab8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.a9b9e06f7ff94130.js`](./nordic.atlas-nodes.0030.a9b9e06f7ff94130.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.1e6e7343c9e2dbf1.js`](./nordic.atlas-nodes.0031.1e6e7343c9e2dbf1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.658246536515db1c.js`](./nordic.atlas-nodes.0032.658246536515db1c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.665188dada2a1378.js`](./nordic.atlas-nodes.0033.665188dada2a1378.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.15249ebf0a475425.js`](./nordic.atlas-nodes.0034.15249ebf0a475425.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.d87912a77359248e.js`](./nordic.atlas-nodes.0035.d87912a77359248e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.3687b66f0a05532b.js`](./nordic.atlas-nodes.0036.3687b66f0a05532b.js)
- Static atlas data chunk: [`nordic.atlas-edges.0037.410297acd754b375.js`](./nordic.atlas-edges.0037.410297acd754b375.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0038.e6eff734a6b30945.js`](./nordic.atlas-sequences.0038.e6eff734a6b30945.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0039.0e32530c548708f3.js`](./nordic.atlas-indexes.0039.0e32530c548708f3.js)
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


# World Evidence Surface

This shared interactive map bundle was generated on `2026-09-06` from Homo
sapiens AADR `v66` plus any governed contextual and animal surfaces that
the active scope contract allows.

World is the governing publication surface. It keeps every published country inside one shared map and excludes Nordic-only context overlays that would look more complete than they really are at broader scale.

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
- The opening extent keeps a broad trans-Atlantic and Eurasian frame so the root publication surface reads as a parent scope rather than a Nordic detail page with a bigger title.

## Output Files

- Interactive map: [`world_map.html`](./world_map.html)
- Combined GeoJSON: [`world_samples.geojson`](./world_samples.geojson)
- Machine-readable summary: [`world_summary.json`](./world_summary.json)
- Map publication contract JSON: [`world_map_publication_contract.json`](./world_map_publication_contract.json)
- Map publication contract markdown: [`world_map_publication_contract.md`](./world_map_publication_contract.md)
- Point traceability JSON: [`world_point_traceability.json`](./world_point_traceability.json)
- Point traceability markdown: [`world_point_traceability.md`](./world_point_traceability.md)
- Nordic country boundaries: [`nordic_country_boundaries.geojson`](./nordic_country_boundaries.geojson)
- Animal locality GeoJSON: [`world_animal_localities.geojson`](./world_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`world_domesticated_animal_localities.geojson`](./world_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`world_comparator_animal_localities.geojson`](./world_comparator_animal_localities.geojson)
- Animal atlas evidence CSV: [`world_animal_atlas_evidence.csv`](./world_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`world_animal_atlas_evidence.json`](./world_animal_atlas_evidence.json)
- Animal point traceability JSON: [`world_animal_point_traceability.json`](./world_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`world_map_assets.json`](./world_map_assets.json)
- Static atlas data chunk: [`world.atlas-provenance.0000.6c4f1932ce5fadb5.js`](./world.atlas-provenance.0000.6c4f1932ce5fadb5.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.c38a9027f249545b.js`](./world.atlas-nodes.0001.c38a9027f249545b.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.85f3fbbe570ae9cf.js`](./world.atlas-nodes.0002.85f3fbbe570ae9cf.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.24c80320bb665093.js`](./world.atlas-nodes.0003.24c80320bb665093.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.2149ea07c3912836.js`](./world.atlas-nodes.0004.2149ea07c3912836.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.2a3d1a1ac723447d.js`](./world.atlas-nodes.0005.2a3d1a1ac723447d.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.53301de1ed4fe6b6.js`](./world.atlas-nodes.0006.53301de1ed4fe6b6.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.118bf430e8d099ba.js`](./world.atlas-nodes.0007.118bf430e8d099ba.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.30d432c7b657160b.js`](./world.atlas-nodes.0008.30d432c7b657160b.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.f807089650f7ef77.js`](./world.atlas-nodes.0009.f807089650f7ef77.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.e99a92c1437079a8.js`](./world.atlas-nodes.0010.e99a92c1437079a8.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.b3439cac66847284.js`](./world.atlas-nodes.0011.b3439cac66847284.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.6f1d64744c30374e.js`](./world.atlas-nodes.0012.6f1d64744c30374e.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.c2d6a8bfde37221c.js`](./world.atlas-nodes.0013.c2d6a8bfde37221c.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.130439156ab12e45.js`](./world.atlas-nodes.0014.130439156ab12e45.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.92a3c850c3083214.js`](./world.atlas-nodes.0015.92a3c850c3083214.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.5aa9018c83fa6c25.js`](./world.atlas-nodes.0016.5aa9018c83fa6c25.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.80ea3be9c7c0578d.js`](./world.atlas-nodes.0017.80ea3be9c7c0578d.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.c54401ebb7d4c2d5.js`](./world.atlas-nodes.0018.c54401ebb7d4c2d5.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.dfdcbb9e59a97303.js`](./world.atlas-nodes.0019.dfdcbb9e59a97303.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.558ab8cd6afbd0ff.js`](./world.atlas-nodes.0020.558ab8cd6afbd0ff.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.d1c23159657b4327.js`](./world.atlas-nodes.0021.d1c23159657b4327.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.3da5a799e421ebd2.js`](./world.atlas-nodes.0022.3da5a799e421ebd2.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.bcaa262c61a33c2a.js`](./world.atlas-nodes.0023.bcaa262c61a33c2a.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.1ea49df4e92a492d.js`](./world.atlas-nodes.0024.1ea49df4e92a492d.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.29899000225c6d4d.js`](./world.atlas-nodes.0025.29899000225c6d4d.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.b3fe2281618a457a.js`](./world.atlas-nodes.0026.b3fe2281618a457a.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.18552cad9e9c56fc.js`](./world.atlas-nodes.0027.18552cad9e9c56fc.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.504bc8270d97bd34.js`](./world.atlas-nodes.0028.504bc8270d97bd34.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.3c4bc90c7f3bf961.js`](./world.atlas-nodes.0029.3c4bc90c7f3bf961.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.359a10ea1739f797.js`](./world.atlas-nodes.0030.359a10ea1739f797.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.c139783911c9226b.js`](./world.atlas-nodes.0031.c139783911c9226b.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.84d7c52acac4b79c.js`](./world.atlas-nodes.0032.84d7c52acac4b79c.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.ed8402f80823d703.js`](./world.atlas-nodes.0033.ed8402f80823d703.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.014193a75e4292e6.js`](./world.atlas-nodes.0034.014193a75e4292e6.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.aa56c8227ab69073.js`](./world.atlas-nodes.0035.aa56c8227ab69073.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.8f896f7cb0e5e3e3.js`](./world.atlas-nodes.0036.8f896f7cb0e5e3e3.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.388e8f13cf63ac4d.js`](./world.atlas-nodes.0037.388e8f13cf63ac4d.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.c23505bc42d6d0c7.js`](./world.atlas-nodes.0038.c23505bc42d6d0c7.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.25456127d81541f5.js`](./world.atlas-nodes.0039.25456127d81541f5.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.229d8f655eedd1c3.js`](./world.atlas-nodes.0040.229d8f655eedd1c3.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.d88b56665148b781.js`](./world.atlas-nodes.0041.d88b56665148b781.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.2138c307579a08cf.js`](./world.atlas-nodes.0042.2138c307579a08cf.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.793192588b612662.js`](./world.atlas-nodes.0043.793192588b612662.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.b45b646b7a1b2a0d.js`](./world.atlas-nodes.0044.b45b646b7a1b2a0d.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.8b962bb8b7868d36.js`](./world.atlas-nodes.0045.8b962bb8b7868d36.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.3dcee439b00843d8.js`](./world.atlas-nodes.0046.3dcee439b00843d8.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.10c67264993f9f9c.js`](./world.atlas-nodes.0047.10c67264993f9f9c.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.73ed71be02586907.js`](./world.atlas-nodes.0048.73ed71be02586907.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.88c49ec2f6cbedb4.js`](./world.atlas-nodes.0049.88c49ec2f6cbedb4.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.ecd5a1589c6e6a8c.js`](./world.atlas-nodes.0050.ecd5a1589c6e6a8c.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.3d26ae7911a74dc9.js`](./world.atlas-nodes.0051.3d26ae7911a74dc9.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.2b230b63435a5635.js`](./world.atlas-nodes.0052.2b230b63435a5635.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.49be5272b6593469.js`](./world.atlas-nodes.0053.49be5272b6593469.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.04d7b58c2715595f.js`](./world.atlas-nodes.0054.04d7b58c2715595f.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.7039b8ebb84e4f85.js`](./world.atlas-nodes.0055.7039b8ebb84e4f85.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.10854d7bde84fd3d.js`](./world.atlas-nodes.0056.10854d7bde84fd3d.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.f1408b92b7888095.js`](./world.atlas-nodes.0057.f1408b92b7888095.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.9b5ee9b8160b04db.js`](./world.atlas-nodes.0058.9b5ee9b8160b04db.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.ecdf0213f74a3703.js`](./world.atlas-nodes.0059.ecdf0213f74a3703.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.bc31997a85448b08.js`](./world.atlas-nodes.0060.bc31997a85448b08.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.0ab77e64ccd17b6f.js`](./world.atlas-nodes.0061.0ab77e64ccd17b6f.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.649c2d4164004ed5.js`](./world.atlas-nodes.0062.649c2d4164004ed5.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.1af8e24c466a4e67.js`](./world.atlas-nodes.0063.1af8e24c466a4e67.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.0036493a04125e2f.js`](./world.atlas-nodes.0064.0036493a04125e2f.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.66745d320054002f.js`](./world.atlas-nodes.0065.66745d320054002f.js)
- Static atlas data chunk: [`world.atlas-edges.0066.e2b671c81646d914.js`](./world.atlas-edges.0066.e2b671c81646d914.js)
- Static atlas data chunk: [`world.atlas-sequences.0067.f5fc3279827e80e0.js`](./world.atlas-sequences.0067.f5fc3279827e80e0.js)
- Static atlas data chunk: [`world.atlas-indexes.0068.ce31bd98858e792b.js`](./world.atlas-indexes.0068.ce31bd98858e792b.js)
- Candidate site ranking CSV: [`world_candidate_sites.csv`](./world_candidate_sites.csv)
- Candidate site ranking JSON: [`world_candidate_sites.json`](./world_candidate_sites.json)
- Candidate site ranking markdown: [`world_candidate_sites.md`](./world_candidate_sites.md)
- Candidate site sensitivity JSON: [`world_candidate_site_sensitivity.json`](./world_candidate_site_sensitivity.json)
- Candidate site sensitivity markdown: [`world_candidate_site_sensitivity.md`](./world_candidate_site_sensitivity.md)
- Candidate ranking engine manifest: [`world_candidate_ranking_engine_manifest.json`](./world_candidate_ranking_engine_manifest.json)
- Atlas evidence surface JSON: [`world_evidence_surface.json`](./world_evidence_surface.json)
- Atlas evidence surface markdown: [`world_evidence_surface.md`](./world_evidence_surface.md)
- Atlas scientific review JSON: [`world_scientific_review.json`](./world_scientific_review.json)
- Atlas scientific review markdown: [`world_scientific_review.md`](./world_scientific_review.md)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Goat aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `26` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `203` |
| Cat aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `40` |
| Pig aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |

## Governed Filters

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch

## Scope Caveats

- World is the parent publication scope, not a claim that worldwide contextual coverage is already complete.
- Nordic environmental and archaeology overlays are withheld here until broader equivalents exist.
- Country counts still describe Homo sapiens AADR rows even when animal layers are also visible.


## Animal aDNA Layers

- Total animal locality points: `271`
- Shipped animal species: `4`
- Domesticated-core species layers: `4`
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
| approximate | 2 |
| exact | 269 |

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| goat | Capra hircus | domesticated_core | 26 |
| horse | Equus caballus | domesticated_core | 203 |
| cat | Felis catus | domesticated_core | 40 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |


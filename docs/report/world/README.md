# World Evidence Surface

This shared interactive map bundle was generated on `2026-09-05` from Homo
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
- Static atlas data chunk: [`world.atlas-provenance.0000.834fe7aebd90bd20.js`](./world.atlas-provenance.0000.834fe7aebd90bd20.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.95e723e7e53abd04.js`](./world.atlas-nodes.0001.95e723e7e53abd04.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.a6b8101fedc02329.js`](./world.atlas-nodes.0002.a6b8101fedc02329.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.9cc6c3124fedf3c8.js`](./world.atlas-nodes.0003.9cc6c3124fedf3c8.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.5b6021181cfc05b7.js`](./world.atlas-nodes.0004.5b6021181cfc05b7.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.d4906bf577b9e6d0.js`](./world.atlas-nodes.0005.d4906bf577b9e6d0.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.fdd48764d37a629a.js`](./world.atlas-nodes.0006.fdd48764d37a629a.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.de95334870909344.js`](./world.atlas-nodes.0007.de95334870909344.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.a5bb76850cdb921a.js`](./world.atlas-nodes.0008.a5bb76850cdb921a.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.55cfa2e04b1ae408.js`](./world.atlas-nodes.0009.55cfa2e04b1ae408.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.33f6b1e89e79e9f5.js`](./world.atlas-nodes.0010.33f6b1e89e79e9f5.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.a24ca35eb9b092f9.js`](./world.atlas-nodes.0011.a24ca35eb9b092f9.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.8c9665cb21a3ebe9.js`](./world.atlas-nodes.0012.8c9665cb21a3ebe9.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.0ce053331b77bebb.js`](./world.atlas-nodes.0013.0ce053331b77bebb.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.9d2c14593a1a7553.js`](./world.atlas-nodes.0014.9d2c14593a1a7553.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.a6c6a01d570cd2c2.js`](./world.atlas-nodes.0015.a6c6a01d570cd2c2.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.dcd7a4194c0db22c.js`](./world.atlas-nodes.0016.dcd7a4194c0db22c.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.6127b745d3bf84bc.js`](./world.atlas-nodes.0017.6127b745d3bf84bc.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.7ef99277cf69274c.js`](./world.atlas-nodes.0018.7ef99277cf69274c.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.cb8bd51e84e717e2.js`](./world.atlas-nodes.0019.cb8bd51e84e717e2.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.d57333226b3a7ce1.js`](./world.atlas-nodes.0020.d57333226b3a7ce1.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.c9c00d9491ee1ce9.js`](./world.atlas-nodes.0021.c9c00d9491ee1ce9.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.0a05ab6ef83f40fc.js`](./world.atlas-nodes.0022.0a05ab6ef83f40fc.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.1f2dd34f38706f84.js`](./world.atlas-nodes.0023.1f2dd34f38706f84.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.e8548dd92629350b.js`](./world.atlas-nodes.0024.e8548dd92629350b.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.9731b07dfcfc1fe8.js`](./world.atlas-nodes.0025.9731b07dfcfc1fe8.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.854f647032153a2f.js`](./world.atlas-nodes.0026.854f647032153a2f.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.7214d85de0e83344.js`](./world.atlas-nodes.0027.7214d85de0e83344.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.eab7b96fbecf61d7.js`](./world.atlas-nodes.0028.eab7b96fbecf61d7.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.907c531a3d5b9f63.js`](./world.atlas-nodes.0029.907c531a3d5b9f63.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.3564772acfe145fe.js`](./world.atlas-nodes.0030.3564772acfe145fe.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.e2057668f643fea0.js`](./world.atlas-nodes.0031.e2057668f643fea0.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.fbf4f62580e28a9b.js`](./world.atlas-nodes.0032.fbf4f62580e28a9b.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.788880df39486fa5.js`](./world.atlas-nodes.0033.788880df39486fa5.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.5e31b51e1eef1bbb.js`](./world.atlas-nodes.0034.5e31b51e1eef1bbb.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.8d99b33aaa58cd5a.js`](./world.atlas-nodes.0035.8d99b33aaa58cd5a.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.3787419656161d96.js`](./world.atlas-nodes.0036.3787419656161d96.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.34602184048dcac3.js`](./world.atlas-nodes.0037.34602184048dcac3.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.5ca5f6b019cecd47.js`](./world.atlas-nodes.0038.5ca5f6b019cecd47.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.3c34cfeca6f89c90.js`](./world.atlas-nodes.0039.3c34cfeca6f89c90.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.0374cd506c5a29a3.js`](./world.atlas-nodes.0040.0374cd506c5a29a3.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.e08040e43867b25f.js`](./world.atlas-nodes.0041.e08040e43867b25f.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.6fd61d75fff50c18.js`](./world.atlas-nodes.0042.6fd61d75fff50c18.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.758da036479a3ba8.js`](./world.atlas-nodes.0043.758da036479a3ba8.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.c6a1b9d79f15d803.js`](./world.atlas-nodes.0044.c6a1b9d79f15d803.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.a78a99f01bad3511.js`](./world.atlas-nodes.0045.a78a99f01bad3511.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.b05256b9094a1f97.js`](./world.atlas-nodes.0046.b05256b9094a1f97.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.34358d07d35035a5.js`](./world.atlas-nodes.0047.34358d07d35035a5.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.c86ea9ea19ed1471.js`](./world.atlas-nodes.0048.c86ea9ea19ed1471.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.3d71cb4fc02a7f4f.js`](./world.atlas-nodes.0049.3d71cb4fc02a7f4f.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.4999c677daf6b960.js`](./world.atlas-nodes.0050.4999c677daf6b960.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.e99653e8289b98f1.js`](./world.atlas-nodes.0051.e99653e8289b98f1.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.a6e287c1afd926c2.js`](./world.atlas-nodes.0052.a6e287c1afd926c2.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.0ec1540508c4338e.js`](./world.atlas-nodes.0053.0ec1540508c4338e.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.098ee66512f8f273.js`](./world.atlas-nodes.0054.098ee66512f8f273.js)
- Static atlas data chunk: [`world.atlas-edges.0055.3b7583a0d544bc4d.js`](./world.atlas-edges.0055.3b7583a0d544bc4d.js)
- Static atlas data chunk: [`world.atlas-sequences.0056.0322d445f162aa7c.js`](./world.atlas-sequences.0056.0322d445f162aa7c.js)
- Static atlas data chunk: [`world.atlas-indexes.0057.0e2694cfcfb86cf4.js`](./world.atlas-indexes.0057.0e2694cfcfb86cf4.js)
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
| Horse aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `207` |
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

- Total animal locality points: `233`
- Shipped animal species: `2`
- Domesticated-core species layers: `2`
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
| exact | 233 |

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| goat | Capra hircus | domesticated_core | 26 |
| horse | Equus caballus | domesticated_core | 207 |


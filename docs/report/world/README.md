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
- Static atlas data chunk: [`world.atlas-provenance.0000.c76411f1c17a7e51.js`](./world.atlas-provenance.0000.c76411f1c17a7e51.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.40068718f81d6f6d.js`](./world.atlas-nodes.0001.40068718f81d6f6d.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.4e776d6c63d9d35b.js`](./world.atlas-nodes.0002.4e776d6c63d9d35b.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.2a233d6c0512a7ec.js`](./world.atlas-nodes.0003.2a233d6c0512a7ec.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.10997bc56ecfcad5.js`](./world.atlas-nodes.0004.10997bc56ecfcad5.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.b7197f3b3282e498.js`](./world.atlas-nodes.0005.b7197f3b3282e498.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.2694faa04e0362c6.js`](./world.atlas-nodes.0006.2694faa04e0362c6.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.528cd62227abb9eb.js`](./world.atlas-nodes.0007.528cd62227abb9eb.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.59b4a37b35eec9ad.js`](./world.atlas-nodes.0008.59b4a37b35eec9ad.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.b1d32bb8ac26a9ea.js`](./world.atlas-nodes.0009.b1d32bb8ac26a9ea.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.39a0a9d96a7840ff.js`](./world.atlas-nodes.0010.39a0a9d96a7840ff.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.f6ef51fd4e2ff959.js`](./world.atlas-nodes.0011.f6ef51fd4e2ff959.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.b6da653b049dfc64.js`](./world.atlas-nodes.0012.b6da653b049dfc64.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.6dd848d03df797a6.js`](./world.atlas-nodes.0013.6dd848d03df797a6.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.b5c2d2e7fe1e4925.js`](./world.atlas-nodes.0014.b5c2d2e7fe1e4925.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.37b1532ad9d8e39e.js`](./world.atlas-nodes.0015.37b1532ad9d8e39e.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.9f740274aa55e972.js`](./world.atlas-nodes.0016.9f740274aa55e972.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.a932081f75c7c8cc.js`](./world.atlas-nodes.0017.a932081f75c7c8cc.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.0fb202ea161dbf44.js`](./world.atlas-nodes.0018.0fb202ea161dbf44.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.f417f495896932bb.js`](./world.atlas-nodes.0019.f417f495896932bb.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.1a8619999bb678ee.js`](./world.atlas-nodes.0020.1a8619999bb678ee.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.a245d4ebaaa93b66.js`](./world.atlas-nodes.0021.a245d4ebaaa93b66.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.e1068c4b2497112d.js`](./world.atlas-nodes.0022.e1068c4b2497112d.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.f99e3d252b36535d.js`](./world.atlas-nodes.0023.f99e3d252b36535d.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.adec2277a750c1c7.js`](./world.atlas-nodes.0024.adec2277a750c1c7.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.0c3803939638532f.js`](./world.atlas-nodes.0025.0c3803939638532f.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.23356f63fed82db2.js`](./world.atlas-nodes.0026.23356f63fed82db2.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.2bcd127352af4930.js`](./world.atlas-nodes.0027.2bcd127352af4930.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.8038a8c3245a34cb.js`](./world.atlas-nodes.0028.8038a8c3245a34cb.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.db37c4158b07c310.js`](./world.atlas-nodes.0029.db37c4158b07c310.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.272913d093cc0b87.js`](./world.atlas-nodes.0030.272913d093cc0b87.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.d5da318307a86baa.js`](./world.atlas-nodes.0031.d5da318307a86baa.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.aab0b0c5fdb28e5f.js`](./world.atlas-nodes.0032.aab0b0c5fdb28e5f.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.5fc9703310ebd098.js`](./world.atlas-nodes.0033.5fc9703310ebd098.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.4cf77bce2f9d64ce.js`](./world.atlas-nodes.0034.4cf77bce2f9d64ce.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.555b55bad1d6bfad.js`](./world.atlas-nodes.0035.555b55bad1d6bfad.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.f5cee46f893bfb2a.js`](./world.atlas-nodes.0036.f5cee46f893bfb2a.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.a9350037ebd824c9.js`](./world.atlas-nodes.0037.a9350037ebd824c9.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.c55ed2a6161ebecb.js`](./world.atlas-nodes.0038.c55ed2a6161ebecb.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.7068ffec08d05943.js`](./world.atlas-nodes.0039.7068ffec08d05943.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.ed9ba115f470bb51.js`](./world.atlas-nodes.0040.ed9ba115f470bb51.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.e67e4e020f8818ea.js`](./world.atlas-nodes.0041.e67e4e020f8818ea.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.b06ed86bbf8964b3.js`](./world.atlas-nodes.0042.b06ed86bbf8964b3.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.aa9429fbf0fcc671.js`](./world.atlas-nodes.0043.aa9429fbf0fcc671.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.cc819179120e5f0f.js`](./world.atlas-nodes.0044.cc819179120e5f0f.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.bc8b1160d6d084b6.js`](./world.atlas-nodes.0045.bc8b1160d6d084b6.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.7ec0de301e4dd7ac.js`](./world.atlas-nodes.0046.7ec0de301e4dd7ac.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.29e20ec5c56ae98f.js`](./world.atlas-nodes.0047.29e20ec5c56ae98f.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.32fe1096962097ed.js`](./world.atlas-nodes.0048.32fe1096962097ed.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.62f1a6d0b42634a3.js`](./world.atlas-nodes.0049.62f1a6d0b42634a3.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.d847c1c274df9718.js`](./world.atlas-nodes.0050.d847c1c274df9718.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.570c19bd8a09feca.js`](./world.atlas-nodes.0051.570c19bd8a09feca.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.7791746372b2489a.js`](./world.atlas-nodes.0052.7791746372b2489a.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.bee1742c1a6b0651.js`](./world.atlas-nodes.0053.bee1742c1a6b0651.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.d56d88ea60b4f630.js`](./world.atlas-nodes.0054.d56d88ea60b4f630.js)
- Static atlas data chunk: [`world.atlas-edges.0055.b295250f16a6d465.js`](./world.atlas-edges.0055.b295250f16a6d465.js)
- Static atlas data chunk: [`world.atlas-sequences.0056.db797f70a3712c03.js`](./world.atlas-sequences.0056.db797f70a3712c03.js)
- Static atlas data chunk: [`world.atlas-indexes.0057.a29da189eeab509a.js`](./world.atlas-indexes.0057.a29da189eeab509a.js)
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


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
- Default basemap: `street`
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
- Static atlas data chunk: [`world.atlas-provenance.0000.8a54be9af6571af3.js`](./world.atlas-provenance.0000.8a54be9af6571af3.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.7ef115c3783ea1ff.js`](./world.atlas-nodes.0001.7ef115c3783ea1ff.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.a52500f199d3c263.js`](./world.atlas-nodes.0002.a52500f199d3c263.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.c109ddc864efaad9.js`](./world.atlas-nodes.0003.c109ddc864efaad9.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.a367c3bcefbf44dc.js`](./world.atlas-nodes.0004.a367c3bcefbf44dc.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.ed5858e8858cd027.js`](./world.atlas-nodes.0005.ed5858e8858cd027.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.fb7372f91e555247.js`](./world.atlas-nodes.0006.fb7372f91e555247.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.844efebcfc6b1e94.js`](./world.atlas-nodes.0007.844efebcfc6b1e94.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.4a9fad1f755ffb1d.js`](./world.atlas-nodes.0008.4a9fad1f755ffb1d.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.7d6fc760dd1fb090.js`](./world.atlas-nodes.0009.7d6fc760dd1fb090.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.a8581aeed5661250.js`](./world.atlas-nodes.0010.a8581aeed5661250.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.e919e55425d09e38.js`](./world.atlas-nodes.0011.e919e55425d09e38.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.47a5f928e4ac2301.js`](./world.atlas-nodes.0012.47a5f928e4ac2301.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.cb176135609a1af5.js`](./world.atlas-nodes.0013.cb176135609a1af5.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.bd2ddb2a85f2b145.js`](./world.atlas-nodes.0014.bd2ddb2a85f2b145.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.9034c9b7019b547b.js`](./world.atlas-nodes.0015.9034c9b7019b547b.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.f0302b89d66a59ea.js`](./world.atlas-nodes.0016.f0302b89d66a59ea.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.56bfa59cac2c01b5.js`](./world.atlas-nodes.0017.56bfa59cac2c01b5.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.175d42d6ba400f93.js`](./world.atlas-nodes.0018.175d42d6ba400f93.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.cc9d730dc89687cf.js`](./world.atlas-nodes.0019.cc9d730dc89687cf.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.817a8310960e2fc8.js`](./world.atlas-nodes.0020.817a8310960e2fc8.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.580df92bc50036ee.js`](./world.atlas-nodes.0021.580df92bc50036ee.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.805d78a8fa20d146.js`](./world.atlas-nodes.0022.805d78a8fa20d146.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.ae1f469062e3e99c.js`](./world.atlas-nodes.0023.ae1f469062e3e99c.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.a9420c0f4613854e.js`](./world.atlas-nodes.0024.a9420c0f4613854e.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.0e62aa2b8124f550.js`](./world.atlas-nodes.0025.0e62aa2b8124f550.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.dfe23f8b900d59c7.js`](./world.atlas-nodes.0026.dfe23f8b900d59c7.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.4e19d60b73ccd4f4.js`](./world.atlas-nodes.0027.4e19d60b73ccd4f4.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.1351914efd2d1256.js`](./world.atlas-nodes.0028.1351914efd2d1256.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.973f384f8f680729.js`](./world.atlas-nodes.0029.973f384f8f680729.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.5871ea2a510bc7ad.js`](./world.atlas-nodes.0030.5871ea2a510bc7ad.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.a04d08615c4f9c41.js`](./world.atlas-nodes.0031.a04d08615c4f9c41.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.d62fe163fd76dd0b.js`](./world.atlas-nodes.0032.d62fe163fd76dd0b.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.3ce8a4056f4d5846.js`](./world.atlas-nodes.0033.3ce8a4056f4d5846.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.ce607a0f0d49033f.js`](./world.atlas-nodes.0034.ce607a0f0d49033f.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.6867503e9c65913b.js`](./world.atlas-nodes.0035.6867503e9c65913b.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.947e5a3f2e9b7fe8.js`](./world.atlas-nodes.0036.947e5a3f2e9b7fe8.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.b9ccaf9ec9cbd66e.js`](./world.atlas-nodes.0037.b9ccaf9ec9cbd66e.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.a4b88aeb360fa32b.js`](./world.atlas-nodes.0038.a4b88aeb360fa32b.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.fea87bcb00b4c99f.js`](./world.atlas-nodes.0039.fea87bcb00b4c99f.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.e9a6d1d0ce2ff3fc.js`](./world.atlas-nodes.0040.e9a6d1d0ce2ff3fc.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.68895448ce513c50.js`](./world.atlas-nodes.0041.68895448ce513c50.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.c06d093a89103cb7.js`](./world.atlas-nodes.0042.c06d093a89103cb7.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.d6c6b3880f25efac.js`](./world.atlas-nodes.0043.d6c6b3880f25efac.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.0f99dad9789c34e9.js`](./world.atlas-nodes.0044.0f99dad9789c34e9.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.8e249160adf1d71e.js`](./world.atlas-nodes.0045.8e249160adf1d71e.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.efef951698a96f7c.js`](./world.atlas-nodes.0046.efef951698a96f7c.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.03ffb482aa24400f.js`](./world.atlas-nodes.0047.03ffb482aa24400f.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.a97a26731f65b023.js`](./world.atlas-nodes.0048.a97a26731f65b023.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.37fcd3cb315d9c98.js`](./world.atlas-nodes.0049.37fcd3cb315d9c98.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.fe7cf6b48f094381.js`](./world.atlas-nodes.0050.fe7cf6b48f094381.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.84da56156cd73b17.js`](./world.atlas-nodes.0051.84da56156cd73b17.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.c6e589487d04504b.js`](./world.atlas-nodes.0052.c6e589487d04504b.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.5e3c6e5e729ef12f.js`](./world.atlas-nodes.0053.5e3c6e5e729ef12f.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.d1ad8993504505ce.js`](./world.atlas-nodes.0054.d1ad8993504505ce.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.71b3f05772f3b4ea.js`](./world.atlas-nodes.0055.71b3f05772f3b4ea.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.5d90dd02ca5b4aca.js`](./world.atlas-nodes.0056.5d90dd02ca5b4aca.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.3bbf0514416fa378.js`](./world.atlas-nodes.0057.3bbf0514416fa378.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.f9b3571a01ecf96d.js`](./world.atlas-nodes.0058.f9b3571a01ecf96d.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.6aa13d0540b33211.js`](./world.atlas-nodes.0059.6aa13d0540b33211.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.75d11eb5dd91e8d7.js`](./world.atlas-nodes.0060.75d11eb5dd91e8d7.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.593e0fe5a00ad611.js`](./world.atlas-nodes.0061.593e0fe5a00ad611.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.a13cb9c421c97538.js`](./world.atlas-nodes.0062.a13cb9c421c97538.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.accb9638bfacdf01.js`](./world.atlas-nodes.0063.accb9638bfacdf01.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.d00d8a001ddcff2a.js`](./world.atlas-nodes.0064.d00d8a001ddcff2a.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.b6a2144c4a7c38c0.js`](./world.atlas-nodes.0065.b6a2144c4a7c38c0.js)
- Static atlas data chunk: [`world.atlas-nodes.0066.9b2639f9f928a774.js`](./world.atlas-nodes.0066.9b2639f9f928a774.js)
- Static atlas data chunk: [`world.atlas-nodes.0067.4b1acb6b3d87a393.js`](./world.atlas-nodes.0067.4b1acb6b3d87a393.js)
- Static atlas data chunk: [`world.atlas-edges.0068.40a0249aec9f5fca.js`](./world.atlas-edges.0068.40a0249aec9f5fca.js)
- Static atlas data chunk: [`world.atlas-sequences.0069.eecb688c6cdfd485.js`](./world.atlas-sequences.0069.eecb688c6cdfd485.js)
- Static atlas data chunk: [`world.atlas-indexes.0070.77f9b06ce6f37d5f.js`](./world.atlas-indexes.0070.77f9b06ce6f37d5f.js)
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
| Sheep aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
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

- Total animal locality points: `273`
- Shipped animal species: `5`
- Domesticated-core species layers: `5`
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
| source_reported_two_decimal_degrees | 2 |

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
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |


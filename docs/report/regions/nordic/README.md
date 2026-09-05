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
- SEAD site GeoJSON: [`nordic_environmental_sites.geojson`](./nordic_environmental_sites.geojson)
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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.15408feefe8f31b6.js`](./nordic.atlas-provenance.0000.15408feefe8f31b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.e41cadfe33cedd8c.js`](./nordic.atlas-nodes.0001.e41cadfe33cedd8c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.a997c1b7cd1a17e9.js`](./nordic.atlas-nodes.0002.a997c1b7cd1a17e9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.aef5b46617a50acb.js`](./nordic.atlas-nodes.0003.aef5b46617a50acb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.64514a6465c11c20.js`](./nordic.atlas-nodes.0004.64514a6465c11c20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.c7625896c3811049.js`](./nordic.atlas-nodes.0005.c7625896c3811049.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.d0f8eaed902f1ceb.js`](./nordic.atlas-nodes.0006.d0f8eaed902f1ceb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.83551f2f51a7cdb7.js`](./nordic.atlas-nodes.0007.83551f2f51a7cdb7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.21d530e13da43126.js`](./nordic.atlas-nodes.0008.21d530e13da43126.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.cf8d278d0b44d1a1.js`](./nordic.atlas-nodes.0009.cf8d278d0b44d1a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.0776a50624410f77.js`](./nordic.atlas-nodes.0010.0776a50624410f77.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.a9118b5a30e1e317.js`](./nordic.atlas-nodes.0011.a9118b5a30e1e317.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.34886dd57712a556.js`](./nordic.atlas-nodes.0012.34886dd57712a556.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.2d3bee3f1fc8e1e8.js`](./nordic.atlas-nodes.0013.2d3bee3f1fc8e1e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.5c71ed68c41ccdf7.js`](./nordic.atlas-nodes.0014.5c71ed68c41ccdf7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.bdea882bd7d2c337.js`](./nordic.atlas-nodes.0015.bdea882bd7d2c337.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.7b7a73491f8f4da5.js`](./nordic.atlas-nodes.0016.7b7a73491f8f4da5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.ab7d861b8a94d2c5.js`](./nordic.atlas-nodes.0017.ab7d861b8a94d2c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.0ed8710e80bade08.js`](./nordic.atlas-nodes.0018.0ed8710e80bade08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.c4a31049fa71bc77.js`](./nordic.atlas-nodes.0019.c4a31049fa71bc77.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.71c89549ef026256.js`](./nordic.atlas-nodes.0020.71c89549ef026256.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.16a69760c30a5e03.js`](./nordic.atlas-nodes.0021.16a69760c30a5e03.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.dc337ef23ccd8f4a.js`](./nordic.atlas-nodes.0022.dc337ef23ccd8f4a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.c620163a89cf333d.js`](./nordic.atlas-nodes.0023.c620163a89cf333d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.f47e45cdb6457d23.js`](./nordic.atlas-nodes.0024.f47e45cdb6457d23.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.b649b1e431305e7b.js`](./nordic.atlas-nodes.0025.b649b1e431305e7b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.20ad0fc026eb435b.js`](./nordic.atlas-nodes.0026.20ad0fc026eb435b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.9d619929bb30a371.js`](./nordic.atlas-nodes.0027.9d619929bb30a371.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.ce7395b00f9f5681.js`](./nordic.atlas-nodes.0028.ce7395b00f9f5681.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.c0b8b2ce6f5cdb17.js`](./nordic.atlas-nodes.0029.c0b8b2ce6f5cdb17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.0d7a91706b447407.js`](./nordic.atlas-nodes.0030.0d7a91706b447407.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.ff92878dda8200f7.js`](./nordic.atlas-nodes.0031.ff92878dda8200f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.be53e7115f6fab56.js`](./nordic.atlas-nodes.0032.be53e7115f6fab56.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.776f16fa4e0e66af.js`](./nordic.atlas-nodes.0033.776f16fa4e0e66af.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.389f35a8e331afd1.js`](./nordic.atlas-nodes.0034.389f35a8e331afd1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.353156fd926740ed.js`](./nordic.atlas-nodes.0035.353156fd926740ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.ea83526d1b296cb8.js`](./nordic.atlas-nodes.0036.ea83526d1b296cb8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.aa8d3714430c0ce2.js`](./nordic.atlas-nodes.0037.aa8d3714430c0ce2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.5224572984fb5b0b.js`](./nordic.atlas-nodes.0038.5224572984fb5b0b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.6f9a916ecd727397.js`](./nordic.atlas-nodes.0039.6f9a916ecd727397.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.3ed50836fd3b38d1.js`](./nordic.atlas-nodes.0040.3ed50836fd3b38d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.77dd190b8913eb84.js`](./nordic.atlas-nodes.0041.77dd190b8913eb84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.f02cef7e966750ea.js`](./nordic.atlas-nodes.0042.f02cef7e966750ea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.af3708c6cbe9014a.js`](./nordic.atlas-nodes.0043.af3708c6cbe9014a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.9821abeeeb785e9e.js`](./nordic.atlas-nodes.0044.9821abeeeb785e9e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.429d17caceed70ef.js`](./nordic.atlas-nodes.0045.429d17caceed70ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.668e06aa1cc01548.js`](./nordic.atlas-nodes.0046.668e06aa1cc01548.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.2cfc23424578f6a1.js`](./nordic.atlas-nodes.0047.2cfc23424578f6a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.0352d2eb5e2e9ad4.js`](./nordic.atlas-nodes.0048.0352d2eb5e2e9ad4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.a488a18d35a12115.js`](./nordic.atlas-nodes.0049.a488a18d35a12115.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.67b5d6f2298ff12b.js`](./nordic.atlas-nodes.0050.67b5d6f2298ff12b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.c82b01fbe0723aa7.js`](./nordic.atlas-nodes.0051.c82b01fbe0723aa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.22f86c4f3c7fd5af.js`](./nordic.atlas-nodes.0052.22f86c4f3c7fd5af.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.4eb03228fc9ee19a.js`](./nordic.atlas-nodes.0053.4eb03228fc9ee19a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.ba949a3db53ca181.js`](./nordic.atlas-nodes.0054.ba949a3db53ca181.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.a5e76c559298537a.js`](./nordic.atlas-nodes.0055.a5e76c559298537a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.bf10a6f199825a08.js`](./nordic.atlas-nodes.0056.bf10a6f199825a08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.ee3af75878128de7.js`](./nordic.atlas-nodes.0057.ee3af75878128de7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.03377fb6514c7702.js`](./nordic.atlas-nodes.0058.03377fb6514c7702.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.20058bd9d1ed9898.js`](./nordic.atlas-nodes.0059.20058bd9d1ed9898.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.908ca1cc99f58278.js`](./nordic.atlas-nodes.0060.908ca1cc99f58278.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.349a1ca154b24bb1.js`](./nordic.atlas-nodes.0061.349a1ca154b24bb1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.f200e382d92269aa.js`](./nordic.atlas-nodes.0062.f200e382d92269aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.c6712915286ceb4a.js`](./nordic.atlas-nodes.0063.c6712915286ceb4a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.86dc1c02a9148e83.js`](./nordic.atlas-nodes.0064.86dc1c02a9148e83.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.ca14ee98bfd633eb.js`](./nordic.atlas-nodes.0065.ca14ee98bfd633eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.9e1e189ee3795bbc.js`](./nordic.atlas-nodes.0066.9e1e189ee3795bbc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.a06b30e6161d846a.js`](./nordic.atlas-nodes.0067.a06b30e6161d846a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.9f9f6d522df30cf7.js`](./nordic.atlas-nodes.0068.9f9f6d522df30cf7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.52dcc48626f820a0.js`](./nordic.atlas-nodes.0069.52dcc48626f820a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.f5a5f7450aedf350.js`](./nordic.atlas-nodes.0070.f5a5f7450aedf350.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.0b8011dcdb25312e.js`](./nordic.atlas-nodes.0071.0b8011dcdb25312e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.f66759392e5d2919.js`](./nordic.atlas-nodes.0072.f66759392e5d2919.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.db700953ae8e6184.js`](./nordic.atlas-nodes.0073.db700953ae8e6184.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.0badbb0801a68617.js`](./nordic.atlas-nodes.0074.0badbb0801a68617.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.128b3fc4fb8ee23a.js`](./nordic.atlas-nodes.0075.128b3fc4fb8ee23a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.4f93cab07efc3e07.js`](./nordic.atlas-nodes.0076.4f93cab07efc3e07.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.d070c80ee22eb39b.js`](./nordic.atlas-nodes.0077.d070c80ee22eb39b.js)
- Static atlas data chunk: [`nordic.atlas-details.0078.d4e7636cd614c25b.js`](./nordic.atlas-details.0078.d4e7636cd614c25b.js)
- Static atlas data chunk: [`nordic.atlas-details.0079.506f362f7773c044.js`](./nordic.atlas-details.0079.506f362f7773c044.js)
- Static atlas data chunk: [`nordic.atlas-details.0080.65aec897ab8e1e16.js`](./nordic.atlas-details.0080.65aec897ab8e1e16.js)
- Static atlas data chunk: [`nordic.atlas-details.0081.882a8330b6445ae6.js`](./nordic.atlas-details.0081.882a8330b6445ae6.js)
- Static atlas data chunk: [`nordic.atlas-details.0082.74bd5b207bcabd5f.js`](./nordic.atlas-details.0082.74bd5b207bcabd5f.js)
- Static atlas data chunk: [`nordic.atlas-details.0083.56fdee0785a6c1be.js`](./nordic.atlas-details.0083.56fdee0785a6c1be.js)
- Static atlas data chunk: [`nordic.atlas-details.0084.003bc365a5d51d98.js`](./nordic.atlas-details.0084.003bc365a5d51d98.js)
- Static atlas data chunk: [`nordic.atlas-details.0085.3532c29be05cad37.js`](./nordic.atlas-details.0085.3532c29be05cad37.js)
- Static atlas data chunk: [`nordic.atlas-details.0086.ef45b03e96492903.js`](./nordic.atlas-details.0086.ef45b03e96492903.js)
- Static atlas data chunk: [`nordic.atlas-details.0087.154e553707302bb8.js`](./nordic.atlas-details.0087.154e553707302bb8.js)
- Static atlas data chunk: [`nordic.atlas-details.0088.7b9a5208f7b1ee76.js`](./nordic.atlas-details.0088.7b9a5208f7b1ee76.js)
- Static atlas data chunk: [`nordic.atlas-details.0089.df074c826e2a5903.js`](./nordic.atlas-details.0089.df074c826e2a5903.js)
- Static atlas data chunk: [`nordic.atlas-details.0090.36953a10779b5fc6.js`](./nordic.atlas-details.0090.36953a10779b5fc6.js)
- Static atlas data chunk: [`nordic.atlas-details.0091.f81a9771861449e6.js`](./nordic.atlas-details.0091.f81a9771861449e6.js)
- Static atlas data chunk: [`nordic.atlas-details.0092.338de298b44b3239.js`](./nordic.atlas-details.0092.338de298b44b3239.js)
- Static atlas data chunk: [`nordic.atlas-details.0093.46b835e6335daf0f.js`](./nordic.atlas-details.0093.46b835e6335daf0f.js)
- Static atlas data chunk: [`nordic.atlas-details.0094.d9adce9bdd4914ac.js`](./nordic.atlas-details.0094.d9adce9bdd4914ac.js)
- Static atlas data chunk: [`nordic.atlas-details.0095.7f14b054347d3978.js`](./nordic.atlas-details.0095.7f14b054347d3978.js)
- Static atlas data chunk: [`nordic.atlas-details.0096.5a86fb7a93dc624d.js`](./nordic.atlas-details.0096.5a86fb7a93dc624d.js)
- Static atlas data chunk: [`nordic.atlas-details.0097.170d4f381d53a86f.js`](./nordic.atlas-details.0097.170d4f381d53a86f.js)
- Static atlas data chunk: [`nordic.atlas-details.0098.cbb6ab6132e8338e.js`](./nordic.atlas-details.0098.cbb6ab6132e8338e.js)
- Static atlas data chunk: [`nordic.atlas-details.0099.429c83ad3a70c68b.js`](./nordic.atlas-details.0099.429c83ad3a70c68b.js)
- Static atlas data chunk: [`nordic.atlas-details.0100.91b5cde9096bca3e.js`](./nordic.atlas-details.0100.91b5cde9096bca3e.js)
- Static atlas data chunk: [`nordic.atlas-details.0101.a861fd3bc20a0a26.js`](./nordic.atlas-details.0101.a861fd3bc20a0a26.js)
- Static atlas data chunk: [`nordic.atlas-details.0102.aaff9bb23172f8ba.js`](./nordic.atlas-details.0102.aaff9bb23172f8ba.js)
- Static atlas data chunk: [`nordic.atlas-details.0103.7a627e2983323e13.js`](./nordic.atlas-details.0103.7a627e2983323e13.js)
- Static atlas data chunk: [`nordic.atlas-details.0104.41ceadcab394dacc.js`](./nordic.atlas-details.0104.41ceadcab394dacc.js)
- Static atlas data chunk: [`nordic.atlas-details.0105.01bb656768e66631.js`](./nordic.atlas-details.0105.01bb656768e66631.js)
- Static atlas data chunk: [`nordic.atlas-details.0106.7dcd33b3f08d4137.js`](./nordic.atlas-details.0106.7dcd33b3f08d4137.js)
- Static atlas data chunk: [`nordic.atlas-details.0107.e07252b4a9153f81.js`](./nordic.atlas-details.0107.e07252b4a9153f81.js)
- Static atlas data chunk: [`nordic.atlas-details.0108.ffc7ad925ac14585.js`](./nordic.atlas-details.0108.ffc7ad925ac14585.js)
- Static atlas data chunk: [`nordic.atlas-details.0109.fe06d35265d4f505.js`](./nordic.atlas-details.0109.fe06d35265d4f505.js)
- Static atlas data chunk: [`nordic.atlas-details.0110.6d82c00144317505.js`](./nordic.atlas-details.0110.6d82c00144317505.js)
- Static atlas data chunk: [`nordic.atlas-details.0111.95628c3402b69617.js`](./nordic.atlas-details.0111.95628c3402b69617.js)
- Static atlas data chunk: [`nordic.atlas-details.0112.91d15469e0627c5d.js`](./nordic.atlas-details.0112.91d15469e0627c5d.js)
- Static atlas data chunk: [`nordic.atlas-details.0113.f02c7127cabdce1a.js`](./nordic.atlas-details.0113.f02c7127cabdce1a.js)
- Static atlas data chunk: [`nordic.atlas-details.0114.5e12b19595861fe4.js`](./nordic.atlas-details.0114.5e12b19595861fe4.js)
- Static atlas data chunk: [`nordic.atlas-details.0115.1cff15d42628eba1.js`](./nordic.atlas-details.0115.1cff15d42628eba1.js)
- Static atlas data chunk: [`nordic.atlas-details.0116.722381c5829002e9.js`](./nordic.atlas-details.0116.722381c5829002e9.js)
- Static atlas data chunk: [`nordic.atlas-details.0117.24e6aeefea35fa0d.js`](./nordic.atlas-details.0117.24e6aeefea35fa0d.js)
- Static atlas data chunk: [`nordic.atlas-details.0118.816c365ecabd8695.js`](./nordic.atlas-details.0118.816c365ecabd8695.js)
- Static atlas data chunk: [`nordic.atlas-details.0119.1e7987e43905c15b.js`](./nordic.atlas-details.0119.1e7987e43905c15b.js)
- Static atlas data chunk: [`nordic.atlas-details.0120.5336ee8c3782641a.js`](./nordic.atlas-details.0120.5336ee8c3782641a.js)
- Static atlas data chunk: [`nordic.atlas-details.0121.c4dc6ad84ddab5ff.js`](./nordic.atlas-details.0121.c4dc6ad84ddab5ff.js)
- Static atlas data chunk: [`nordic.atlas-details.0122.335735d104662aa3.js`](./nordic.atlas-details.0122.335735d104662aa3.js)
- Static atlas data chunk: [`nordic.atlas-details.0123.4b5d661d400f9b7b.js`](./nordic.atlas-details.0123.4b5d661d400f9b7b.js)
- Static atlas data chunk: [`nordic.atlas-details.0124.79c9e233f5a61652.js`](./nordic.atlas-details.0124.79c9e233f5a61652.js)
- Static atlas data chunk: [`nordic.atlas-details.0125.dcb852d99dd979fe.js`](./nordic.atlas-details.0125.dcb852d99dd979fe.js)
- Static atlas data chunk: [`nordic.atlas-details.0126.f73d5c9bea0adcfc.js`](./nordic.atlas-details.0126.f73d5c9bea0adcfc.js)
- Static atlas data chunk: [`nordic.atlas-details.0127.63e9ddd40199f575.js`](./nordic.atlas-details.0127.63e9ddd40199f575.js)
- Static atlas data chunk: [`nordic.atlas-details.0128.03085c597a670076.js`](./nordic.atlas-details.0128.03085c597a670076.js)
- Static atlas data chunk: [`nordic.atlas-details.0129.9c7e509b40c377f1.js`](./nordic.atlas-details.0129.9c7e509b40c377f1.js)
- Static atlas data chunk: [`nordic.atlas-details.0130.ec6cd7ed8268e53e.js`](./nordic.atlas-details.0130.ec6cd7ed8268e53e.js)
- Static atlas data chunk: [`nordic.atlas-details.0131.6b0b123e01545f3b.js`](./nordic.atlas-details.0131.6b0b123e01545f3b.js)
- Static atlas data chunk: [`nordic.atlas-details.0132.953684a8b5c06755.js`](./nordic.atlas-details.0132.953684a8b5c06755.js)
- Static atlas data chunk: [`nordic.atlas-details.0133.7aa1c58b25b0b138.js`](./nordic.atlas-details.0133.7aa1c58b25b0b138.js)
- Static atlas data chunk: [`nordic.atlas-details.0134.9ae941d71951bc23.js`](./nordic.atlas-details.0134.9ae941d71951bc23.js)
- Static atlas data chunk: [`nordic.atlas-details.0135.43a41a536a6663f8.js`](./nordic.atlas-details.0135.43a41a536a6663f8.js)
- Static atlas data chunk: [`nordic.atlas-details.0136.c9b44224081b9b8c.js`](./nordic.atlas-details.0136.c9b44224081b9b8c.js)
- Static atlas data chunk: [`nordic.atlas-details.0137.f6fe51596a284921.js`](./nordic.atlas-details.0137.f6fe51596a284921.js)
- Static atlas data chunk: [`nordic.atlas-details.0138.3ef1016ef6ee997b.js`](./nordic.atlas-details.0138.3ef1016ef6ee997b.js)
- Static atlas data chunk: [`nordic.atlas-details.0139.4695f8aa64737288.js`](./nordic.atlas-details.0139.4695f8aa64737288.js)
- Static atlas data chunk: [`nordic.atlas-details.0140.15f3b5a0b3712ca1.js`](./nordic.atlas-details.0140.15f3b5a0b3712ca1.js)
- Static atlas data chunk: [`nordic.atlas-details.0141.33705d0e19bb38a5.js`](./nordic.atlas-details.0141.33705d0e19bb38a5.js)
- Static atlas data chunk: [`nordic.atlas-details.0142.f398fa0e3567164b.js`](./nordic.atlas-details.0142.f398fa0e3567164b.js)
- Static atlas data chunk: [`nordic.atlas-edges.0143.f073881bb5fd414d.js`](./nordic.atlas-edges.0143.f073881bb5fd414d.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0144.bdd7978840036a99.js`](./nordic.atlas-sequences.0144.bdd7978840036a99.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0145.fc272f4db0c433e4.js`](./nordic.atlas-indexes.0145.fc272f4db0c433e4.js)
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
| SEAD sites | `scope_specific_overlay` | Environmental archaeology sites staged from the SEAD normalization bundle. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `9738` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Neotoma sample pollen-presence context | `scope_specific_overlay` | Dated source samples with positive reported pollen observations; not reviewed pollen-sum events. | `3569` |
| Neotoma literal ecological codes | `scope_specific_overlay` | Literal source ecological codes without cross-source equivalence or propagation claims. | `8778` |
| Neotoma exact source taxa | `scope_specific_overlay` | Exact source taxon identities without accepted ecological classification or propagation claims. | `74580` |
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

- Total animal locality points: `4`
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
| approximate | 2 |
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
| pig | Sus scrofa domesticus | domesticated_core | 2 |


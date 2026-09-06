# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-07` from Homo
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
- Default basemap: `street`
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
- Wild and progenitor animal locality GeoJSON: [`nordic_progenitor_animal_localities.geojson`](./nordic_progenitor_animal_localities.geojson)
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.a3ecb19ea62aac9d.js`](./nordic.atlas-provenance.0000.a3ecb19ea62aac9d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.e2d4567c620c4979.js`](./nordic.atlas-nodes.0001.e2d4567c620c4979.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.b44278f585683b9a.js`](./nordic.atlas-nodes.0002.b44278f585683b9a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.54b169675c6e5438.js`](./nordic.atlas-nodes.0003.54b169675c6e5438.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.a16b3ceb002b07dd.js`](./nordic.atlas-nodes.0004.a16b3ceb002b07dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.f6bc79b6c705229d.js`](./nordic.atlas-nodes.0005.f6bc79b6c705229d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.09c727b90cdc668c.js`](./nordic.atlas-nodes.0006.09c727b90cdc668c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.d5d9f7ff0a50777e.js`](./nordic.atlas-nodes.0007.d5d9f7ff0a50777e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.da5ea2cc41f0fd9f.js`](./nordic.atlas-nodes.0008.da5ea2cc41f0fd9f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.f014b62463bd7c66.js`](./nordic.atlas-nodes.0009.f014b62463bd7c66.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.35a2a7819687fe6e.js`](./nordic.atlas-nodes.0010.35a2a7819687fe6e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.876651fe1c388bd0.js`](./nordic.atlas-nodes.0011.876651fe1c388bd0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.764a68ec34a944c2.js`](./nordic.atlas-nodes.0012.764a68ec34a944c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.6f6dc719c3019171.js`](./nordic.atlas-nodes.0013.6f6dc719c3019171.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.e1b7481f9e726c82.js`](./nordic.atlas-nodes.0014.e1b7481f9e726c82.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.6fb0bf73f971f864.js`](./nordic.atlas-nodes.0015.6fb0bf73f971f864.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.88cdf70aed4db690.js`](./nordic.atlas-nodes.0016.88cdf70aed4db690.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.f7c7f1c486d61e64.js`](./nordic.atlas-nodes.0017.f7c7f1c486d61e64.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.99d009767dc43df9.js`](./nordic.atlas-nodes.0018.99d009767dc43df9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.a8d7684ccabcc6ba.js`](./nordic.atlas-nodes.0019.a8d7684ccabcc6ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.6b190569c6cd859e.js`](./nordic.atlas-nodes.0020.6b190569c6cd859e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.842ee7345ff49408.js`](./nordic.atlas-nodes.0021.842ee7345ff49408.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.2f667e713075d80e.js`](./nordic.atlas-nodes.0022.2f667e713075d80e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.eac19956bcf4d3cc.js`](./nordic.atlas-nodes.0023.eac19956bcf4d3cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.6f33e4b7948a5f50.js`](./nordic.atlas-nodes.0024.6f33e4b7948a5f50.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.badd1256f8f55343.js`](./nordic.atlas-nodes.0025.badd1256f8f55343.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.8e9ab83f167877d3.js`](./nordic.atlas-nodes.0026.8e9ab83f167877d3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.969bf0f08085f408.js`](./nordic.atlas-nodes.0027.969bf0f08085f408.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.f636ea70c8c8ec84.js`](./nordic.atlas-nodes.0028.f636ea70c8c8ec84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.98d0487d7e853399.js`](./nordic.atlas-nodes.0029.98d0487d7e853399.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.0e9cab1647c32a9f.js`](./nordic.atlas-nodes.0030.0e9cab1647c32a9f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.59fc3dbf4ad7a951.js`](./nordic.atlas-nodes.0031.59fc3dbf4ad7a951.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.82db3af4ab42d4ff.js`](./nordic.atlas-nodes.0032.82db3af4ab42d4ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.9c6fef9ea83fc938.js`](./nordic.atlas-nodes.0033.9c6fef9ea83fc938.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.4fe3fffa1d386521.js`](./nordic.atlas-nodes.0034.4fe3fffa1d386521.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.8d22e2548e0df704.js`](./nordic.atlas-nodes.0035.8d22e2548e0df704.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.6afb1f23dbe6d59b.js`](./nordic.atlas-nodes.0036.6afb1f23dbe6d59b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.3fe5cafb64b22c63.js`](./nordic.atlas-nodes.0037.3fe5cafb64b22c63.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.d6f68fc9cee2adf6.js`](./nordic.atlas-nodes.0038.d6f68fc9cee2adf6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.fca25e08ec41062d.js`](./nordic.atlas-nodes.0039.fca25e08ec41062d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.5ef195c4e0b6e157.js`](./nordic.atlas-nodes.0040.5ef195c4e0b6e157.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.0fe0f68b4b48a224.js`](./nordic.atlas-nodes.0041.0fe0f68b4b48a224.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.2d4005cd09c6491a.js`](./nordic.atlas-nodes.0042.2d4005cd09c6491a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.a722fd84f065712c.js`](./nordic.atlas-nodes.0043.a722fd84f065712c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.3924ddb7dccba3c2.js`](./nordic.atlas-nodes.0044.3924ddb7dccba3c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.641651907a5b188d.js`](./nordic.atlas-nodes.0045.641651907a5b188d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.9e610e665f6d58da.js`](./nordic.atlas-nodes.0046.9e610e665f6d58da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.c69c73a61b019ddb.js`](./nordic.atlas-nodes.0047.c69c73a61b019ddb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.f433004b0c7bf013.js`](./nordic.atlas-nodes.0048.f433004b0c7bf013.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.c84c0e3cd1be4f8a.js`](./nordic.atlas-nodes.0049.c84c0e3cd1be4f8a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.599e47e461a1171a.js`](./nordic.atlas-nodes.0050.599e47e461a1171a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.e493d09605c9c0ba.js`](./nordic.atlas-nodes.0051.e493d09605c9c0ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.93237ae9ed63bc9f.js`](./nordic.atlas-nodes.0052.93237ae9ed63bc9f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.7f38d655f3d5cda6.js`](./nordic.atlas-nodes.0053.7f38d655f3d5cda6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.67facb76fcd29c9b.js`](./nordic.atlas-nodes.0054.67facb76fcd29c9b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.abb24f67ef5ad4b6.js`](./nordic.atlas-nodes.0055.abb24f67ef5ad4b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.32eebcc5aea40f4c.js`](./nordic.atlas-nodes.0056.32eebcc5aea40f4c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.836299baefbdb2aa.js`](./nordic.atlas-nodes.0057.836299baefbdb2aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.d90054a71f35312f.js`](./nordic.atlas-nodes.0058.d90054a71f35312f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.3701199640ec266e.js`](./nordic.atlas-nodes.0059.3701199640ec266e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.a8526e7a3c495d2d.js`](./nordic.atlas-nodes.0060.a8526e7a3c495d2d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.943dfb016e038ea8.js`](./nordic.atlas-nodes.0061.943dfb016e038ea8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.a786fa584c18480c.js`](./nordic.atlas-nodes.0062.a786fa584c18480c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.b65f2a7057a64847.js`](./nordic.atlas-nodes.0063.b65f2a7057a64847.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.7dbcc7447406d798.js`](./nordic.atlas-nodes.0064.7dbcc7447406d798.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.cffd3ed1d4001590.js`](./nordic.atlas-nodes.0065.cffd3ed1d4001590.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.55927a3f2f63b972.js`](./nordic.atlas-nodes.0066.55927a3f2f63b972.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.5c16ad0b38a37c67.js`](./nordic.atlas-nodes.0067.5c16ad0b38a37c67.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.23f2e3513964c6f7.js`](./nordic.atlas-nodes.0068.23f2e3513964c6f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.9ba313e22e28616e.js`](./nordic.atlas-nodes.0069.9ba313e22e28616e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.240ef6c3e9e37de2.js`](./nordic.atlas-nodes.0070.240ef6c3e9e37de2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.ba6e39b7bf1d5fc8.js`](./nordic.atlas-nodes.0071.ba6e39b7bf1d5fc8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.f4a707ef9e6a06ae.js`](./nordic.atlas-nodes.0072.f4a707ef9e6a06ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.69bfc04448fe721b.js`](./nordic.atlas-nodes.0073.69bfc04448fe721b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.191a0503bf4a7901.js`](./nordic.atlas-nodes.0074.191a0503bf4a7901.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.09dfabcdaefc837d.js`](./nordic.atlas-nodes.0075.09dfabcdaefc837d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.11df7a38df9d6840.js`](./nordic.atlas-nodes.0076.11df7a38df9d6840.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.30e2c3cd6ea40512.js`](./nordic.atlas-nodes.0077.30e2c3cd6ea40512.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.05b9e3f87371e59b.js`](./nordic.atlas-nodes.0078.05b9e3f87371e59b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.7043482def166ac9.js`](./nordic.atlas-nodes.0079.7043482def166ac9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.ce83d44e4dc124f9.js`](./nordic.atlas-nodes.0080.ce83d44e4dc124f9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.155509c860f7ce1e.js`](./nordic.atlas-nodes.0081.155509c860f7ce1e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.be8fee625322480f.js`](./nordic.atlas-nodes.0082.be8fee625322480f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.7218ee327bc7f309.js`](./nordic.atlas-nodes.0083.7218ee327bc7f309.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.d5350ffaa858f778.js`](./nordic.atlas-nodes.0084.d5350ffaa858f778.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.a2592de61416dad2.js`](./nordic.atlas-nodes.0085.a2592de61416dad2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.fc3f22d73b603b3c.js`](./nordic.atlas-nodes.0086.fc3f22d73b603b3c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.af37dad326bec010.js`](./nordic.atlas-nodes.0087.af37dad326bec010.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.1a7f65bcf4480cbd.js`](./nordic.atlas-nodes.0088.1a7f65bcf4480cbd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.787469c7aa56d849.js`](./nordic.atlas-nodes.0089.787469c7aa56d849.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.60e673b5c75dedb0.js`](./nordic.atlas-nodes.0090.60e673b5c75dedb0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.c9202c6015c1489e.js`](./nordic.atlas-nodes.0091.c9202c6015c1489e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.18b43f0fe0f54902.js`](./nordic.atlas-nodes.0092.18b43f0fe0f54902.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.59494eae94884fc5.js`](./nordic.atlas-nodes.0093.59494eae94884fc5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.2594186b0b72f1bd.js`](./nordic.atlas-nodes.0094.2594186b0b72f1bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.404f75c816e40022.js`](./nordic.atlas-nodes.0095.404f75c816e40022.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.008bfd985b02610c.js`](./nordic.atlas-nodes.0096.008bfd985b02610c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.5139b2b9f206f06d.js`](./nordic.atlas-nodes.0097.5139b2b9f206f06d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.f47915488ed11ea2.js`](./nordic.atlas-nodes.0098.f47915488ed11ea2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.20f4c0a9042d9aa4.js`](./nordic.atlas-nodes.0099.20f4c0a9042d9aa4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.0b8930c2e4968844.js`](./nordic.atlas-nodes.0100.0b8930c2e4968844.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.6bb9cdf7263fcacc.js`](./nordic.atlas-nodes.0101.6bb9cdf7263fcacc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.fc7977ab3b1437a0.js`](./nordic.atlas-nodes.0102.fc7977ab3b1437a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.d037877af540f13a.js`](./nordic.atlas-nodes.0103.d037877af540f13a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.a7cd0e4fa6cf1960.js`](./nordic.atlas-nodes.0104.a7cd0e4fa6cf1960.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.d40cdee82c012ce0.js`](./nordic.atlas-nodes.0105.d40cdee82c012ce0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.c3b2e5907ea35748.js`](./nordic.atlas-nodes.0106.c3b2e5907ea35748.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.45af678db3226f46.js`](./nordic.atlas-nodes.0107.45af678db3226f46.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.26191b5a0935db72.js`](./nordic.atlas-nodes.0108.26191b5a0935db72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.431832a061f17ef0.js`](./nordic.atlas-nodes.0109.431832a061f17ef0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.8a84df15cb6ae8d9.js`](./nordic.atlas-nodes.0110.8a84df15cb6ae8d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.435a80714608cc59.js`](./nordic.atlas-nodes.0111.435a80714608cc59.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.860ebd6feb52ea65.js`](./nordic.atlas-nodes.0112.860ebd6feb52ea65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.77fad48258ef007c.js`](./nordic.atlas-nodes.0113.77fad48258ef007c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.6daf772e86461116.js`](./nordic.atlas-nodes.0114.6daf772e86461116.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.69d651c881d327eb.js`](./nordic.atlas-nodes.0115.69d651c881d327eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.a747f1178f07ac3d.js`](./nordic.atlas-nodes.0116.a747f1178f07ac3d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.01dfaa91f3ebdf5a.js`](./nordic.atlas-nodes.0117.01dfaa91f3ebdf5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.f40844a465f93488.js`](./nordic.atlas-nodes.0118.f40844a465f93488.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.0455c97a5502ea2a.js`](./nordic.atlas-nodes.0119.0455c97a5502ea2a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.308a2b2e1d9835ac.js`](./nordic.atlas-nodes.0120.308a2b2e1d9835ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.af7618aa727a827a.js`](./nordic.atlas-nodes.0121.af7618aa727a827a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.897c8f978fc1d2bf.js`](./nordic.atlas-nodes.0122.897c8f978fc1d2bf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.42805dd32e1e7fb1.js`](./nordic.atlas-nodes.0123.42805dd32e1e7fb1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.565b68d107943c7d.js`](./nordic.atlas-nodes.0124.565b68d107943c7d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.21d439e6a2699b98.js`](./nordic.atlas-nodes.0125.21d439e6a2699b98.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.a5a84be4a5957c1d.js`](./nordic.atlas-nodes.0126.a5a84be4a5957c1d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.86e739d95e65976e.js`](./nordic.atlas-nodes.0127.86e739d95e65976e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.b9335b52a6791b07.js`](./nordic.atlas-nodes.0128.b9335b52a6791b07.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.270412b5f6774c43.js`](./nordic.atlas-nodes.0129.270412b5f6774c43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.6613d0e6343b796b.js`](./nordic.atlas-nodes.0130.6613d0e6343b796b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.b78dcf507028b94c.js`](./nordic.atlas-nodes.0131.b78dcf507028b94c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.51b6e50c16c8e86b.js`](./nordic.atlas-nodes.0132.51b6e50c16c8e86b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.617949a75c07dbf8.js`](./nordic.atlas-nodes.0133.617949a75c07dbf8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.01f6dca20799e90e.js`](./nordic.atlas-nodes.0134.01f6dca20799e90e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.fba01136d472f9df.js`](./nordic.atlas-nodes.0135.fba01136d472f9df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.f47e3186d384e24d.js`](./nordic.atlas-nodes.0136.f47e3186d384e24d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.f95c7743333f1538.js`](./nordic.atlas-nodes.0137.f95c7743333f1538.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.1cec1f6a5ff9ecbf.js`](./nordic.atlas-nodes.0138.1cec1f6a5ff9ecbf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.e7693cf5172145b2.js`](./nordic.atlas-nodes.0139.e7693cf5172145b2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.1abe8eefa906f0e7.js`](./nordic.atlas-nodes.0140.1abe8eefa906f0e7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.96ba9a0dab70f19d.js`](./nordic.atlas-nodes.0141.96ba9a0dab70f19d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.9e3cdeb7c4de6267.js`](./nordic.atlas-nodes.0142.9e3cdeb7c4de6267.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.7af16deb0cf0aa95.js`](./nordic.atlas-nodes.0143.7af16deb0cf0aa95.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.de41d9b31610354e.js`](./nordic.atlas-nodes.0144.de41d9b31610354e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.54f54c377da88269.js`](./nordic.atlas-nodes.0145.54f54c377da88269.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.050874b7cf136eff.js`](./nordic.atlas-nodes.0146.050874b7cf136eff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.c30904ffae0c8941.js`](./nordic.atlas-nodes.0147.c30904ffae0c8941.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.5d09070bf5ceecd4.js`](./nordic.atlas-nodes.0148.5d09070bf5ceecd4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.31248585b83a4e36.js`](./nordic.atlas-nodes.0149.31248585b83a4e36.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.ebe5bc0dafc68d65.js`](./nordic.atlas-nodes.0150.ebe5bc0dafc68d65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.288633986eea2ca1.js`](./nordic.atlas-nodes.0151.288633986eea2ca1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.811723378db198ea.js`](./nordic.atlas-nodes.0152.811723378db198ea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.27b2d01193179cd0.js`](./nordic.atlas-nodes.0153.27b2d01193179cd0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.b3124032fe26e110.js`](./nordic.atlas-nodes.0154.b3124032fe26e110.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.6640a7d1203b897c.js`](./nordic.atlas-nodes.0155.6640a7d1203b897c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.0a85aaefcf8cd799.js`](./nordic.atlas-nodes.0156.0a85aaefcf8cd799.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.db035b716f130fcb.js`](./nordic.atlas-nodes.0157.db035b716f130fcb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.bdbe62108fbf246d.js`](./nordic.atlas-nodes.0158.bdbe62108fbf246d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.b199c496a7b559f7.js`](./nordic.atlas-nodes.0159.b199c496a7b559f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.e93923f667876a38.js`](./nordic.atlas-nodes.0160.e93923f667876a38.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.047f3a6a813ea462.js`](./nordic.atlas-nodes.0161.047f3a6a813ea462.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.4a80eae9682fd0b4.js`](./nordic.atlas-nodes.0162.4a80eae9682fd0b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.36c44ef74fd34b81.js`](./nordic.atlas-nodes.0163.36c44ef74fd34b81.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.f9a4c40318a35872.js`](./nordic.atlas-nodes.0164.f9a4c40318a35872.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.11b2efed8a93bed3.js`](./nordic.atlas-details.0165.11b2efed8a93bed3.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.d4e3c494b6506349.js`](./nordic.atlas-details.0166.d4e3c494b6506349.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.731ca5ee7f66193d.js`](./nordic.atlas-details.0167.731ca5ee7f66193d.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.7845827143b0d224.js`](./nordic.atlas-details.0168.7845827143b0d224.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.aa33703d3b76efea.js`](./nordic.atlas-details.0169.aa33703d3b76efea.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.8ddb289714a0cea4.js`](./nordic.atlas-details.0170.8ddb289714a0cea4.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.a32f6125f5f98e27.js`](./nordic.atlas-details.0171.a32f6125f5f98e27.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.5486b792f281bd5d.js`](./nordic.atlas-details.0172.5486b792f281bd5d.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.dfcfe1e6e7d9a784.js`](./nordic.atlas-details.0173.dfcfe1e6e7d9a784.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.4c43dc4e80a40094.js`](./nordic.atlas-details.0174.4c43dc4e80a40094.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.9bd104d9e56f407e.js`](./nordic.atlas-details.0175.9bd104d9e56f407e.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.63888df36d0ffb3f.js`](./nordic.atlas-details.0176.63888df36d0ffb3f.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.808e16ab6ba8aee5.js`](./nordic.atlas-details.0177.808e16ab6ba8aee5.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.e9ec2589b2c72843.js`](./nordic.atlas-details.0178.e9ec2589b2c72843.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.c2f65617039a58f2.js`](./nordic.atlas-details.0179.c2f65617039a58f2.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.d596b3eb9023484a.js`](./nordic.atlas-details.0180.d596b3eb9023484a.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.486e7b59d1391d18.js`](./nordic.atlas-details.0181.486e7b59d1391d18.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.f1334a03eb9b1bd4.js`](./nordic.atlas-details.0182.f1334a03eb9b1bd4.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.1115ce88082b764b.js`](./nordic.atlas-details.0183.1115ce88082b764b.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.fdbc0b972b1e312d.js`](./nordic.atlas-details.0184.fdbc0b972b1e312d.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.abb4305297b4dd94.js`](./nordic.atlas-details.0185.abb4305297b4dd94.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.e6ab4cf14dffa7bf.js`](./nordic.atlas-details.0186.e6ab4cf14dffa7bf.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.4459701a0e88e492.js`](./nordic.atlas-details.0187.4459701a0e88e492.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.347cd17e34293cd4.js`](./nordic.atlas-details.0188.347cd17e34293cd4.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.9e0489607b7fad77.js`](./nordic.atlas-details.0189.9e0489607b7fad77.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.aeb09ff19628329c.js`](./nordic.atlas-details.0190.aeb09ff19628329c.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.74c5176cb31ae7af.js`](./nordic.atlas-details.0191.74c5176cb31ae7af.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.f629366ea0f74050.js`](./nordic.atlas-details.0192.f629366ea0f74050.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.af28df8c00a3c8c7.js`](./nordic.atlas-details.0193.af28df8c00a3c8c7.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.f38426d86737d5ed.js`](./nordic.atlas-details.0194.f38426d86737d5ed.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.891ef4e27ec4df20.js`](./nordic.atlas-details.0195.891ef4e27ec4df20.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.cfd3852bf4206433.js`](./nordic.atlas-details.0196.cfd3852bf4206433.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.47f0fca5614f9a4e.js`](./nordic.atlas-details.0197.47f0fca5614f9a4e.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.41fda52bbb58c942.js`](./nordic.atlas-details.0198.41fda52bbb58c942.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.46c6a43bbe199800.js`](./nordic.atlas-details.0199.46c6a43bbe199800.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.a916e5a0ef784141.js`](./nordic.atlas-details.0200.a916e5a0ef784141.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.e3597a55f4bd80be.js`](./nordic.atlas-details.0201.e3597a55f4bd80be.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.7b34d36d112fff28.js`](./nordic.atlas-details.0202.7b34d36d112fff28.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.867214a0306d4911.js`](./nordic.atlas-details.0203.867214a0306d4911.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.d0a6566ead039456.js`](./nordic.atlas-details.0204.d0a6566ead039456.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.b0758c6d8e346f3e.js`](./nordic.atlas-details.0205.b0758c6d8e346f3e.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.c56bc3848ba597f3.js`](./nordic.atlas-details.0206.c56bc3848ba597f3.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.87237650a04db888.js`](./nordic.atlas-details.0207.87237650a04db888.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.bdf11d74cc1ea58a.js`](./nordic.atlas-details.0208.bdf11d74cc1ea58a.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.03a4bbd99c2d5ee3.js`](./nordic.atlas-details.0209.03a4bbd99c2d5ee3.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.862527ac33c5c643.js`](./nordic.atlas-details.0210.862527ac33c5c643.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.591e99ba6f9ec8d1.js`](./nordic.atlas-details.0211.591e99ba6f9ec8d1.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.f501d481dc6338bb.js`](./nordic.atlas-details.0212.f501d481dc6338bb.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.ea42279815b2e88c.js`](./nordic.atlas-details.0213.ea42279815b2e88c.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.fbbfa12c07e0b49c.js`](./nordic.atlas-details.0214.fbbfa12c07e0b49c.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.08f6049c258871c8.js`](./nordic.atlas-details.0215.08f6049c258871c8.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.4fb7b5115acec246.js`](./nordic.atlas-details.0216.4fb7b5115acec246.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.752d0cb4c7351fcb.js`](./nordic.atlas-details.0217.752d0cb4c7351fcb.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.db16a842ff15860c.js`](./nordic.atlas-details.0218.db16a842ff15860c.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.2ba94b6575e39f9e.js`](./nordic.atlas-details.0219.2ba94b6575e39f9e.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.3a28a5c7d3e8dd79.js`](./nordic.atlas-details.0220.3a28a5c7d3e8dd79.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.7aca291fb758f9b0.js`](./nordic.atlas-details.0221.7aca291fb758f9b0.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.6a2f9841bda313ae.js`](./nordic.atlas-details.0222.6a2f9841bda313ae.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.9db2e2be598c1b47.js`](./nordic.atlas-details.0223.9db2e2be598c1b47.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.5f380d04faa5b392.js`](./nordic.atlas-details.0224.5f380d04faa5b392.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.4f92a8799e5e5dfd.js`](./nordic.atlas-details.0225.4f92a8799e5e5dfd.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.88fce74b7039f786.js`](./nordic.atlas-details.0226.88fce74b7039f786.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.88dbdacc40e0398a.js`](./nordic.atlas-details.0227.88dbdacc40e0398a.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.9ec88091e88ee588.js`](./nordic.atlas-details.0228.9ec88091e88ee588.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.ae010a89293fd770.js`](./nordic.atlas-edges.0229.ae010a89293fd770.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.4d072cab3cdb1c38.js`](./nordic.atlas-sequences.0230.4d072cab3cdb1c38.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.470ab01009f1bf41.js`](./nordic.atlas-indexes.0231.470ab01009f1bf41.js)
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
- Governed oldest-to-present playback storyboards: [`nordic_playback_storyboards.json`](./nordic_playback_storyboards.json)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | Pollen sequences staged from the LandClim normalization bundle. | `490` |
| Neotoma pollen sites | `scope_specific_overlay` | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `193` |
| SEAD sites | `scope_specific_overlay` | Environmental archaeology sites staged from the SEAD normalization bundle. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `9727` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Neotoma sample pollen-presence context | `scope_specific_overlay` | Dated source samples with positive reported pollen observations; not reviewed pollen-sum events. | `9988` |
| Neotoma literal ecological codes | `scope_specific_overlay` | Literal source ecological codes without cross-source equivalence or propagation claims. | `25165` |
| Neotoma exact source taxa | `scope_specific_overlay` | Exact source taxon identities without accepted ecological classification or propagation claims. | `215751` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |
| LandClim REVEALS time-window grids | `scope_specific_overlay` | Time-window-specific REVEALS grid estimates from published LandClim PANGAEA datasets. | `2515` |

## Governed Filters

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch
- Accepted scientific comparison when qualified classifications are available
- Neotoma source-sample, literal-code, and exact-label chronology
- Oldest-to-present BP window navigation and playback
- PANGAEA 937075 exact-window modeled context
- Modeled-context visible-frame export
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


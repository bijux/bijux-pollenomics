# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-06` from Homo
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
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.ecc9a0b5eb23a31e.js`](./nordic.atlas-provenance.0000.ecc9a0b5eb23a31e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.f56697df114e315c.js`](./nordic.atlas-nodes.0001.f56697df114e315c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.103f9673cc7e8d99.js`](./nordic.atlas-nodes.0002.103f9673cc7e8d99.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.014927ba62abc741.js`](./nordic.atlas-nodes.0003.014927ba62abc741.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.e9f4d98641bc24ee.js`](./nordic.atlas-nodes.0004.e9f4d98641bc24ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.cac1a76058cf6508.js`](./nordic.atlas-nodes.0005.cac1a76058cf6508.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.652aa069a8e1819f.js`](./nordic.atlas-nodes.0006.652aa069a8e1819f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.a36a03036e2c1db4.js`](./nordic.atlas-nodes.0007.a36a03036e2c1db4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.a8dd9454e1170f08.js`](./nordic.atlas-nodes.0008.a8dd9454e1170f08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.b63efd058540c051.js`](./nordic.atlas-nodes.0009.b63efd058540c051.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.7e1f0fdaa602f7b6.js`](./nordic.atlas-nodes.0010.7e1f0fdaa602f7b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.6ec56d25c70ae884.js`](./nordic.atlas-nodes.0011.6ec56d25c70ae884.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.4ea5df92c960fd17.js`](./nordic.atlas-nodes.0012.4ea5df92c960fd17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.746b01c195566049.js`](./nordic.atlas-nodes.0013.746b01c195566049.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.09ff6e035626669b.js`](./nordic.atlas-nodes.0014.09ff6e035626669b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.18ba97810ae43c88.js`](./nordic.atlas-nodes.0015.18ba97810ae43c88.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.90973994ab807e59.js`](./nordic.atlas-nodes.0016.90973994ab807e59.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.6b7b7931fd17afd8.js`](./nordic.atlas-nodes.0017.6b7b7931fd17afd8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.b5a35af3e7a56d88.js`](./nordic.atlas-nodes.0018.b5a35af3e7a56d88.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.75186cfc313df4f1.js`](./nordic.atlas-nodes.0019.75186cfc313df4f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.a132c04d6b429297.js`](./nordic.atlas-nodes.0020.a132c04d6b429297.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.5e710cf4253b3f2d.js`](./nordic.atlas-nodes.0021.5e710cf4253b3f2d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.7c17a7872a38079d.js`](./nordic.atlas-nodes.0022.7c17a7872a38079d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.1bbdede6ce1118eb.js`](./nordic.atlas-nodes.0023.1bbdede6ce1118eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.7a01ff84f4b3a9a0.js`](./nordic.atlas-nodes.0024.7a01ff84f4b3a9a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.ac6e9c2111bddf96.js`](./nordic.atlas-nodes.0025.ac6e9c2111bddf96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.9006896dff3e75b2.js`](./nordic.atlas-nodes.0026.9006896dff3e75b2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.e6c176de90b23a32.js`](./nordic.atlas-nodes.0027.e6c176de90b23a32.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.2f5350bb58c53c3f.js`](./nordic.atlas-nodes.0028.2f5350bb58c53c3f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.cf9e00d37cb30800.js`](./nordic.atlas-nodes.0029.cf9e00d37cb30800.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.07ee56c7347e3e07.js`](./nordic.atlas-nodes.0030.07ee56c7347e3e07.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.d46d824faa120937.js`](./nordic.atlas-nodes.0031.d46d824faa120937.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.de1e91efc2784f42.js`](./nordic.atlas-nodes.0032.de1e91efc2784f42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.175fd1f05bd8be72.js`](./nordic.atlas-nodes.0033.175fd1f05bd8be72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.28dbddcc6f279a2b.js`](./nordic.atlas-nodes.0034.28dbddcc6f279a2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.9a812d0e2d1b2c0f.js`](./nordic.atlas-nodes.0035.9a812d0e2d1b2c0f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.4236da9423951906.js`](./nordic.atlas-nodes.0036.4236da9423951906.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.4e2a8e9c21a9a4da.js`](./nordic.atlas-nodes.0037.4e2a8e9c21a9a4da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.fb925f7742e887b6.js`](./nordic.atlas-nodes.0038.fb925f7742e887b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.5335dbc80cbf1c8d.js`](./nordic.atlas-nodes.0039.5335dbc80cbf1c8d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.3fb20abe0faac65d.js`](./nordic.atlas-nodes.0040.3fb20abe0faac65d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.ea28f03dc03e0943.js`](./nordic.atlas-nodes.0041.ea28f03dc03e0943.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.31486a52cd91b705.js`](./nordic.atlas-nodes.0042.31486a52cd91b705.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.c11de125491fd092.js`](./nordic.atlas-nodes.0043.c11de125491fd092.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.856654148a71a1ed.js`](./nordic.atlas-nodes.0044.856654148a71a1ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.d11d321e0402e37c.js`](./nordic.atlas-nodes.0045.d11d321e0402e37c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.94dcc8d7843026ad.js`](./nordic.atlas-nodes.0046.94dcc8d7843026ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.dcd4ac573b2bbaff.js`](./nordic.atlas-nodes.0047.dcd4ac573b2bbaff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.ea98080a22f8fd04.js`](./nordic.atlas-nodes.0048.ea98080a22f8fd04.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.771a6d2817d60ae8.js`](./nordic.atlas-nodes.0049.771a6d2817d60ae8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.7489628c978627f9.js`](./nordic.atlas-nodes.0050.7489628c978627f9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.cb87c51f31755b6e.js`](./nordic.atlas-nodes.0051.cb87c51f31755b6e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.e59373729e2559b7.js`](./nordic.atlas-nodes.0052.e59373729e2559b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.d454ec0a8102fff7.js`](./nordic.atlas-nodes.0053.d454ec0a8102fff7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.c6f0f5d6268d2348.js`](./nordic.atlas-nodes.0054.c6f0f5d6268d2348.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.08063930e5134fe1.js`](./nordic.atlas-nodes.0055.08063930e5134fe1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.257e0985cb30b238.js`](./nordic.atlas-nodes.0056.257e0985cb30b238.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.009416b06d026f60.js`](./nordic.atlas-nodes.0057.009416b06d026f60.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.7541e37ff5d7a064.js`](./nordic.atlas-nodes.0058.7541e37ff5d7a064.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.e763ef4129acc44e.js`](./nordic.atlas-nodes.0059.e763ef4129acc44e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.8dd1e4234cdb36c0.js`](./nordic.atlas-nodes.0060.8dd1e4234cdb36c0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.042181e2fdd629f8.js`](./nordic.atlas-nodes.0061.042181e2fdd629f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.4628750587e5121e.js`](./nordic.atlas-nodes.0062.4628750587e5121e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.ab59f469f6c1158d.js`](./nordic.atlas-nodes.0063.ab59f469f6c1158d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.21613981df374794.js`](./nordic.atlas-nodes.0064.21613981df374794.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.32cc8686f0550264.js`](./nordic.atlas-nodes.0065.32cc8686f0550264.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.514168c2752a5020.js`](./nordic.atlas-nodes.0066.514168c2752a5020.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.9144e6049b39895a.js`](./nordic.atlas-nodes.0067.9144e6049b39895a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.93da91a203f741a0.js`](./nordic.atlas-nodes.0068.93da91a203f741a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.76ef455ce0c097b7.js`](./nordic.atlas-nodes.0069.76ef455ce0c097b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.a31bcae1bd5e9147.js`](./nordic.atlas-nodes.0070.a31bcae1bd5e9147.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.29a9f2764be0d6b8.js`](./nordic.atlas-nodes.0071.29a9f2764be0d6b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.9c1e1326692eb08e.js`](./nordic.atlas-nodes.0072.9c1e1326692eb08e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.f2f877f41be3463e.js`](./nordic.atlas-nodes.0073.f2f877f41be3463e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.053a608759e63393.js`](./nordic.atlas-nodes.0074.053a608759e63393.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.f46e3a683ad28b65.js`](./nordic.atlas-nodes.0075.f46e3a683ad28b65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.a9f57bd9fe8aa1e5.js`](./nordic.atlas-nodes.0076.a9f57bd9fe8aa1e5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.a63f40cbcef0efc0.js`](./nordic.atlas-nodes.0077.a63f40cbcef0efc0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.077cba04784e7584.js`](./nordic.atlas-nodes.0078.077cba04784e7584.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.fe939a74131d771a.js`](./nordic.atlas-nodes.0079.fe939a74131d771a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.9d8815fff2ab68d0.js`](./nordic.atlas-nodes.0080.9d8815fff2ab68d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.5cd757151d7e0ae8.js`](./nordic.atlas-nodes.0081.5cd757151d7e0ae8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.cf6d7aa6fe7430b3.js`](./nordic.atlas-nodes.0082.cf6d7aa6fe7430b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.4a7ab615f44a3714.js`](./nordic.atlas-nodes.0083.4a7ab615f44a3714.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.54b0a3a0e1fb6a19.js`](./nordic.atlas-nodes.0084.54b0a3a0e1fb6a19.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.5c7caf116ed9343c.js`](./nordic.atlas-nodes.0085.5c7caf116ed9343c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.d363b7bf1e819ece.js`](./nordic.atlas-nodes.0086.d363b7bf1e819ece.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.1fb31691c297cf4e.js`](./nordic.atlas-nodes.0087.1fb31691c297cf4e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.9a51995d7112c7eb.js`](./nordic.atlas-nodes.0088.9a51995d7112c7eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.5da4cdb4b921c23d.js`](./nordic.atlas-nodes.0089.5da4cdb4b921c23d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.02e086b464fc9db6.js`](./nordic.atlas-nodes.0090.02e086b464fc9db6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.0bd62f5ca79ed9a4.js`](./nordic.atlas-nodes.0091.0bd62f5ca79ed9a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.0de37bbe3e0d50ba.js`](./nordic.atlas-nodes.0092.0de37bbe3e0d50ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.ee0e9d8047b65e12.js`](./nordic.atlas-nodes.0093.ee0e9d8047b65e12.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.104b76445146a73e.js`](./nordic.atlas-nodes.0094.104b76445146a73e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.e166d598e0d9f653.js`](./nordic.atlas-nodes.0095.e166d598e0d9f653.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.c0c5b6cc52284b67.js`](./nordic.atlas-nodes.0096.c0c5b6cc52284b67.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.1667f94e1cd8e0db.js`](./nordic.atlas-nodes.0097.1667f94e1cd8e0db.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.8312f4ea497c4a5a.js`](./nordic.atlas-nodes.0098.8312f4ea497c4a5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.084e89ef452f7930.js`](./nordic.atlas-nodes.0099.084e89ef452f7930.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.271f62233d58e4f9.js`](./nordic.atlas-nodes.0100.271f62233d58e4f9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.254f0b65b5bb2ba9.js`](./nordic.atlas-nodes.0101.254f0b65b5bb2ba9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.ba11869b3cf66224.js`](./nordic.atlas-nodes.0102.ba11869b3cf66224.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.2eca30b6c335f5d6.js`](./nordic.atlas-nodes.0103.2eca30b6c335f5d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.dbbed62655b5bed3.js`](./nordic.atlas-nodes.0104.dbbed62655b5bed3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.4bc46dec8c82822b.js`](./nordic.atlas-nodes.0105.4bc46dec8c82822b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.07452d55da369ce4.js`](./nordic.atlas-nodes.0106.07452d55da369ce4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.68461fefd5eaf12e.js`](./nordic.atlas-nodes.0107.68461fefd5eaf12e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.48cdfb6f6acbef27.js`](./nordic.atlas-nodes.0108.48cdfb6f6acbef27.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.1ed7e378c6696417.js`](./nordic.atlas-nodes.0109.1ed7e378c6696417.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.3a7117f41a37af84.js`](./nordic.atlas-nodes.0110.3a7117f41a37af84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.85202df7497f30d3.js`](./nordic.atlas-nodes.0111.85202df7497f30d3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.75a34f96fc366368.js`](./nordic.atlas-nodes.0112.75a34f96fc366368.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.d5875393fcae7e8c.js`](./nordic.atlas-nodes.0113.d5875393fcae7e8c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.3272b8d84d6a764d.js`](./nordic.atlas-nodes.0114.3272b8d84d6a764d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.6a7a2e3c613f7a7f.js`](./nordic.atlas-nodes.0115.6a7a2e3c613f7a7f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.a8e1fb9a5dc42126.js`](./nordic.atlas-nodes.0116.a8e1fb9a5dc42126.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.268ba39842e20d76.js`](./nordic.atlas-nodes.0117.268ba39842e20d76.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.0388d7b9d6f6c8d0.js`](./nordic.atlas-nodes.0118.0388d7b9d6f6c8d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.12740529e0b8a5ac.js`](./nordic.atlas-nodes.0119.12740529e0b8a5ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.01d1aa14c1940812.js`](./nordic.atlas-nodes.0120.01d1aa14c1940812.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.67c69aa5f93ff3e8.js`](./nordic.atlas-nodes.0121.67c69aa5f93ff3e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.e35d6e8b5141c4bd.js`](./nordic.atlas-nodes.0122.e35d6e8b5141c4bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.3382dcad966598ab.js`](./nordic.atlas-nodes.0123.3382dcad966598ab.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.bbf827520b96fcc2.js`](./nordic.atlas-nodes.0124.bbf827520b96fcc2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.1839d0ba29e01424.js`](./nordic.atlas-nodes.0125.1839d0ba29e01424.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.d84c3926e0fb4b4e.js`](./nordic.atlas-nodes.0126.d84c3926e0fb4b4e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.a91bd89f1e484048.js`](./nordic.atlas-nodes.0127.a91bd89f1e484048.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.389bb8acdc95312d.js`](./nordic.atlas-nodes.0128.389bb8acdc95312d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.8f47db6afc46f383.js`](./nordic.atlas-nodes.0129.8f47db6afc46f383.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.a896efa4703b90ae.js`](./nordic.atlas-nodes.0130.a896efa4703b90ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.bb987c519051cb1b.js`](./nordic.atlas-nodes.0131.bb987c519051cb1b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.c0c6a237b6287e11.js`](./nordic.atlas-nodes.0132.c0c6a237b6287e11.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.c9e7ee53a0158d02.js`](./nordic.atlas-nodes.0133.c9e7ee53a0158d02.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.9bf78727f5818353.js`](./nordic.atlas-nodes.0134.9bf78727f5818353.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.47e8c2f4a5e710e6.js`](./nordic.atlas-nodes.0135.47e8c2f4a5e710e6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.083905e7db8a0fef.js`](./nordic.atlas-nodes.0136.083905e7db8a0fef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.6de5001670238cdf.js`](./nordic.atlas-nodes.0137.6de5001670238cdf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.48c01c61c2fe292d.js`](./nordic.atlas-nodes.0138.48c01c61c2fe292d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.7ef9849d364bbcad.js`](./nordic.atlas-nodes.0139.7ef9849d364bbcad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.26e2b411b132fb38.js`](./nordic.atlas-nodes.0140.26e2b411b132fb38.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.2b1c37c9b1956966.js`](./nordic.atlas-nodes.0141.2b1c37c9b1956966.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.00cf91f65c4623c3.js`](./nordic.atlas-nodes.0142.00cf91f65c4623c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.4e9a2ac25fef27b1.js`](./nordic.atlas-nodes.0143.4e9a2ac25fef27b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.2b95da02d8f8a30e.js`](./nordic.atlas-nodes.0144.2b95da02d8f8a30e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.d326edac7fd52c3b.js`](./nordic.atlas-nodes.0145.d326edac7fd52c3b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.b454e0451469d72c.js`](./nordic.atlas-nodes.0146.b454e0451469d72c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.feb3128b9a8aa20c.js`](./nordic.atlas-nodes.0147.feb3128b9a8aa20c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.24b28d1207b2c578.js`](./nordic.atlas-nodes.0148.24b28d1207b2c578.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.036e2017c1bd4bb3.js`](./nordic.atlas-nodes.0149.036e2017c1bd4bb3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.97159a3f263e2b17.js`](./nordic.atlas-nodes.0150.97159a3f263e2b17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.0d277bfc7c67adb9.js`](./nordic.atlas-nodes.0151.0d277bfc7c67adb9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.62b83ecf2aaa5799.js`](./nordic.atlas-nodes.0152.62b83ecf2aaa5799.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.0f22fdf032ed6690.js`](./nordic.atlas-nodes.0153.0f22fdf032ed6690.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.4277cb84485cd280.js`](./nordic.atlas-nodes.0154.4277cb84485cd280.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.e6666543fa1614e0.js`](./nordic.atlas-nodes.0155.e6666543fa1614e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.2ccb960339970e1f.js`](./nordic.atlas-nodes.0156.2ccb960339970e1f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.629bcf1244b43083.js`](./nordic.atlas-nodes.0157.629bcf1244b43083.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.1462906053b7eb11.js`](./nordic.atlas-nodes.0158.1462906053b7eb11.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.ff39006a49ffe95e.js`](./nordic.atlas-nodes.0159.ff39006a49ffe95e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.3ed7c22a47a26d6b.js`](./nordic.atlas-nodes.0160.3ed7c22a47a26d6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.bb13e25323fc9daa.js`](./nordic.atlas-nodes.0161.bb13e25323fc9daa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.f101abd4e4bfac72.js`](./nordic.atlas-nodes.0162.f101abd4e4bfac72.js)
- Static atlas data chunk: [`nordic.atlas-details.0163.f3586c8d79f838b6.js`](./nordic.atlas-details.0163.f3586c8d79f838b6.js)
- Static atlas data chunk: [`nordic.atlas-details.0164.a51aade387f46532.js`](./nordic.atlas-details.0164.a51aade387f46532.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.45ec29c63e10dcec.js`](./nordic.atlas-details.0165.45ec29c63e10dcec.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.b901c7853f03fc3c.js`](./nordic.atlas-details.0166.b901c7853f03fc3c.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.34101f20fcb4c35a.js`](./nordic.atlas-details.0167.34101f20fcb4c35a.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.90bcb938911c686d.js`](./nordic.atlas-details.0168.90bcb938911c686d.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.f8d39a83b9790f39.js`](./nordic.atlas-details.0169.f8d39a83b9790f39.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.ca882dfa175cf8f8.js`](./nordic.atlas-details.0170.ca882dfa175cf8f8.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.f6ce675cac78dbca.js`](./nordic.atlas-details.0171.f6ce675cac78dbca.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.4e4bff74d366bc15.js`](./nordic.atlas-details.0172.4e4bff74d366bc15.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.38c0b304d5e1f305.js`](./nordic.atlas-details.0173.38c0b304d5e1f305.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.741f397442931148.js`](./nordic.atlas-details.0174.741f397442931148.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.6f6c4737d42e77f0.js`](./nordic.atlas-details.0175.6f6c4737d42e77f0.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.a6c576373fc5840e.js`](./nordic.atlas-details.0176.a6c576373fc5840e.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.0c92ee5cc46a892d.js`](./nordic.atlas-details.0177.0c92ee5cc46a892d.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.9554cbeef9be16b5.js`](./nordic.atlas-details.0178.9554cbeef9be16b5.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.3f3876baccc8547a.js`](./nordic.atlas-details.0179.3f3876baccc8547a.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.06c1223ed318db67.js`](./nordic.atlas-details.0180.06c1223ed318db67.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.dc3d5cf8d4a770b9.js`](./nordic.atlas-details.0181.dc3d5cf8d4a770b9.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.6f4f17bdfe3e7eaf.js`](./nordic.atlas-details.0182.6f4f17bdfe3e7eaf.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.4ce905123d408bb1.js`](./nordic.atlas-details.0183.4ce905123d408bb1.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.c5231998cc01ac2d.js`](./nordic.atlas-details.0184.c5231998cc01ac2d.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.f2ea0247486c8555.js`](./nordic.atlas-details.0185.f2ea0247486c8555.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.2a028f169808e2cc.js`](./nordic.atlas-details.0186.2a028f169808e2cc.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.f77a6e9eabcb896b.js`](./nordic.atlas-details.0187.f77a6e9eabcb896b.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.23418278162432f8.js`](./nordic.atlas-details.0188.23418278162432f8.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.e0020475972ab545.js`](./nordic.atlas-details.0189.e0020475972ab545.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.0610761f5dbfe623.js`](./nordic.atlas-details.0190.0610761f5dbfe623.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.d9aa11f07d240dbc.js`](./nordic.atlas-details.0191.d9aa11f07d240dbc.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.23d0eb5424d9fdb5.js`](./nordic.atlas-details.0192.23d0eb5424d9fdb5.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.491bd3ed4767bb96.js`](./nordic.atlas-details.0193.491bd3ed4767bb96.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.281a27ff18cf5883.js`](./nordic.atlas-details.0194.281a27ff18cf5883.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.799e980794f6f72b.js`](./nordic.atlas-details.0195.799e980794f6f72b.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.f6184b3626d28b53.js`](./nordic.atlas-details.0196.f6184b3626d28b53.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.c6d2ec579e78a05a.js`](./nordic.atlas-details.0197.c6d2ec579e78a05a.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.1df0d6252968e471.js`](./nordic.atlas-details.0198.1df0d6252968e471.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.972f2de91e2d84be.js`](./nordic.atlas-details.0199.972f2de91e2d84be.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.ba8f6e6f13639fc5.js`](./nordic.atlas-details.0200.ba8f6e6f13639fc5.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.913fdbd6b9ab18a4.js`](./nordic.atlas-details.0201.913fdbd6b9ab18a4.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.01a38198576c24d2.js`](./nordic.atlas-details.0202.01a38198576c24d2.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.20b95271a6e8db66.js`](./nordic.atlas-details.0203.20b95271a6e8db66.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.f178c974e2050650.js`](./nordic.atlas-details.0204.f178c974e2050650.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.4ebefe8b128cd168.js`](./nordic.atlas-details.0205.4ebefe8b128cd168.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.d1e9904c1b7bd1ca.js`](./nordic.atlas-details.0206.d1e9904c1b7bd1ca.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.a0d2c5ede3f02606.js`](./nordic.atlas-details.0207.a0d2c5ede3f02606.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.fc962604ff578462.js`](./nordic.atlas-details.0208.fc962604ff578462.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.587d3951b8bb55f9.js`](./nordic.atlas-details.0209.587d3951b8bb55f9.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.5e0497e985c32eb7.js`](./nordic.atlas-details.0210.5e0497e985c32eb7.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.75312d62088eaf19.js`](./nordic.atlas-details.0211.75312d62088eaf19.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.4f0310eb850fc215.js`](./nordic.atlas-details.0212.4f0310eb850fc215.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.ac353ba1bf1c82ac.js`](./nordic.atlas-details.0213.ac353ba1bf1c82ac.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.95ff06ace8685de2.js`](./nordic.atlas-details.0214.95ff06ace8685de2.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.48246b971b0b3be0.js`](./nordic.atlas-details.0215.48246b971b0b3be0.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.a1fb9b799c994ed4.js`](./nordic.atlas-details.0216.a1fb9b799c994ed4.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.3ef074298a0f928a.js`](./nordic.atlas-details.0217.3ef074298a0f928a.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.39ce9bd6bba49526.js`](./nordic.atlas-details.0218.39ce9bd6bba49526.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.6e1eee41f2944918.js`](./nordic.atlas-details.0219.6e1eee41f2944918.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.9a4701b5b716b6d9.js`](./nordic.atlas-details.0220.9a4701b5b716b6d9.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.64427baa0e905c09.js`](./nordic.atlas-details.0221.64427baa0e905c09.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.3c2cef2efb706c19.js`](./nordic.atlas-details.0222.3c2cef2efb706c19.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.fce48af93688ad2b.js`](./nordic.atlas-details.0223.fce48af93688ad2b.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.6eca96a140c3853d.js`](./nordic.atlas-details.0224.6eca96a140c3853d.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.05f4cc8761c01121.js`](./nordic.atlas-details.0225.05f4cc8761c01121.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.72df52fc6c2142d7.js`](./nordic.atlas-details.0226.72df52fc6c2142d7.js)
- Static atlas data chunk: [`nordic.atlas-edges.0227.b48f7bf144cbff5e.js`](./nordic.atlas-edges.0227.b48f7bf144cbff5e.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0228.5dc04b5203ba2cb1.js`](./nordic.atlas-sequences.0228.5dc04b5203ba2cb1.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0229.4cf169b48a784bef.js`](./nordic.atlas-indexes.0229.4cf169b48a784bef.js)
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
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `9738` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
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


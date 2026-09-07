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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.f9104d051c028902.js`](./nordic.atlas-provenance.0000.f9104d051c028902.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.a1df597ca5c59897.js`](./nordic.atlas-nodes.0001.a1df597ca5c59897.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.18ec8fea748aabf0.js`](./nordic.atlas-nodes.0002.18ec8fea748aabf0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.99a18e5db327ad83.js`](./nordic.atlas-nodes.0003.99a18e5db327ad83.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.03cd97a27ae95777.js`](./nordic.atlas-nodes.0004.03cd97a27ae95777.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.95af11396093687a.js`](./nordic.atlas-nodes.0005.95af11396093687a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.29ad85be101c7d97.js`](./nordic.atlas-nodes.0006.29ad85be101c7d97.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.0c41f098df6ef5c7.js`](./nordic.atlas-nodes.0007.0c41f098df6ef5c7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.f09ca24cb9ab5c33.js`](./nordic.atlas-nodes.0008.f09ca24cb9ab5c33.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.46a3772561ecb2e7.js`](./nordic.atlas-nodes.0009.46a3772561ecb2e7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.3fc4b671eb56d26c.js`](./nordic.atlas-nodes.0010.3fc4b671eb56d26c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.603383fbde0eb0cc.js`](./nordic.atlas-nodes.0011.603383fbde0eb0cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.63b4bbacce3554a1.js`](./nordic.atlas-nodes.0012.63b4bbacce3554a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.81f63c7b3c0acbee.js`](./nordic.atlas-nodes.0013.81f63c7b3c0acbee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.216208a566c6967c.js`](./nordic.atlas-nodes.0014.216208a566c6967c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.3c712530c989b5df.js`](./nordic.atlas-nodes.0015.3c712530c989b5df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.3547a7e39c10d6d7.js`](./nordic.atlas-nodes.0016.3547a7e39c10d6d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.e0d26a054d422819.js`](./nordic.atlas-nodes.0017.e0d26a054d422819.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.4fc477a074def9b8.js`](./nordic.atlas-nodes.0018.4fc477a074def9b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.8cce853801bb6be2.js`](./nordic.atlas-nodes.0019.8cce853801bb6be2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.27baa628b5f538b8.js`](./nordic.atlas-nodes.0020.27baa628b5f538b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.5c419b72ce43d800.js`](./nordic.atlas-nodes.0021.5c419b72ce43d800.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.87805801b521ca5b.js`](./nordic.atlas-nodes.0022.87805801b521ca5b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.6789382d2d494f7b.js`](./nordic.atlas-nodes.0023.6789382d2d494f7b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.d19e5e19604c5af9.js`](./nordic.atlas-nodes.0024.d19e5e19604c5af9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.00310a630c287d96.js`](./nordic.atlas-nodes.0025.00310a630c287d96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.43229e8afa3c7c03.js`](./nordic.atlas-nodes.0026.43229e8afa3c7c03.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.ce3bf9051e706fb1.js`](./nordic.atlas-nodes.0027.ce3bf9051e706fb1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.a7a5bda6a70e9fb1.js`](./nordic.atlas-nodes.0028.a7a5bda6a70e9fb1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.4c1f9f5c54f34ed1.js`](./nordic.atlas-nodes.0029.4c1f9f5c54f34ed1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.5f92a020965f6dc3.js`](./nordic.atlas-nodes.0030.5f92a020965f6dc3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.d8f2c53c124702d2.js`](./nordic.atlas-nodes.0031.d8f2c53c124702d2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.7a00395262562d0d.js`](./nordic.atlas-nodes.0032.7a00395262562d0d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.e06adf339b05c54f.js`](./nordic.atlas-nodes.0033.e06adf339b05c54f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.51896a700166b81c.js`](./nordic.atlas-nodes.0034.51896a700166b81c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.7c7a8bde35b17a81.js`](./nordic.atlas-nodes.0035.7c7a8bde35b17a81.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.18d063b9001222f7.js`](./nordic.atlas-nodes.0036.18d063b9001222f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.f07a4510cb51248b.js`](./nordic.atlas-nodes.0037.f07a4510cb51248b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.4add75f0caee1206.js`](./nordic.atlas-nodes.0038.4add75f0caee1206.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.118eb6854721f99d.js`](./nordic.atlas-nodes.0039.118eb6854721f99d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.73fedda23f76c8f7.js`](./nordic.atlas-nodes.0040.73fedda23f76c8f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.b4b397064e7e0048.js`](./nordic.atlas-nodes.0041.b4b397064e7e0048.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.5c6f7d14ffcb3659.js`](./nordic.atlas-nodes.0042.5c6f7d14ffcb3659.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.1ad331413d9a6a1e.js`](./nordic.atlas-nodes.0043.1ad331413d9a6a1e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.9a633b6c6e8caa4e.js`](./nordic.atlas-nodes.0044.9a633b6c6e8caa4e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.004ba4a7de24490e.js`](./nordic.atlas-nodes.0045.004ba4a7de24490e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.c1b0f8f62a191654.js`](./nordic.atlas-nodes.0046.c1b0f8f62a191654.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.e5e7498c23a225d5.js`](./nordic.atlas-nodes.0047.e5e7498c23a225d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.cefe0870abd02b09.js`](./nordic.atlas-nodes.0048.cefe0870abd02b09.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.8ab0145140f7dc3a.js`](./nordic.atlas-nodes.0049.8ab0145140f7dc3a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.1d0767087f962f24.js`](./nordic.atlas-nodes.0050.1d0767087f962f24.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.9e08599b12376f7c.js`](./nordic.atlas-nodes.0051.9e08599b12376f7c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.683eef7a9414a631.js`](./nordic.atlas-nodes.0052.683eef7a9414a631.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.76578f3ed4c8678b.js`](./nordic.atlas-nodes.0053.76578f3ed4c8678b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.b3c4c51df6377bff.js`](./nordic.atlas-nodes.0054.b3c4c51df6377bff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.d949350d30de7d39.js`](./nordic.atlas-nodes.0055.d949350d30de7d39.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.3f8efb6b047f1289.js`](./nordic.atlas-nodes.0056.3f8efb6b047f1289.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.906664f09746607d.js`](./nordic.atlas-nodes.0057.906664f09746607d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.81cb361a7cb51d22.js`](./nordic.atlas-nodes.0058.81cb361a7cb51d22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.b1329308c3766377.js`](./nordic.atlas-nodes.0059.b1329308c3766377.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.71af5bef7abf4e50.js`](./nordic.atlas-nodes.0060.71af5bef7abf4e50.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.e9fb3bf3c95bbd29.js`](./nordic.atlas-nodes.0061.e9fb3bf3c95bbd29.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.bff58bd58626d3fa.js`](./nordic.atlas-nodes.0062.bff58bd58626d3fa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.f7388ce25de4b741.js`](./nordic.atlas-nodes.0063.f7388ce25de4b741.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.a7c022805f289601.js`](./nordic.atlas-nodes.0064.a7c022805f289601.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.2c9ad420d441b38f.js`](./nordic.atlas-nodes.0065.2c9ad420d441b38f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.99cf566912f697df.js`](./nordic.atlas-nodes.0066.99cf566912f697df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.c723dae89de10a36.js`](./nordic.atlas-nodes.0067.c723dae89de10a36.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.e83340391c605ecd.js`](./nordic.atlas-nodes.0068.e83340391c605ecd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.f616f42aa5b101c3.js`](./nordic.atlas-nodes.0069.f616f42aa5b101c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.79d8b749d5984ed3.js`](./nordic.atlas-nodes.0070.79d8b749d5984ed3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.0820d92ada5dc032.js`](./nordic.atlas-nodes.0071.0820d92ada5dc032.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.8148a50b67a1a570.js`](./nordic.atlas-nodes.0072.8148a50b67a1a570.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.58c7936090041069.js`](./nordic.atlas-nodes.0073.58c7936090041069.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.bffe6989df9ab409.js`](./nordic.atlas-nodes.0074.bffe6989df9ab409.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.361513222c7a0236.js`](./nordic.atlas-nodes.0075.361513222c7a0236.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.f7e5eace9fe99133.js`](./nordic.atlas-nodes.0076.f7e5eace9fe99133.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.2642e1eafd256aa5.js`](./nordic.atlas-nodes.0077.2642e1eafd256aa5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.f9f907f1b8686d44.js`](./nordic.atlas-nodes.0078.f9f907f1b8686d44.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.59e7572beaaf7aa6.js`](./nordic.atlas-nodes.0079.59e7572beaaf7aa6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.3e259a77d16103a5.js`](./nordic.atlas-nodes.0080.3e259a77d16103a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.0dc4a29e9f3ced64.js`](./nordic.atlas-nodes.0081.0dc4a29e9f3ced64.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.21017cd94c61ced5.js`](./nordic.atlas-nodes.0082.21017cd94c61ced5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.b223418f6a19e87d.js`](./nordic.atlas-nodes.0083.b223418f6a19e87d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.67e7b33a3ea8aa92.js`](./nordic.atlas-nodes.0084.67e7b33a3ea8aa92.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.aed5f11a40916270.js`](./nordic.atlas-nodes.0085.aed5f11a40916270.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.a649b2d5964fbfb9.js`](./nordic.atlas-nodes.0086.a649b2d5964fbfb9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.fcd6ebc56165b38b.js`](./nordic.atlas-nodes.0087.fcd6ebc56165b38b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.c0720748e098f31a.js`](./nordic.atlas-nodes.0088.c0720748e098f31a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.31c30ef4f139851e.js`](./nordic.atlas-nodes.0089.31c30ef4f139851e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.27138aa9be521162.js`](./nordic.atlas-nodes.0090.27138aa9be521162.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.2b5628cf2003df53.js`](./nordic.atlas-nodes.0091.2b5628cf2003df53.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.189d9c478014b096.js`](./nordic.atlas-nodes.0092.189d9c478014b096.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.c947422e62636d30.js`](./nordic.atlas-nodes.0093.c947422e62636d30.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.798d6601bf646b4a.js`](./nordic.atlas-nodes.0094.798d6601bf646b4a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.c6930ab4f4b706ee.js`](./nordic.atlas-nodes.0095.c6930ab4f4b706ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.50dcadf2b7e23ffa.js`](./nordic.atlas-nodes.0096.50dcadf2b7e23ffa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.2a14ebe447c02fed.js`](./nordic.atlas-nodes.0097.2a14ebe447c02fed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.3ee3718ae38a92c5.js`](./nordic.atlas-nodes.0098.3ee3718ae38a92c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.92c042ea85c52117.js`](./nordic.atlas-nodes.0099.92c042ea85c52117.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.b75b911f9528b875.js`](./nordic.atlas-nodes.0100.b75b911f9528b875.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.a5911dbb1234fa6e.js`](./nordic.atlas-nodes.0101.a5911dbb1234fa6e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.44a3b01c693111e5.js`](./nordic.atlas-nodes.0102.44a3b01c693111e5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.683d3d3b6b8d9ea3.js`](./nordic.atlas-nodes.0103.683d3d3b6b8d9ea3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.364cff380811d3b1.js`](./nordic.atlas-nodes.0104.364cff380811d3b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.bab9535abedab2a1.js`](./nordic.atlas-nodes.0105.bab9535abedab2a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.09f9538b3fe6524c.js`](./nordic.atlas-nodes.0106.09f9538b3fe6524c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.b02508bf6b64ae68.js`](./nordic.atlas-nodes.0107.b02508bf6b64ae68.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.568c4d6c2eb9ac6f.js`](./nordic.atlas-nodes.0108.568c4d6c2eb9ac6f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.36f625368c7c9fbd.js`](./nordic.atlas-nodes.0109.36f625368c7c9fbd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.5564e487dc71f275.js`](./nordic.atlas-nodes.0110.5564e487dc71f275.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.11efd5b8b90e7c90.js`](./nordic.atlas-nodes.0111.11efd5b8b90e7c90.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.f7ccf625639dcd0d.js`](./nordic.atlas-nodes.0112.f7ccf625639dcd0d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.6f6a61655424e95a.js`](./nordic.atlas-nodes.0113.6f6a61655424e95a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.d23dfc044e6b827d.js`](./nordic.atlas-nodes.0114.d23dfc044e6b827d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.e3252413301e6934.js`](./nordic.atlas-nodes.0115.e3252413301e6934.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.d05fc82a2e7778c8.js`](./nordic.atlas-nodes.0116.d05fc82a2e7778c8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.f6070e09d7e09e74.js`](./nordic.atlas-nodes.0117.f6070e09d7e09e74.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.5fe767bfeb2afb6b.js`](./nordic.atlas-nodes.0118.5fe767bfeb2afb6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.459f1c9188b76aa7.js`](./nordic.atlas-nodes.0119.459f1c9188b76aa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.efe61790c95926e5.js`](./nordic.atlas-nodes.0120.efe61790c95926e5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.41528655f9f938d6.js`](./nordic.atlas-nodes.0121.41528655f9f938d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.bd9f8a04076d943d.js`](./nordic.atlas-nodes.0122.bd9f8a04076d943d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.33a495b09f60ec14.js`](./nordic.atlas-nodes.0123.33a495b09f60ec14.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.2f7980beb70a0ad0.js`](./nordic.atlas-nodes.0124.2f7980beb70a0ad0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.42372abbffc58b22.js`](./nordic.atlas-nodes.0125.42372abbffc58b22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.d5b7e5b388d2f2ae.js`](./nordic.atlas-nodes.0126.d5b7e5b388d2f2ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.2fdd062910e180ee.js`](./nordic.atlas-nodes.0127.2fdd062910e180ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.17220b79c679383d.js`](./nordic.atlas-nodes.0128.17220b79c679383d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.3f4c199871bd04b7.js`](./nordic.atlas-nodes.0129.3f4c199871bd04b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.a80169f4ff0fad71.js`](./nordic.atlas-nodes.0130.a80169f4ff0fad71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.4777a99f4185b9e6.js`](./nordic.atlas-nodes.0131.4777a99f4185b9e6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.a2b977b2d064625d.js`](./nordic.atlas-nodes.0132.a2b977b2d064625d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.364bf92f51974625.js`](./nordic.atlas-nodes.0133.364bf92f51974625.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.da7820c2e45f0d32.js`](./nordic.atlas-nodes.0134.da7820c2e45f0d32.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.fdae7e02f1ec2b7b.js`](./nordic.atlas-nodes.0135.fdae7e02f1ec2b7b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.db1ebcf584a23148.js`](./nordic.atlas-nodes.0136.db1ebcf584a23148.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.38efcab4267544ae.js`](./nordic.atlas-nodes.0137.38efcab4267544ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.7250a790bfb0dd6a.js`](./nordic.atlas-nodes.0138.7250a790bfb0dd6a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.edb4b505d66888b0.js`](./nordic.atlas-nodes.0139.edb4b505d66888b0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.fbfe90f17092bcd2.js`](./nordic.atlas-nodes.0140.fbfe90f17092bcd2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.18d9b57631a0a7a9.js`](./nordic.atlas-nodes.0141.18d9b57631a0a7a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.e696613655d9b25a.js`](./nordic.atlas-nodes.0142.e696613655d9b25a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.e37283cc2988dd4b.js`](./nordic.atlas-nodes.0143.e37283cc2988dd4b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.f7db488caacb4e2b.js`](./nordic.atlas-nodes.0144.f7db488caacb4e2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.8b445872ec7562ed.js`](./nordic.atlas-nodes.0145.8b445872ec7562ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.a9dd12d03932ebef.js`](./nordic.atlas-nodes.0146.a9dd12d03932ebef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.c703853aed4bad21.js`](./nordic.atlas-nodes.0147.c703853aed4bad21.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.80817e8e941f0fbe.js`](./nordic.atlas-nodes.0148.80817e8e941f0fbe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.09d988b553abca85.js`](./nordic.atlas-nodes.0149.09d988b553abca85.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.9e605fc5826e6a6d.js`](./nordic.atlas-nodes.0150.9e605fc5826e6a6d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.9f40de3bf2a58885.js`](./nordic.atlas-nodes.0151.9f40de3bf2a58885.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.7dccab3abd280874.js`](./nordic.atlas-nodes.0152.7dccab3abd280874.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.42a07bf666e9fc5e.js`](./nordic.atlas-nodes.0153.42a07bf666e9fc5e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.656da4d5ccb8108b.js`](./nordic.atlas-nodes.0154.656da4d5ccb8108b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.658c125eec596fcf.js`](./nordic.atlas-nodes.0155.658c125eec596fcf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.776f187ab0f14b96.js`](./nordic.atlas-nodes.0156.776f187ab0f14b96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.acc587c87aced202.js`](./nordic.atlas-nodes.0157.acc587c87aced202.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.731979558d378f70.js`](./nordic.atlas-nodes.0158.731979558d378f70.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.1ae2828ac54c35c8.js`](./nordic.atlas-nodes.0159.1ae2828ac54c35c8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.8dfff1b7ab49ac78.js`](./nordic.atlas-nodes.0160.8dfff1b7ab49ac78.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.a4b9811e2ab702d3.js`](./nordic.atlas-nodes.0161.a4b9811e2ab702d3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.9f409769a43d2da9.js`](./nordic.atlas-nodes.0162.9f409769a43d2da9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.3d73e21f6545790a.js`](./nordic.atlas-nodes.0163.3d73e21f6545790a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.020a153dfe3c8cd6.js`](./nordic.atlas-nodes.0164.020a153dfe3c8cd6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.9c0a461865278265.js`](./nordic.atlas-nodes.0165.9c0a461865278265.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.4d78c9090658b911.js`](./nordic.atlas-nodes.0166.4d78c9090658b911.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.c860ab2cdf1aa171.js`](./nordic.atlas-nodes.0167.c860ab2cdf1aa171.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.0a9d84679bcfbdf4.js`](./nordic.atlas-nodes.0168.0a9d84679bcfbdf4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.ab1a81e3b1240ba9.js`](./nordic.atlas-nodes.0169.ab1a81e3b1240ba9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.caa02c756d3b0bed.js`](./nordic.atlas-nodes.0170.caa02c756d3b0bed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0171.fff887249267b6f8.js`](./nordic.atlas-nodes.0171.fff887249267b6f8.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.97c86febb6501714.js`](./nordic.atlas-details.0172.97c86febb6501714.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.86f85310fecb8eec.js`](./nordic.atlas-details.0173.86f85310fecb8eec.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.20ad735bf9b49dae.js`](./nordic.atlas-details.0174.20ad735bf9b49dae.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.44c20417f1b05c0c.js`](./nordic.atlas-details.0175.44c20417f1b05c0c.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.4d1623bdf6a01bb3.js`](./nordic.atlas-details.0176.4d1623bdf6a01bb3.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.14dcb2ca1eb9222b.js`](./nordic.atlas-details.0177.14dcb2ca1eb9222b.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.1b817a6c51e51cb7.js`](./nordic.atlas-details.0178.1b817a6c51e51cb7.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.6b4d1870867d7d34.js`](./nordic.atlas-details.0179.6b4d1870867d7d34.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.ade11676906e2fe6.js`](./nordic.atlas-details.0180.ade11676906e2fe6.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.ffb9d05af140072f.js`](./nordic.atlas-details.0181.ffb9d05af140072f.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.369be31763e9e1b4.js`](./nordic.atlas-details.0182.369be31763e9e1b4.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.71fcdeb271e4c492.js`](./nordic.atlas-details.0183.71fcdeb271e4c492.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.a1d7f50705fcd8e0.js`](./nordic.atlas-details.0184.a1d7f50705fcd8e0.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.76044edefb2ffd10.js`](./nordic.atlas-details.0185.76044edefb2ffd10.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.2648e7d840f58c75.js`](./nordic.atlas-details.0186.2648e7d840f58c75.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.1bc8811ae3ce6b6e.js`](./nordic.atlas-details.0187.1bc8811ae3ce6b6e.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.b80a815d58b6d9a3.js`](./nordic.atlas-details.0188.b80a815d58b6d9a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.94e20fec0179b4c6.js`](./nordic.atlas-details.0189.94e20fec0179b4c6.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.9a27e9f70ebe461e.js`](./nordic.atlas-details.0190.9a27e9f70ebe461e.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.7b1276544ab596b1.js`](./nordic.atlas-details.0191.7b1276544ab596b1.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.feb2c0db891b8aba.js`](./nordic.atlas-details.0192.feb2c0db891b8aba.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.a373051eee10463a.js`](./nordic.atlas-details.0193.a373051eee10463a.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.1ccbf98eb1a05724.js`](./nordic.atlas-details.0194.1ccbf98eb1a05724.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.dd72f0b246e71116.js`](./nordic.atlas-details.0195.dd72f0b246e71116.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.f59742d82b688ec6.js`](./nordic.atlas-details.0196.f59742d82b688ec6.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.451a1a353f49ae8e.js`](./nordic.atlas-details.0197.451a1a353f49ae8e.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.cba9fde2f6331972.js`](./nordic.atlas-details.0198.cba9fde2f6331972.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.07bc297dacd9ab68.js`](./nordic.atlas-details.0199.07bc297dacd9ab68.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.0ff506027a12a486.js`](./nordic.atlas-details.0200.0ff506027a12a486.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.5ab9a2aa9e574ce8.js`](./nordic.atlas-details.0201.5ab9a2aa9e574ce8.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.172be45924666375.js`](./nordic.atlas-details.0202.172be45924666375.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.3978ec38fef5cb1e.js`](./nordic.atlas-details.0203.3978ec38fef5cb1e.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.6ab4e401c2b48e8e.js`](./nordic.atlas-details.0204.6ab4e401c2b48e8e.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.db80cae1665c6b45.js`](./nordic.atlas-details.0205.db80cae1665c6b45.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.0678ac25c408b749.js`](./nordic.atlas-details.0206.0678ac25c408b749.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.28fea8bf746ddb59.js`](./nordic.atlas-details.0207.28fea8bf746ddb59.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.732ba6f6873fe677.js`](./nordic.atlas-details.0208.732ba6f6873fe677.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.0a214b6257dcb7a1.js`](./nordic.atlas-details.0209.0a214b6257dcb7a1.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.210e37d06ea61546.js`](./nordic.atlas-details.0210.210e37d06ea61546.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.d7af5fbc3d2fb151.js`](./nordic.atlas-details.0211.d7af5fbc3d2fb151.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.8496f34f89ee2a7d.js`](./nordic.atlas-details.0212.8496f34f89ee2a7d.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.31680325de76ef15.js`](./nordic.atlas-details.0213.31680325de76ef15.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.955884be10da47cf.js`](./nordic.atlas-details.0214.955884be10da47cf.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.ad9fb426561668c0.js`](./nordic.atlas-details.0215.ad9fb426561668c0.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.bacb4559787f47c4.js`](./nordic.atlas-details.0216.bacb4559787f47c4.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.cfaa2f097d18ce05.js`](./nordic.atlas-details.0217.cfaa2f097d18ce05.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.ea32a16ff012a8c0.js`](./nordic.atlas-details.0218.ea32a16ff012a8c0.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.21ed279b10566024.js`](./nordic.atlas-details.0219.21ed279b10566024.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.71791918ff523cf8.js`](./nordic.atlas-details.0220.71791918ff523cf8.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.c61e212a95d20f29.js`](./nordic.atlas-details.0221.c61e212a95d20f29.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.2cb73ca26a1fd5f7.js`](./nordic.atlas-details.0222.2cb73ca26a1fd5f7.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.c5459f9c920d099a.js`](./nordic.atlas-details.0223.c5459f9c920d099a.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.1660e90f0a8c9722.js`](./nordic.atlas-details.0224.1660e90f0a8c9722.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.8eaedccbfea4e586.js`](./nordic.atlas-details.0225.8eaedccbfea4e586.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.5717f36cb7f340a6.js`](./nordic.atlas-details.0226.5717f36cb7f340a6.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.f352364ebed72731.js`](./nordic.atlas-details.0227.f352364ebed72731.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.eaab353fdceccf4b.js`](./nordic.atlas-details.0228.eaab353fdceccf4b.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.8d4759253e410fa2.js`](./nordic.atlas-details.0229.8d4759253e410fa2.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.cac8b27dd59ecab2.js`](./nordic.atlas-details.0230.cac8b27dd59ecab2.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.3da7049a41be69eb.js`](./nordic.atlas-details.0231.3da7049a41be69eb.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.c7b7cf86d703c26b.js`](./nordic.atlas-details.0232.c7b7cf86d703c26b.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.df0cae13d0b98c47.js`](./nordic.atlas-details.0233.df0cae13d0b98c47.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.65ceae02b89ad449.js`](./nordic.atlas-details.0234.65ceae02b89ad449.js)
- Static atlas data chunk: [`nordic.atlas-details.0235.e146ff4c0b798098.js`](./nordic.atlas-details.0235.e146ff4c0b798098.js)
- Static atlas data chunk: [`nordic.atlas-edges.0236.7bff90a3b29984e9.js`](./nordic.atlas-edges.0236.7bff90a3b29984e9.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0237.4bd3fe662962e801.js`](./nordic.atlas-sequences.0237.4bd3fe662962e801.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0238.41035b9d6913a934.js`](./nordic.atlas-indexes.0238.41035b9d6913a934.js)
- Animal source-sample chronology accountability: [`nordic_animal_sample_chronology_context.json`](./nordic_animal_sample_chronology_context.json)
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
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `3` |
| Cat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Sheep source-sample chronology | `shared_world_scale_layer` |  | `4` |
| Pig source-sample chronology | `shared_world_scale_layer` |  | `2` |
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


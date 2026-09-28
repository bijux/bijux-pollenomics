# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-28` from Homo
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
- RAÄ atlas input status: [`raa_atlas_input_status.json`](./raa_atlas_input_status.json)
- RAÄ archaeology density: [`sweden_archaeology_density.geojson`](./sweden_archaeology_density.geojson)
- Animal locality GeoJSON: [`nordic_animal_localities.geojson`](./nordic_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`nordic_domesticated_animal_localities.geojson`](./nordic_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`nordic_comparator_animal_localities.geojson`](./nordic_comparator_animal_localities.geojson)
- Wild and progenitor animal locality GeoJSON: [`nordic_progenitor_animal_localities.geojson`](./nordic_progenitor_animal_localities.geojson)
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.f6f150288d8723f5.js`](./nordic.atlas-provenance.0000.f6f150288d8723f5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.7916c24096a434c9.js`](./nordic.atlas-nodes.0001.7916c24096a434c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.aae575c2dc33aa44.js`](./nordic.atlas-nodes.0002.aae575c2dc33aa44.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.3deda9e333956b80.js`](./nordic.atlas-nodes.0003.3deda9e333956b80.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.ea2fc7c212ca8e38.js`](./nordic.atlas-nodes.0004.ea2fc7c212ca8e38.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.f7a528eb0ac288fc.js`](./nordic.atlas-nodes.0005.f7a528eb0ac288fc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.caf41f6aef62d1ec.js`](./nordic.atlas-nodes.0006.caf41f6aef62d1ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.79392d1ea1644550.js`](./nordic.atlas-nodes.0007.79392d1ea1644550.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.eed3933cc1042677.js`](./nordic.atlas-nodes.0008.eed3933cc1042677.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.cfa6bc93428ff280.js`](./nordic.atlas-nodes.0009.cfa6bc93428ff280.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.2350e8658aee644b.js`](./nordic.atlas-nodes.0010.2350e8658aee644b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.41a993c532b3cc8c.js`](./nordic.atlas-nodes.0011.41a993c532b3cc8c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.5eef893b91a62c94.js`](./nordic.atlas-nodes.0012.5eef893b91a62c94.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.a14b784f23f101cb.js`](./nordic.atlas-nodes.0013.a14b784f23f101cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.67132ee5b69a6cff.js`](./nordic.atlas-nodes.0014.67132ee5b69a6cff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.ffd2f0e074dab3b5.js`](./nordic.atlas-nodes.0015.ffd2f0e074dab3b5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.33dbced6cf555edd.js`](./nordic.atlas-nodes.0016.33dbced6cf555edd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.6fb442c1b8bc9860.js`](./nordic.atlas-nodes.0017.6fb442c1b8bc9860.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.8e818dd740f79c88.js`](./nordic.atlas-nodes.0018.8e818dd740f79c88.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.867873c751671d8d.js`](./nordic.atlas-nodes.0019.867873c751671d8d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.84439454ef7f6169.js`](./nordic.atlas-nodes.0020.84439454ef7f6169.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.a9fa120de1f935fa.js`](./nordic.atlas-nodes.0021.a9fa120de1f935fa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.cad556b82eef071e.js`](./nordic.atlas-nodes.0022.cad556b82eef071e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.c620f95021a37158.js`](./nordic.atlas-nodes.0023.c620f95021a37158.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.4f62e7afd3460c02.js`](./nordic.atlas-nodes.0024.4f62e7afd3460c02.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.68f6ee6165f1e658.js`](./nordic.atlas-nodes.0025.68f6ee6165f1e658.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.bdc666177655a21c.js`](./nordic.atlas-nodes.0026.bdc666177655a21c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.47f56c8374e6f205.js`](./nordic.atlas-nodes.0027.47f56c8374e6f205.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.70db4b8074b3ef9e.js`](./nordic.atlas-nodes.0028.70db4b8074b3ef9e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.f4e964a93ac8c973.js`](./nordic.atlas-nodes.0029.f4e964a93ac8c973.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.a11e8ea0e646ff12.js`](./nordic.atlas-nodes.0030.a11e8ea0e646ff12.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.66d9d1dec8b7c307.js`](./nordic.atlas-nodes.0031.66d9d1dec8b7c307.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.05f2c24c6c391dc3.js`](./nordic.atlas-nodes.0032.05f2c24c6c391dc3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.5a68187de6d705ce.js`](./nordic.atlas-nodes.0033.5a68187de6d705ce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.f592757e11c26636.js`](./nordic.atlas-nodes.0034.f592757e11c26636.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.d06ad19d03e641b1.js`](./nordic.atlas-nodes.0035.d06ad19d03e641b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.6cdc57c65aa9df73.js`](./nordic.atlas-nodes.0036.6cdc57c65aa9df73.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.5c4b094471bb3652.js`](./nordic.atlas-nodes.0037.5c4b094471bb3652.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.6aee45b75a6aed27.js`](./nordic.atlas-nodes.0038.6aee45b75a6aed27.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.8d36e731869e90d1.js`](./nordic.atlas-nodes.0039.8d36e731869e90d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.6c41952db112a778.js`](./nordic.atlas-nodes.0040.6c41952db112a778.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.49aeebd81bb37e95.js`](./nordic.atlas-nodes.0041.49aeebd81bb37e95.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.58ec05d0f4bf9241.js`](./nordic.atlas-nodes.0042.58ec05d0f4bf9241.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.e6f16b42b3045806.js`](./nordic.atlas-nodes.0043.e6f16b42b3045806.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.b61087c4c46c8600.js`](./nordic.atlas-nodes.0044.b61087c4c46c8600.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.5165dbcb063fa5ca.js`](./nordic.atlas-nodes.0045.5165dbcb063fa5ca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.d195e3299cc43f51.js`](./nordic.atlas-nodes.0046.d195e3299cc43f51.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.f03e18f57e4cd130.js`](./nordic.atlas-nodes.0047.f03e18f57e4cd130.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.0805097d266ad5e9.js`](./nordic.atlas-nodes.0048.0805097d266ad5e9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.b00c81a797c05793.js`](./nordic.atlas-nodes.0049.b00c81a797c05793.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.b421f9ab09b99fa6.js`](./nordic.atlas-nodes.0050.b421f9ab09b99fa6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.aaa3c1271b9504cd.js`](./nordic.atlas-nodes.0051.aaa3c1271b9504cd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.1b821948008659bc.js`](./nordic.atlas-nodes.0052.1b821948008659bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.2c7e253da6a5b907.js`](./nordic.atlas-nodes.0053.2c7e253da6a5b907.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.81a77610c0adc47c.js`](./nordic.atlas-nodes.0054.81a77610c0adc47c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.28932d9fc592b2bc.js`](./nordic.atlas-nodes.0055.28932d9fc592b2bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.513ed673fd053b61.js`](./nordic.atlas-nodes.0056.513ed673fd053b61.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.bb8b0790f0357420.js`](./nordic.atlas-nodes.0057.bb8b0790f0357420.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.f8e5ae7cf15aab66.js`](./nordic.atlas-nodes.0058.f8e5ae7cf15aab66.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.e9d2d9d345c5197d.js`](./nordic.atlas-nodes.0059.e9d2d9d345c5197d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.7518c7cbc6761736.js`](./nordic.atlas-nodes.0060.7518c7cbc6761736.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.a35bf9d2579d3100.js`](./nordic.atlas-nodes.0061.a35bf9d2579d3100.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.325f53dbf448bd31.js`](./nordic.atlas-nodes.0062.325f53dbf448bd31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.3467fb4b1cab489d.js`](./nordic.atlas-nodes.0063.3467fb4b1cab489d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.ad2230000deb84a5.js`](./nordic.atlas-nodes.0064.ad2230000deb84a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.781692a408c6d8ff.js`](./nordic.atlas-nodes.0065.781692a408c6d8ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.93197011b11a6293.js`](./nordic.atlas-nodes.0066.93197011b11a6293.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.8287115dfa32d720.js`](./nordic.atlas-nodes.0067.8287115dfa32d720.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.2f5a15e944db5707.js`](./nordic.atlas-nodes.0068.2f5a15e944db5707.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.4ca1321811fcadfa.js`](./nordic.atlas-nodes.0069.4ca1321811fcadfa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.29ae65112895b1fb.js`](./nordic.atlas-nodes.0070.29ae65112895b1fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.e01e8f653ba15960.js`](./nordic.atlas-nodes.0071.e01e8f653ba15960.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.b6dfa494830575da.js`](./nordic.atlas-nodes.0072.b6dfa494830575da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.882beff74e9c57d5.js`](./nordic.atlas-nodes.0073.882beff74e9c57d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.2e79d44039accf2f.js`](./nordic.atlas-nodes.0074.2e79d44039accf2f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.043be0673d5189d2.js`](./nordic.atlas-nodes.0075.043be0673d5189d2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.a06268dbb8a76f86.js`](./nordic.atlas-nodes.0076.a06268dbb8a76f86.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.1ce2254345e764f4.js`](./nordic.atlas-nodes.0077.1ce2254345e764f4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.8efdc4803fff8713.js`](./nordic.atlas-nodes.0078.8efdc4803fff8713.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.ba226809a00777b7.js`](./nordic.atlas-nodes.0079.ba226809a00777b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.d45df9f3ecd4fc2f.js`](./nordic.atlas-nodes.0080.d45df9f3ecd4fc2f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.d896339de57fabc8.js`](./nordic.atlas-nodes.0081.d896339de57fabc8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.b22fe3e2f14464a2.js`](./nordic.atlas-nodes.0082.b22fe3e2f14464a2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.322f77ddcd9309ff.js`](./nordic.atlas-nodes.0083.322f77ddcd9309ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.c4e6005537885f10.js`](./nordic.atlas-nodes.0084.c4e6005537885f10.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.221c626bab0cd417.js`](./nordic.atlas-nodes.0085.221c626bab0cd417.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.2330b2248097242f.js`](./nordic.atlas-nodes.0086.2330b2248097242f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.160612280691671f.js`](./nordic.atlas-nodes.0087.160612280691671f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.bfa6531ae837a1d5.js`](./nordic.atlas-nodes.0088.bfa6531ae837a1d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.de28752ba2e9e976.js`](./nordic.atlas-nodes.0089.de28752ba2e9e976.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.e750c6ef021c585f.js`](./nordic.atlas-nodes.0090.e750c6ef021c585f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.495812d7cb6a35a8.js`](./nordic.atlas-nodes.0091.495812d7cb6a35a8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.2952ceaa2d436c5d.js`](./nordic.atlas-nodes.0092.2952ceaa2d436c5d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.5da41158cf95fb9f.js`](./nordic.atlas-nodes.0093.5da41158cf95fb9f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.6711e62e27f579e2.js`](./nordic.atlas-nodes.0094.6711e62e27f579e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.3ffa3e1fd6c67276.js`](./nordic.atlas-nodes.0095.3ffa3e1fd6c67276.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.c76d3334f415712e.js`](./nordic.atlas-nodes.0096.c76d3334f415712e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.d28bd8e990b8b535.js`](./nordic.atlas-nodes.0097.d28bd8e990b8b535.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.5fdacbe501166761.js`](./nordic.atlas-nodes.0098.5fdacbe501166761.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.ca649457a39805cc.js`](./nordic.atlas-nodes.0099.ca649457a39805cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.84443b0eecfde5d6.js`](./nordic.atlas-nodes.0100.84443b0eecfde5d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.b2790a49006042a6.js`](./nordic.atlas-nodes.0101.b2790a49006042a6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.53c4200112725859.js`](./nordic.atlas-nodes.0102.53c4200112725859.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.c80bd4da66db9ada.js`](./nordic.atlas-nodes.0103.c80bd4da66db9ada.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.2154ee3a9dbe9ce0.js`](./nordic.atlas-nodes.0104.2154ee3a9dbe9ce0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.40b3ef6c1ecaa43e.js`](./nordic.atlas-nodes.0105.40b3ef6c1ecaa43e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.107ad23b61f017eb.js`](./nordic.atlas-nodes.0106.107ad23b61f017eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.9019d3e817585c97.js`](./nordic.atlas-nodes.0107.9019d3e817585c97.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.aef16edded2226c9.js`](./nordic.atlas-nodes.0108.aef16edded2226c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.8dc65ea305cb5b4c.js`](./nordic.atlas-nodes.0109.8dc65ea305cb5b4c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.7d7416493dee60c1.js`](./nordic.atlas-nodes.0110.7d7416493dee60c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.3048ce3488e42eaf.js`](./nordic.atlas-nodes.0111.3048ce3488e42eaf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.fc973407cf57c441.js`](./nordic.atlas-nodes.0112.fc973407cf57c441.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.de01ab82ac135b4d.js`](./nordic.atlas-nodes.0113.de01ab82ac135b4d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.b442726fe005d2fb.js`](./nordic.atlas-nodes.0114.b442726fe005d2fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.04bf8369b8837028.js`](./nordic.atlas-nodes.0115.04bf8369b8837028.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.868bf8c5605e7988.js`](./nordic.atlas-nodes.0116.868bf8c5605e7988.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.873a0163d3a755c8.js`](./nordic.atlas-nodes.0117.873a0163d3a755c8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.091b445e1e696eed.js`](./nordic.atlas-nodes.0118.091b445e1e696eed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.355658a92fe5f9e8.js`](./nordic.atlas-nodes.0119.355658a92fe5f9e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.8ab62f9c03efac17.js`](./nordic.atlas-nodes.0120.8ab62f9c03efac17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.473aab9ebd9f9626.js`](./nordic.atlas-nodes.0121.473aab9ebd9f9626.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.53fc21ae7fbb8b67.js`](./nordic.atlas-nodes.0122.53fc21ae7fbb8b67.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.c97a5299d5375bfb.js`](./nordic.atlas-nodes.0123.c97a5299d5375bfb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.1e0a49739e57d260.js`](./nordic.atlas-nodes.0124.1e0a49739e57d260.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.01cf42845c69daf7.js`](./nordic.atlas-nodes.0125.01cf42845c69daf7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.119399d8c8871a24.js`](./nordic.atlas-nodes.0126.119399d8c8871a24.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.fe29934b53434850.js`](./nordic.atlas-nodes.0127.fe29934b53434850.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.89603aa4d105973f.js`](./nordic.atlas-nodes.0128.89603aa4d105973f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.5aad159648baa946.js`](./nordic.atlas-nodes.0129.5aad159648baa946.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.502d405e69424994.js`](./nordic.atlas-nodes.0130.502d405e69424994.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.c514c81b926a0894.js`](./nordic.atlas-nodes.0131.c514c81b926a0894.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.5bde15e76c81f7b7.js`](./nordic.atlas-nodes.0132.5bde15e76c81f7b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.e932f295ab4480c5.js`](./nordic.atlas-nodes.0133.e932f295ab4480c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.8f5f5444dd5ffeda.js`](./nordic.atlas-nodes.0134.8f5f5444dd5ffeda.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.04091b6aab178a90.js`](./nordic.atlas-nodes.0135.04091b6aab178a90.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.a6b365dc0b94ad75.js`](./nordic.atlas-nodes.0136.a6b365dc0b94ad75.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.3d49a680d38001ef.js`](./nordic.atlas-nodes.0137.3d49a680d38001ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.e8c987996b4aec09.js`](./nordic.atlas-nodes.0138.e8c987996b4aec09.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.5bc206f9d17f2a7f.js`](./nordic.atlas-nodes.0139.5bc206f9d17f2a7f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.e70ba9441721ec31.js`](./nordic.atlas-nodes.0140.e70ba9441721ec31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.112729a036758ef0.js`](./nordic.atlas-nodes.0141.112729a036758ef0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.57ca63f82ff0ba85.js`](./nordic.atlas-nodes.0142.57ca63f82ff0ba85.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.50079d29b34c3f48.js`](./nordic.atlas-nodes.0143.50079d29b34c3f48.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.ec9cc11b87b15172.js`](./nordic.atlas-nodes.0144.ec9cc11b87b15172.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.0d6ec01769c86bb8.js`](./nordic.atlas-nodes.0145.0d6ec01769c86bb8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.b18ba72ffb7ee662.js`](./nordic.atlas-nodes.0146.b18ba72ffb7ee662.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.99f61a0b2014c07d.js`](./nordic.atlas-nodes.0147.99f61a0b2014c07d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.1cd2817650fd0848.js`](./nordic.atlas-nodes.0148.1cd2817650fd0848.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.576db202b14e5a85.js`](./nordic.atlas-nodes.0149.576db202b14e5a85.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.5fed2053f9443fce.js`](./nordic.atlas-nodes.0150.5fed2053f9443fce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.1dce59c827e390a7.js`](./nordic.atlas-nodes.0151.1dce59c827e390a7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.bd4816dbd87f98f0.js`](./nordic.atlas-nodes.0152.bd4816dbd87f98f0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.ec4b18fc1cbc981d.js`](./nordic.atlas-nodes.0153.ec4b18fc1cbc981d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.29b86c6686e9fbe3.js`](./nordic.atlas-nodes.0154.29b86c6686e9fbe3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.82341402a7d8e3f6.js`](./nordic.atlas-nodes.0155.82341402a7d8e3f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.06e746c5f785e053.js`](./nordic.atlas-nodes.0156.06e746c5f785e053.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.3b4e9e31d67330ee.js`](./nordic.atlas-nodes.0157.3b4e9e31d67330ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.75b1c8a988f8c0df.js`](./nordic.atlas-nodes.0158.75b1c8a988f8c0df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.15a078fe80054456.js`](./nordic.atlas-nodes.0159.15a078fe80054456.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.d3fed0736e0cfc2c.js`](./nordic.atlas-nodes.0160.d3fed0736e0cfc2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.f9cff703e9a4b879.js`](./nordic.atlas-nodes.0161.f9cff703e9a4b879.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.ee3444de5b56bdad.js`](./nordic.atlas-nodes.0162.ee3444de5b56bdad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.4f644c39de1c9600.js`](./nordic.atlas-nodes.0163.4f644c39de1c9600.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.4f42571d837291c4.js`](./nordic.atlas-nodes.0164.4f42571d837291c4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.0e904196a72077fa.js`](./nordic.atlas-nodes.0165.0e904196a72077fa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.fe943a245e8475c2.js`](./nordic.atlas-nodes.0166.fe943a245e8475c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.561b778de86664da.js`](./nordic.atlas-nodes.0167.561b778de86664da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.8dcf296ba33a46a5.js`](./nordic.atlas-nodes.0168.8dcf296ba33a46a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.35ae6100b49cc6de.js`](./nordic.atlas-nodes.0169.35ae6100b49cc6de.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.884277f25d6570d6.js`](./nordic.atlas-nodes.0170.884277f25d6570d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0171.a425a2ec4db8b48f.js`](./nordic.atlas-nodes.0171.a425a2ec4db8b48f.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.5746018efbad0903.js`](./nordic.atlas-details.0172.5746018efbad0903.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.56063eb648ee0bbc.js`](./nordic.atlas-details.0173.56063eb648ee0bbc.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.baf3762436a9b373.js`](./nordic.atlas-details.0174.baf3762436a9b373.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.8b7ef309fecca1bb.js`](./nordic.atlas-details.0175.8b7ef309fecca1bb.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.d2f57bd1b1f13264.js`](./nordic.atlas-details.0176.d2f57bd1b1f13264.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.4e02514c22a835f5.js`](./nordic.atlas-details.0177.4e02514c22a835f5.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.b7435c687cef10c5.js`](./nordic.atlas-details.0178.b7435c687cef10c5.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.3795291e64fd23f4.js`](./nordic.atlas-details.0179.3795291e64fd23f4.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.c18b3f7688c680fb.js`](./nordic.atlas-details.0180.c18b3f7688c680fb.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.0e4781e9a228ac29.js`](./nordic.atlas-details.0181.0e4781e9a228ac29.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.636ec8b3bb508aba.js`](./nordic.atlas-details.0182.636ec8b3bb508aba.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.b30b7f809992ebc8.js`](./nordic.atlas-details.0183.b30b7f809992ebc8.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.a4a8e12c4780ffff.js`](./nordic.atlas-details.0184.a4a8e12c4780ffff.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.6524ad0cc4676c8f.js`](./nordic.atlas-details.0185.6524ad0cc4676c8f.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.6a1dd76773316a51.js`](./nordic.atlas-details.0186.6a1dd76773316a51.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.61b9379467cc24af.js`](./nordic.atlas-details.0187.61b9379467cc24af.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.6f35fb9e0f86f07e.js`](./nordic.atlas-details.0188.6f35fb9e0f86f07e.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.dafd566cd56227db.js`](./nordic.atlas-details.0189.dafd566cd56227db.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.e3ea4c419ccb3150.js`](./nordic.atlas-details.0190.e3ea4c419ccb3150.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.adf159bdbdba35ee.js`](./nordic.atlas-details.0191.adf159bdbdba35ee.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.3bebf7fbad405798.js`](./nordic.atlas-details.0192.3bebf7fbad405798.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.fe68c12688d92566.js`](./nordic.atlas-details.0193.fe68c12688d92566.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.6faa338830bd3889.js`](./nordic.atlas-details.0194.6faa338830bd3889.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.c00974f77aca6e9e.js`](./nordic.atlas-details.0195.c00974f77aca6e9e.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.7a06fce767a098e9.js`](./nordic.atlas-details.0196.7a06fce767a098e9.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.3ba9992f3de1e648.js`](./nordic.atlas-details.0197.3ba9992f3de1e648.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.40fb7b6d13d0d2b7.js`](./nordic.atlas-details.0198.40fb7b6d13d0d2b7.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.e93df647093e95d1.js`](./nordic.atlas-details.0199.e93df647093e95d1.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.90f5f16b5a8a1279.js`](./nordic.atlas-details.0200.90f5f16b5a8a1279.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.9a112968f4373541.js`](./nordic.atlas-details.0201.9a112968f4373541.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.d86f2d4ee516149a.js`](./nordic.atlas-details.0202.d86f2d4ee516149a.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.87a3af06040f827a.js`](./nordic.atlas-details.0203.87a3af06040f827a.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.be3fd485ffcdcab0.js`](./nordic.atlas-details.0204.be3fd485ffcdcab0.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.53b1f1fc6e20afff.js`](./nordic.atlas-details.0205.53b1f1fc6e20afff.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.a1c10426dc071e00.js`](./nordic.atlas-details.0206.a1c10426dc071e00.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.90546888c75cca49.js`](./nordic.atlas-details.0207.90546888c75cca49.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.7bb66b8a01c12af8.js`](./nordic.atlas-details.0208.7bb66b8a01c12af8.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.d5bd30290224539f.js`](./nordic.atlas-details.0209.d5bd30290224539f.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.b3cab512bd9831ee.js`](./nordic.atlas-details.0210.b3cab512bd9831ee.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.4defc4032fd7f728.js`](./nordic.atlas-details.0211.4defc4032fd7f728.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.8299c5ebd1fb5e0b.js`](./nordic.atlas-details.0212.8299c5ebd1fb5e0b.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.f929435e69474de2.js`](./nordic.atlas-details.0213.f929435e69474de2.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.06ed3f175916c540.js`](./nordic.atlas-details.0214.06ed3f175916c540.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.72adbffab78b35a6.js`](./nordic.atlas-details.0215.72adbffab78b35a6.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.f658e1eb4d965f33.js`](./nordic.atlas-details.0216.f658e1eb4d965f33.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.b45bc973e9d36a66.js`](./nordic.atlas-details.0217.b45bc973e9d36a66.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.e6eaf3ff1a853ff9.js`](./nordic.atlas-details.0218.e6eaf3ff1a853ff9.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.73c7a7191a8538bb.js`](./nordic.atlas-details.0219.73c7a7191a8538bb.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.dbc6e251cbc021d0.js`](./nordic.atlas-details.0220.dbc6e251cbc021d0.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.01208d74673441f4.js`](./nordic.atlas-details.0221.01208d74673441f4.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.de35c26c2365b62c.js`](./nordic.atlas-details.0222.de35c26c2365b62c.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.6526d464c6345eb9.js`](./nordic.atlas-details.0223.6526d464c6345eb9.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.d13703b41a126acd.js`](./nordic.atlas-details.0224.d13703b41a126acd.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.00065acc58fc09e8.js`](./nordic.atlas-details.0225.00065acc58fc09e8.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.52f460974a1ccfec.js`](./nordic.atlas-details.0226.52f460974a1ccfec.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.08256f5d4aaeb296.js`](./nordic.atlas-details.0227.08256f5d4aaeb296.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.d13bfbd00fe95188.js`](./nordic.atlas-details.0228.d13bfbd00fe95188.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.016d1f96a1f89c4f.js`](./nordic.atlas-details.0229.016d1f96a1f89c4f.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.b2e974492665d8e6.js`](./nordic.atlas-details.0230.b2e974492665d8e6.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.785e2aaf0a095387.js`](./nordic.atlas-details.0231.785e2aaf0a095387.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.9a75269cbc87df22.js`](./nordic.atlas-details.0232.9a75269cbc87df22.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.9a89e39f9d41ee4a.js`](./nordic.atlas-details.0233.9a89e39f9d41ee4a.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.334940fbc34fba94.js`](./nordic.atlas-details.0234.334940fbc34fba94.js)
- Static atlas data chunk: [`nordic.atlas-details.0235.f699ba0c3b82748c.js`](./nordic.atlas-details.0235.f699ba0c3b82748c.js)
- Static atlas data chunk: [`nordic.atlas-edges.0236.2f9e70523afb0c51.js`](./nordic.atlas-edges.0236.2f9e70523afb0c51.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0237.60d7a82ba8fd0552.js`](./nordic.atlas-sequences.0237.60d7a82ba8fd0552.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0238.7ca898032f71d5c3.js`](./nordic.atlas-indexes.0238.7ca898032f71d5c3.js)
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
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `8799` |
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
| RAÄ archaeology density | `scope_specific_overlay` | Sweden only. Density cells summarize `Fornlämning` counts. | `106` |

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


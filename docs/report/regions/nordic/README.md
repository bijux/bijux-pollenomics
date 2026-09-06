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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.ceec37730dc1cb2f.js`](./nordic.atlas-provenance.0000.ceec37730dc1cb2f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.f0342a76f75486c6.js`](./nordic.atlas-nodes.0001.f0342a76f75486c6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.cece8973b6ae70ce.js`](./nordic.atlas-nodes.0002.cece8973b6ae70ce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.a96f71d187490e63.js`](./nordic.atlas-nodes.0003.a96f71d187490e63.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.2e9752585da7f82c.js`](./nordic.atlas-nodes.0004.2e9752585da7f82c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.4f60ac377a09ef15.js`](./nordic.atlas-nodes.0005.4f60ac377a09ef15.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.44a0dbdd20411f9c.js`](./nordic.atlas-nodes.0006.44a0dbdd20411f9c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.62255e817d071d6a.js`](./nordic.atlas-nodes.0007.62255e817d071d6a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.19d30b19feb00231.js`](./nordic.atlas-nodes.0008.19d30b19feb00231.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.c11550e2c4ea5171.js`](./nordic.atlas-nodes.0009.c11550e2c4ea5171.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.b3905e6f567aefa2.js`](./nordic.atlas-nodes.0010.b3905e6f567aefa2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.eedfa235e966f650.js`](./nordic.atlas-nodes.0011.eedfa235e966f650.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.7993b87775c3c47c.js`](./nordic.atlas-nodes.0012.7993b87775c3c47c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.b572af9aa46be577.js`](./nordic.atlas-nodes.0013.b572af9aa46be577.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.3728f6c1cc4e931b.js`](./nordic.atlas-nodes.0014.3728f6c1cc4e931b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.0434a792ee6ece5d.js`](./nordic.atlas-nodes.0015.0434a792ee6ece5d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.1307c4ceff135a2f.js`](./nordic.atlas-nodes.0016.1307c4ceff135a2f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.4e980e3c6d331cbc.js`](./nordic.atlas-nodes.0017.4e980e3c6d331cbc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.99c0244dae00c784.js`](./nordic.atlas-nodes.0018.99c0244dae00c784.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.ed435c63da253d56.js`](./nordic.atlas-nodes.0019.ed435c63da253d56.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.fcdc4f79786bb018.js`](./nordic.atlas-nodes.0020.fcdc4f79786bb018.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.86f7f410d83c2509.js`](./nordic.atlas-nodes.0021.86f7f410d83c2509.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.6875f483e0634598.js`](./nordic.atlas-nodes.0022.6875f483e0634598.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.5a0d19b2d340a1b1.js`](./nordic.atlas-nodes.0023.5a0d19b2d340a1b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.bbd435086ad10d57.js`](./nordic.atlas-nodes.0024.bbd435086ad10d57.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.f7a6fd585112204d.js`](./nordic.atlas-nodes.0025.f7a6fd585112204d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.18f2d43f81129fce.js`](./nordic.atlas-nodes.0026.18f2d43f81129fce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.1b9c05399f01be29.js`](./nordic.atlas-nodes.0027.1b9c05399f01be29.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.33434fc639b13053.js`](./nordic.atlas-nodes.0028.33434fc639b13053.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.af82a52fac33241b.js`](./nordic.atlas-nodes.0029.af82a52fac33241b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.55d7e6c5974c139d.js`](./nordic.atlas-nodes.0030.55d7e6c5974c139d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.2f21e6b7ff6e18b5.js`](./nordic.atlas-nodes.0031.2f21e6b7ff6e18b5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.d472e1662c557e5b.js`](./nordic.atlas-nodes.0032.d472e1662c557e5b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.29dc0618b91584cc.js`](./nordic.atlas-nodes.0033.29dc0618b91584cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.3130385f9a659a16.js`](./nordic.atlas-nodes.0034.3130385f9a659a16.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.a065c21cc5a7a89b.js`](./nordic.atlas-nodes.0035.a065c21cc5a7a89b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.63af42cf9e1a69ec.js`](./nordic.atlas-nodes.0036.63af42cf9e1a69ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.4705f17f96d9975a.js`](./nordic.atlas-nodes.0037.4705f17f96d9975a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.4fb39e0db40ab1f8.js`](./nordic.atlas-nodes.0038.4fb39e0db40ab1f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.9b921771c4f21569.js`](./nordic.atlas-nodes.0039.9b921771c4f21569.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.53b1360d2358840f.js`](./nordic.atlas-nodes.0040.53b1360d2358840f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.bd45637efb26c629.js`](./nordic.atlas-nodes.0041.bd45637efb26c629.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.db3d2ea7469071ba.js`](./nordic.atlas-nodes.0042.db3d2ea7469071ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.100b859114c70d4b.js`](./nordic.atlas-nodes.0043.100b859114c70d4b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.18d06a09ced27c7a.js`](./nordic.atlas-nodes.0044.18d06a09ced27c7a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.bbbda96033432003.js`](./nordic.atlas-nodes.0045.bbbda96033432003.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.dbd69e5c85859f53.js`](./nordic.atlas-nodes.0046.dbd69e5c85859f53.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.754fee85e01dd3c5.js`](./nordic.atlas-nodes.0047.754fee85e01dd3c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.d8bf6541996c4af9.js`](./nordic.atlas-nodes.0048.d8bf6541996c4af9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.e474d92f937f48c0.js`](./nordic.atlas-nodes.0049.e474d92f937f48c0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.74b7e9bac98e49ff.js`](./nordic.atlas-nodes.0050.74b7e9bac98e49ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.ca6e31d4b8939125.js`](./nordic.atlas-nodes.0051.ca6e31d4b8939125.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.6bfc4b7241357e04.js`](./nordic.atlas-nodes.0052.6bfc4b7241357e04.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.c2b3e1f9c8d94122.js`](./nordic.atlas-nodes.0053.c2b3e1f9c8d94122.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.b796181cd4b223e0.js`](./nordic.atlas-nodes.0054.b796181cd4b223e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.93d72f4da0c0e5f8.js`](./nordic.atlas-nodes.0055.93d72f4da0c0e5f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.43dd8f9f4389fbf1.js`](./nordic.atlas-nodes.0056.43dd8f9f4389fbf1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.7c28404831d68477.js`](./nordic.atlas-nodes.0057.7c28404831d68477.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.7d4bfd8e64448d3f.js`](./nordic.atlas-nodes.0058.7d4bfd8e64448d3f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.d56cfbd32d9f09ed.js`](./nordic.atlas-nodes.0059.d56cfbd32d9f09ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.8919e129535ebbee.js`](./nordic.atlas-nodes.0060.8919e129535ebbee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.5023ea452eb2e907.js`](./nordic.atlas-nodes.0061.5023ea452eb2e907.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.5d965c66ef1fe953.js`](./nordic.atlas-nodes.0062.5d965c66ef1fe953.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.33ecd0ec4c493749.js`](./nordic.atlas-nodes.0063.33ecd0ec4c493749.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.a798fceb1049b498.js`](./nordic.atlas-nodes.0064.a798fceb1049b498.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.5f75ae35a9b961fc.js`](./nordic.atlas-nodes.0065.5f75ae35a9b961fc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.a40880b960f7fb2e.js`](./nordic.atlas-nodes.0066.a40880b960f7fb2e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.8cefcd6f88ce3871.js`](./nordic.atlas-nodes.0067.8cefcd6f88ce3871.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.9f93308b0540e081.js`](./nordic.atlas-nodes.0068.9f93308b0540e081.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.55a77b6d4f7d23b9.js`](./nordic.atlas-nodes.0069.55a77b6d4f7d23b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.6b98bd30d335c398.js`](./nordic.atlas-nodes.0070.6b98bd30d335c398.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.52a85fef116cef9b.js`](./nordic.atlas-nodes.0071.52a85fef116cef9b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.558952f10d263f10.js`](./nordic.atlas-nodes.0072.558952f10d263f10.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.a5c229c4989edc0e.js`](./nordic.atlas-nodes.0073.a5c229c4989edc0e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.48f0fb5b0e266b75.js`](./nordic.atlas-nodes.0074.48f0fb5b0e266b75.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.4552002bccad9b04.js`](./nordic.atlas-nodes.0075.4552002bccad9b04.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.b2c46ad22c4a2c31.js`](./nordic.atlas-nodes.0076.b2c46ad22c4a2c31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.25940d7c2d27b313.js`](./nordic.atlas-nodes.0077.25940d7c2d27b313.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.d5b209764af420b9.js`](./nordic.atlas-nodes.0078.d5b209764af420b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.97687bbf1351ae1e.js`](./nordic.atlas-nodes.0079.97687bbf1351ae1e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.cb75d63522a2fa30.js`](./nordic.atlas-nodes.0080.cb75d63522a2fa30.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.35bd5452ee72f8d3.js`](./nordic.atlas-nodes.0081.35bd5452ee72f8d3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.9e0ff29e503daccf.js`](./nordic.atlas-nodes.0082.9e0ff29e503daccf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.d33078cd62ac6641.js`](./nordic.atlas-nodes.0083.d33078cd62ac6641.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.2173dd3be035445e.js`](./nordic.atlas-nodes.0084.2173dd3be035445e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.8132d8eec5c5566d.js`](./nordic.atlas-nodes.0085.8132d8eec5c5566d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.996074c1a6de049f.js`](./nordic.atlas-nodes.0086.996074c1a6de049f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.9cd5f3afd77ea5c1.js`](./nordic.atlas-nodes.0087.9cd5f3afd77ea5c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.b918e820e2fd5255.js`](./nordic.atlas-nodes.0088.b918e820e2fd5255.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.848a1d4f47c27d6b.js`](./nordic.atlas-nodes.0089.848a1d4f47c27d6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.dd1d43da39998327.js`](./nordic.atlas-nodes.0090.dd1d43da39998327.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.dd9e26d2999c4ac1.js`](./nordic.atlas-nodes.0091.dd9e26d2999c4ac1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.a6092d19e26ad9ad.js`](./nordic.atlas-nodes.0092.a6092d19e26ad9ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.47d252cfb842c5ee.js`](./nordic.atlas-nodes.0093.47d252cfb842c5ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.4678b4affcf39b38.js`](./nordic.atlas-nodes.0094.4678b4affcf39b38.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.2dcf0b928b2ebe36.js`](./nordic.atlas-nodes.0095.2dcf0b928b2ebe36.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.24ed6a0c3b9ec4c5.js`](./nordic.atlas-nodes.0096.24ed6a0c3b9ec4c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.58cbd180f13fc4d9.js`](./nordic.atlas-nodes.0097.58cbd180f13fc4d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.fd1cf0a1f89f4dfe.js`](./nordic.atlas-nodes.0098.fd1cf0a1f89f4dfe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.4dd27e12ac3d48b1.js`](./nordic.atlas-nodes.0099.4dd27e12ac3d48b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.8fe1eca87c850db0.js`](./nordic.atlas-nodes.0100.8fe1eca87c850db0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.7c2461d0e5763941.js`](./nordic.atlas-nodes.0101.7c2461d0e5763941.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.52fcd505e7dba7f6.js`](./nordic.atlas-nodes.0102.52fcd505e7dba7f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.a641d5e3d09a6179.js`](./nordic.atlas-nodes.0103.a641d5e3d09a6179.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.2ab7fc23ec516137.js`](./nordic.atlas-nodes.0104.2ab7fc23ec516137.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.8ff49f0149369dd0.js`](./nordic.atlas-nodes.0105.8ff49f0149369dd0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.51b183affc408dcc.js`](./nordic.atlas-nodes.0106.51b183affc408dcc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.c0e3022cdc1010ee.js`](./nordic.atlas-nodes.0107.c0e3022cdc1010ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.4ed9760693672d5a.js`](./nordic.atlas-nodes.0108.4ed9760693672d5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.17b5f7c8bc898aef.js`](./nordic.atlas-nodes.0109.17b5f7c8bc898aef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.117d10b5a6321a23.js`](./nordic.atlas-nodes.0110.117d10b5a6321a23.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.df398e3ba00c7d78.js`](./nordic.atlas-nodes.0111.df398e3ba00c7d78.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.3c7ea5a68d0997dd.js`](./nordic.atlas-nodes.0112.3c7ea5a68d0997dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.bb121a092f2cf86a.js`](./nordic.atlas-nodes.0113.bb121a092f2cf86a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.37bfe32c8f1d3fa7.js`](./nordic.atlas-nodes.0114.37bfe32c8f1d3fa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.ab2134049fa89241.js`](./nordic.atlas-nodes.0115.ab2134049fa89241.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.62de2fb0c33c60aa.js`](./nordic.atlas-nodes.0116.62de2fb0c33c60aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.cf9339f4b2be1804.js`](./nordic.atlas-nodes.0117.cf9339f4b2be1804.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.ba48de41415dca29.js`](./nordic.atlas-nodes.0118.ba48de41415dca29.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.905212604ee3ea90.js`](./nordic.atlas-nodes.0119.905212604ee3ea90.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.f1e14a771650c078.js`](./nordic.atlas-nodes.0120.f1e14a771650c078.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.2a644ba2525c859d.js`](./nordic.atlas-nodes.0121.2a644ba2525c859d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.5546a6e4fa6747b0.js`](./nordic.atlas-nodes.0122.5546a6e4fa6747b0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.61daa1476687fda3.js`](./nordic.atlas-nodes.0123.61daa1476687fda3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.0eceb9acb5ed1037.js`](./nordic.atlas-nodes.0124.0eceb9acb5ed1037.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.159b36cb0d9a9110.js`](./nordic.atlas-nodes.0125.159b36cb0d9a9110.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.f52654969673399a.js`](./nordic.atlas-nodes.0126.f52654969673399a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.0edd1ea8744e0ba2.js`](./nordic.atlas-nodes.0127.0edd1ea8744e0ba2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.0bb592f09926d940.js`](./nordic.atlas-nodes.0128.0bb592f09926d940.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.1db020a5f12c7763.js`](./nordic.atlas-nodes.0129.1db020a5f12c7763.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.16d12fe046142b6d.js`](./nordic.atlas-nodes.0130.16d12fe046142b6d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.12c919419f154507.js`](./nordic.atlas-nodes.0131.12c919419f154507.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.bae95b51c11e4c9d.js`](./nordic.atlas-nodes.0132.bae95b51c11e4c9d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.ae7605b34e03a097.js`](./nordic.atlas-nodes.0133.ae7605b34e03a097.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.56ad6ab69cd9dd20.js`](./nordic.atlas-nodes.0134.56ad6ab69cd9dd20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.d4c7d22e07761c9b.js`](./nordic.atlas-nodes.0135.d4c7d22e07761c9b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.8e6b9d4a65ccce4b.js`](./nordic.atlas-nodes.0136.8e6b9d4a65ccce4b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.2e12d4a953ecdac8.js`](./nordic.atlas-nodes.0137.2e12d4a953ecdac8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.d0f1049acab0c386.js`](./nordic.atlas-nodes.0138.d0f1049acab0c386.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.f2e1b9031cd81202.js`](./nordic.atlas-nodes.0139.f2e1b9031cd81202.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.d734e8d22573d047.js`](./nordic.atlas-nodes.0140.d734e8d22573d047.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.dae821c854732b46.js`](./nordic.atlas-nodes.0141.dae821c854732b46.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.9c0419a9aad6bfdd.js`](./nordic.atlas-nodes.0142.9c0419a9aad6bfdd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.eb33bfb8a3d7364b.js`](./nordic.atlas-nodes.0143.eb33bfb8a3d7364b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.b4ca91c663a504ed.js`](./nordic.atlas-nodes.0144.b4ca91c663a504ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.d7b6a81f337eec17.js`](./nordic.atlas-nodes.0145.d7b6a81f337eec17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.9b75192fd835804e.js`](./nordic.atlas-nodes.0146.9b75192fd835804e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.ea4858095b7aa996.js`](./nordic.atlas-nodes.0147.ea4858095b7aa996.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.28463cf0efcc5d5d.js`](./nordic.atlas-nodes.0148.28463cf0efcc5d5d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.505215bcc8f62e74.js`](./nordic.atlas-nodes.0149.505215bcc8f62e74.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.25b951a1f95d9007.js`](./nordic.atlas-nodes.0150.25b951a1f95d9007.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.072125582beab28c.js`](./nordic.atlas-nodes.0151.072125582beab28c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.abe3c67f9a1855b6.js`](./nordic.atlas-nodes.0152.abe3c67f9a1855b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.0dce3bc944f05aec.js`](./nordic.atlas-nodes.0153.0dce3bc944f05aec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.168c20f44d2b17c3.js`](./nordic.atlas-nodes.0154.168c20f44d2b17c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.d7033564ce86fe29.js`](./nordic.atlas-nodes.0155.d7033564ce86fe29.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.1b5835c6d806fb08.js`](./nordic.atlas-nodes.0156.1b5835c6d806fb08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.10a7151a171623eb.js`](./nordic.atlas-nodes.0157.10a7151a171623eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.0f1fe2226a6719b3.js`](./nordic.atlas-nodes.0158.0f1fe2226a6719b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.c2340bf48ebc7988.js`](./nordic.atlas-nodes.0159.c2340bf48ebc7988.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.865ad675204e4b70.js`](./nordic.atlas-nodes.0160.865ad675204e4b70.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.1536e8bce5172dba.js`](./nordic.atlas-nodes.0161.1536e8bce5172dba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.48fe662c1d0147d0.js`](./nordic.atlas-nodes.0162.48fe662c1d0147d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.0e7d79f0edcf1df7.js`](./nordic.atlas-nodes.0163.0e7d79f0edcf1df7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.730817598c6e4456.js`](./nordic.atlas-nodes.0164.730817598c6e4456.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.890e6f15e63a5471.js`](./nordic.atlas-details.0165.890e6f15e63a5471.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.bab188308b1d6c26.js`](./nordic.atlas-details.0166.bab188308b1d6c26.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.f4d5e67b0cbf4ed1.js`](./nordic.atlas-details.0167.f4d5e67b0cbf4ed1.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.a1f1447304342fd6.js`](./nordic.atlas-details.0168.a1f1447304342fd6.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.c63063552fa39e49.js`](./nordic.atlas-details.0169.c63063552fa39e49.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.c429fd85cc8b0d5e.js`](./nordic.atlas-details.0170.c429fd85cc8b0d5e.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.ff0eb43f8d5d1950.js`](./nordic.atlas-details.0171.ff0eb43f8d5d1950.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.461d50609f72f33c.js`](./nordic.atlas-details.0172.461d50609f72f33c.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.134c3583853de6b6.js`](./nordic.atlas-details.0173.134c3583853de6b6.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.4de2926c545742fc.js`](./nordic.atlas-details.0174.4de2926c545742fc.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.d3dc8e9cd698a3d7.js`](./nordic.atlas-details.0175.d3dc8e9cd698a3d7.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.184de344531ab1d8.js`](./nordic.atlas-details.0176.184de344531ab1d8.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.d25b4a01456b4b21.js`](./nordic.atlas-details.0177.d25b4a01456b4b21.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.d969e105a4c1fdeb.js`](./nordic.atlas-details.0178.d969e105a4c1fdeb.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.38cf9f623914ebc1.js`](./nordic.atlas-details.0179.38cf9f623914ebc1.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.603dc48802641bbe.js`](./nordic.atlas-details.0180.603dc48802641bbe.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.e41dcea678d2f810.js`](./nordic.atlas-details.0181.e41dcea678d2f810.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.7a9faa20e9c4ef28.js`](./nordic.atlas-details.0182.7a9faa20e9c4ef28.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.48ee00e7bb5e6391.js`](./nordic.atlas-details.0183.48ee00e7bb5e6391.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.772104b8fcd1dd7d.js`](./nordic.atlas-details.0184.772104b8fcd1dd7d.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.76f31dd2b3824662.js`](./nordic.atlas-details.0185.76f31dd2b3824662.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.a19299c3b6813277.js`](./nordic.atlas-details.0186.a19299c3b6813277.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.7d6bda41c6fefb26.js`](./nordic.atlas-details.0187.7d6bda41c6fefb26.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.4c7d2c7fcaccb463.js`](./nordic.atlas-details.0188.4c7d2c7fcaccb463.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.2899f2ec3ff09cbf.js`](./nordic.atlas-details.0189.2899f2ec3ff09cbf.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.604a754ece0fe033.js`](./nordic.atlas-details.0190.604a754ece0fe033.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.8262d07f3d4943b4.js`](./nordic.atlas-details.0191.8262d07f3d4943b4.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.11e2f0df8a79ac93.js`](./nordic.atlas-details.0192.11e2f0df8a79ac93.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.850c7697f94ab593.js`](./nordic.atlas-details.0193.850c7697f94ab593.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.3ab4af29266e7ef8.js`](./nordic.atlas-details.0194.3ab4af29266e7ef8.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.8a0d483ec19e81f4.js`](./nordic.atlas-details.0195.8a0d483ec19e81f4.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.5dc10b0deff430de.js`](./nordic.atlas-details.0196.5dc10b0deff430de.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.c91c10a6274d074d.js`](./nordic.atlas-details.0197.c91c10a6274d074d.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.ce1e007fc761f741.js`](./nordic.atlas-details.0198.ce1e007fc761f741.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.b120b79872f73c4e.js`](./nordic.atlas-details.0199.b120b79872f73c4e.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.4269999402072406.js`](./nordic.atlas-details.0200.4269999402072406.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.67fc2454af915583.js`](./nordic.atlas-details.0201.67fc2454af915583.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.b14d6014c402f25a.js`](./nordic.atlas-details.0202.b14d6014c402f25a.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.2b3218a3492b5cb7.js`](./nordic.atlas-details.0203.2b3218a3492b5cb7.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.6a58c721cd9cecaa.js`](./nordic.atlas-details.0204.6a58c721cd9cecaa.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.8756f74c8d2d58b7.js`](./nordic.atlas-details.0205.8756f74c8d2d58b7.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.4a56545e249750e5.js`](./nordic.atlas-details.0206.4a56545e249750e5.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.3cc3ed4a7522a407.js`](./nordic.atlas-details.0207.3cc3ed4a7522a407.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.8f95e390c92a07be.js`](./nordic.atlas-details.0208.8f95e390c92a07be.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.ab49207b3db6e7f2.js`](./nordic.atlas-details.0209.ab49207b3db6e7f2.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.c70342e8e7be7a69.js`](./nordic.atlas-details.0210.c70342e8e7be7a69.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.56605e80ab0ad758.js`](./nordic.atlas-details.0211.56605e80ab0ad758.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.f976da309cb77aed.js`](./nordic.atlas-details.0212.f976da309cb77aed.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.666f3a9c951836ab.js`](./nordic.atlas-details.0213.666f3a9c951836ab.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.20d6f6d296d76c7d.js`](./nordic.atlas-details.0214.20d6f6d296d76c7d.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.a75329c4ba98913a.js`](./nordic.atlas-details.0215.a75329c4ba98913a.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.aedda1db9e3f6e85.js`](./nordic.atlas-details.0216.aedda1db9e3f6e85.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.d076e50093f6f4fb.js`](./nordic.atlas-details.0217.d076e50093f6f4fb.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.a599087d4beb190a.js`](./nordic.atlas-details.0218.a599087d4beb190a.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.32dac8df1e18cb13.js`](./nordic.atlas-details.0219.32dac8df1e18cb13.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.784d1dc809d75af6.js`](./nordic.atlas-details.0220.784d1dc809d75af6.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.c5aa7787c682982d.js`](./nordic.atlas-details.0221.c5aa7787c682982d.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.5d26818ce8a55712.js`](./nordic.atlas-details.0222.5d26818ce8a55712.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.e1ad50ccd74f8c0d.js`](./nordic.atlas-details.0223.e1ad50ccd74f8c0d.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.6a6538578313eae3.js`](./nordic.atlas-details.0224.6a6538578313eae3.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.30f00187cf94c4a3.js`](./nordic.atlas-details.0225.30f00187cf94c4a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.e2aafb9e4b1ffea3.js`](./nordic.atlas-details.0226.e2aafb9e4b1ffea3.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.cf0e99c2ed80fab4.js`](./nordic.atlas-details.0227.cf0e99c2ed80fab4.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.473943b0132eb442.js`](./nordic.atlas-details.0228.473943b0132eb442.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.454108df1203c1f4.js`](./nordic.atlas-edges.0229.454108df1203c1f4.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.35ff0d584fb6a602.js`](./nordic.atlas-sequences.0230.35ff0d584fb6a602.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.b7f419818c6a30b9.js`](./nordic.atlas-indexes.0231.b7f419818c6a30b9.js)
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
| Sheep aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
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

- Total animal locality points: `6`
- Shipped animal species: `3`
- Domesticated-core species layers: `3`
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
| source_reported_two_decimal_degrees | 2 |

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| horse | Equus caballus | domesticated_core | 2 |
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |


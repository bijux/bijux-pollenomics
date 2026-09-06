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
- Wild and progenitor animal locality GeoJSON: [`nordic_progenitor_animal_localities.geojson`](./nordic_progenitor_animal_localities.geojson)
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.aec40be17ad911a2.js`](./nordic.atlas-provenance.0000.aec40be17ad911a2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.eb3ec01599b4236f.js`](./nordic.atlas-nodes.0001.eb3ec01599b4236f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.d636a09095797f9d.js`](./nordic.atlas-nodes.0002.d636a09095797f9d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.df7ca3cf7f3dbe9f.js`](./nordic.atlas-nodes.0003.df7ca3cf7f3dbe9f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.8b554371ba28b553.js`](./nordic.atlas-nodes.0004.8b554371ba28b553.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.68b9f1917c04c419.js`](./nordic.atlas-nodes.0005.68b9f1917c04c419.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.f200fcab6042b75b.js`](./nordic.atlas-nodes.0006.f200fcab6042b75b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.c0e75603c61860e6.js`](./nordic.atlas-nodes.0007.c0e75603c61860e6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.d1dfe1cd1430f2c9.js`](./nordic.atlas-nodes.0008.d1dfe1cd1430f2c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.96792e8580a6fe3d.js`](./nordic.atlas-nodes.0009.96792e8580a6fe3d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.71c4b810cd7ce141.js`](./nordic.atlas-nodes.0010.71c4b810cd7ce141.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.9db35bdf8612daf7.js`](./nordic.atlas-nodes.0011.9db35bdf8612daf7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.2c5d68374e34452f.js`](./nordic.atlas-nodes.0012.2c5d68374e34452f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.e796809a13242fb6.js`](./nordic.atlas-nodes.0013.e796809a13242fb6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.af84c79c29de7519.js`](./nordic.atlas-nodes.0014.af84c79c29de7519.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.dfe242d6409b8cb4.js`](./nordic.atlas-nodes.0015.dfe242d6409b8cb4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.f128999632053b0d.js`](./nordic.atlas-nodes.0016.f128999632053b0d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.de238757d7d36fc7.js`](./nordic.atlas-nodes.0017.de238757d7d36fc7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.5c79e38d151cb5f6.js`](./nordic.atlas-nodes.0018.5c79e38d151cb5f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.a33b176e514a9bed.js`](./nordic.atlas-nodes.0019.a33b176e514a9bed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.fd52a899a8342b6f.js`](./nordic.atlas-nodes.0020.fd52a899a8342b6f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.82b6ca5a314eff4a.js`](./nordic.atlas-nodes.0021.82b6ca5a314eff4a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.dc7ffdb9546f86f8.js`](./nordic.atlas-nodes.0022.dc7ffdb9546f86f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.7de1b77c7550fa71.js`](./nordic.atlas-nodes.0023.7de1b77c7550fa71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.019ff1f3a754eb72.js`](./nordic.atlas-nodes.0024.019ff1f3a754eb72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.20bc0f23d39bf76e.js`](./nordic.atlas-nodes.0025.20bc0f23d39bf76e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.c9d520079c8fe390.js`](./nordic.atlas-nodes.0026.c9d520079c8fe390.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.a4e490a05c83587b.js`](./nordic.atlas-nodes.0027.a4e490a05c83587b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.f61617a638429627.js`](./nordic.atlas-nodes.0028.f61617a638429627.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.c967d71818b96b92.js`](./nordic.atlas-nodes.0029.c967d71818b96b92.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.925aca96c70889c3.js`](./nordic.atlas-nodes.0030.925aca96c70889c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.d8ea6f51a24ba08a.js`](./nordic.atlas-nodes.0031.d8ea6f51a24ba08a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.26c30b60c0c9646b.js`](./nordic.atlas-nodes.0032.26c30b60c0c9646b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.b2ef96b5a5a2bef7.js`](./nordic.atlas-nodes.0033.b2ef96b5a5a2bef7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.f12dd7a94d41b2eb.js`](./nordic.atlas-nodes.0034.f12dd7a94d41b2eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.d24e3b284d3a5cc1.js`](./nordic.atlas-nodes.0035.d24e3b284d3a5cc1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.7630f3168d1fe31f.js`](./nordic.atlas-nodes.0036.7630f3168d1fe31f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.593189516a594b7b.js`](./nordic.atlas-nodes.0037.593189516a594b7b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.118e68c5ecac5599.js`](./nordic.atlas-nodes.0038.118e68c5ecac5599.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.4544e9a03971e29f.js`](./nordic.atlas-nodes.0039.4544e9a03971e29f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.18137afc29b6ffe3.js`](./nordic.atlas-nodes.0040.18137afc29b6ffe3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.065ca8f88aa52aac.js`](./nordic.atlas-nodes.0041.065ca8f88aa52aac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.281a0186a839066b.js`](./nordic.atlas-nodes.0042.281a0186a839066b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.3ef732c430daaec5.js`](./nordic.atlas-nodes.0043.3ef732c430daaec5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.13d45344b5627855.js`](./nordic.atlas-nodes.0044.13d45344b5627855.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.26b717af27943fb1.js`](./nordic.atlas-nodes.0045.26b717af27943fb1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.0b22725bfba06a20.js`](./nordic.atlas-nodes.0046.0b22725bfba06a20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.5590b588ddae6e69.js`](./nordic.atlas-nodes.0047.5590b588ddae6e69.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.b6364d81fbe96ac5.js`](./nordic.atlas-nodes.0048.b6364d81fbe96ac5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.8c95f6a9d484f8d6.js`](./nordic.atlas-nodes.0049.8c95f6a9d484f8d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.7637488fcfe87af0.js`](./nordic.atlas-nodes.0050.7637488fcfe87af0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.56ade10005846926.js`](./nordic.atlas-nodes.0051.56ade10005846926.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.836dd1a4aab2502a.js`](./nordic.atlas-nodes.0052.836dd1a4aab2502a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.3e840009351e0919.js`](./nordic.atlas-nodes.0053.3e840009351e0919.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.b20aee4f37c8d3c3.js`](./nordic.atlas-nodes.0054.b20aee4f37c8d3c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.54b66a9c459195f3.js`](./nordic.atlas-nodes.0055.54b66a9c459195f3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.144aa48e4f881fe9.js`](./nordic.atlas-nodes.0056.144aa48e4f881fe9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.2c4f230c4176d627.js`](./nordic.atlas-nodes.0057.2c4f230c4176d627.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.9cea6d5ae632fb04.js`](./nordic.atlas-nodes.0058.9cea6d5ae632fb04.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.e59c0eac88a9e924.js`](./nordic.atlas-nodes.0059.e59c0eac88a9e924.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.a8bc18d0f37d063a.js`](./nordic.atlas-nodes.0060.a8bc18d0f37d063a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.fa79c7ad25e94aba.js`](./nordic.atlas-nodes.0061.fa79c7ad25e94aba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.6044957c471c00a9.js`](./nordic.atlas-nodes.0062.6044957c471c00a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.be0c7dae832c8813.js`](./nordic.atlas-nodes.0063.be0c7dae832c8813.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.9ed10f475c410c1c.js`](./nordic.atlas-nodes.0064.9ed10f475c410c1c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.e78cc22ce988c32f.js`](./nordic.atlas-nodes.0065.e78cc22ce988c32f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.5208d5c16187ca6b.js`](./nordic.atlas-nodes.0066.5208d5c16187ca6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.a6c8f81152f47827.js`](./nordic.atlas-nodes.0067.a6c8f81152f47827.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.7e607352392a93cd.js`](./nordic.atlas-nodes.0068.7e607352392a93cd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.64adbc31d020895e.js`](./nordic.atlas-nodes.0069.64adbc31d020895e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.e9c3c399e92cfb58.js`](./nordic.atlas-nodes.0070.e9c3c399e92cfb58.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.d4f94338ec60c02e.js`](./nordic.atlas-nodes.0071.d4f94338ec60c02e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.f3fc8f0262e9f1a4.js`](./nordic.atlas-nodes.0072.f3fc8f0262e9f1a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.d6a27674827a087e.js`](./nordic.atlas-nodes.0073.d6a27674827a087e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.83331e35feea6172.js`](./nordic.atlas-nodes.0074.83331e35feea6172.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.9ed19ca662c7ba9d.js`](./nordic.atlas-nodes.0075.9ed19ca662c7ba9d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.a8bfa55ac25b5e45.js`](./nordic.atlas-nodes.0076.a8bfa55ac25b5e45.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.73a4685a69d49746.js`](./nordic.atlas-nodes.0077.73a4685a69d49746.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.73a4c989ef57c8f1.js`](./nordic.atlas-nodes.0078.73a4c989ef57c8f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.2bf0805597ae9cb3.js`](./nordic.atlas-nodes.0079.2bf0805597ae9cb3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.813a8f5f16df4d76.js`](./nordic.atlas-nodes.0080.813a8f5f16df4d76.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.4a53eacb89d13fd4.js`](./nordic.atlas-nodes.0081.4a53eacb89d13fd4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.2fb1572f5668dc29.js`](./nordic.atlas-nodes.0082.2fb1572f5668dc29.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.9738d315517fbcc8.js`](./nordic.atlas-nodes.0083.9738d315517fbcc8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.82d0720cbe36fbcd.js`](./nordic.atlas-nodes.0084.82d0720cbe36fbcd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.d7ac4a27d9865fd9.js`](./nordic.atlas-nodes.0085.d7ac4a27d9865fd9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.77838dd4a90760e1.js`](./nordic.atlas-nodes.0086.77838dd4a90760e1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.a274efb44bd58e85.js`](./nordic.atlas-nodes.0087.a274efb44bd58e85.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.1391c91eb495d879.js`](./nordic.atlas-nodes.0088.1391c91eb495d879.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.3b4f419dbe61daca.js`](./nordic.atlas-nodes.0089.3b4f419dbe61daca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.9324578033931225.js`](./nordic.atlas-nodes.0090.9324578033931225.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.495b1de1e9c12f31.js`](./nordic.atlas-nodes.0091.495b1de1e9c12f31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.8ac9e0304c92d490.js`](./nordic.atlas-nodes.0092.8ac9e0304c92d490.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.14cca3e3641f7dc1.js`](./nordic.atlas-nodes.0093.14cca3e3641f7dc1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.3d70b0208ab22cbb.js`](./nordic.atlas-nodes.0094.3d70b0208ab22cbb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.06b7b0f849197206.js`](./nordic.atlas-nodes.0095.06b7b0f849197206.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.b583ac1866d39e47.js`](./nordic.atlas-nodes.0096.b583ac1866d39e47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.ace163a55c8807b3.js`](./nordic.atlas-nodes.0097.ace163a55c8807b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.506cdb612fe0fec9.js`](./nordic.atlas-nodes.0098.506cdb612fe0fec9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.bb37fc3fe968b779.js`](./nordic.atlas-nodes.0099.bb37fc3fe968b779.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.b0e1bbcccfb1360a.js`](./nordic.atlas-nodes.0100.b0e1bbcccfb1360a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.5ede51d280c6e8d8.js`](./nordic.atlas-nodes.0101.5ede51d280c6e8d8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.e87d1bb6d9288c43.js`](./nordic.atlas-nodes.0102.e87d1bb6d9288c43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.ec75e7ff13d385d1.js`](./nordic.atlas-nodes.0103.ec75e7ff13d385d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.3f7320731a10e87d.js`](./nordic.atlas-nodes.0104.3f7320731a10e87d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.cf7af52bb22abf71.js`](./nordic.atlas-nodes.0105.cf7af52bb22abf71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.01055e4e9849d341.js`](./nordic.atlas-nodes.0106.01055e4e9849d341.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.f6b57c2a28e276f4.js`](./nordic.atlas-nodes.0107.f6b57c2a28e276f4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.9303176910f38791.js`](./nordic.atlas-nodes.0108.9303176910f38791.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.bb391cf28ce72825.js`](./nordic.atlas-nodes.0109.bb391cf28ce72825.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.d7c29c8bb53f8fa1.js`](./nordic.atlas-nodes.0110.d7c29c8bb53f8fa1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.aae88e09ebd2adda.js`](./nordic.atlas-nodes.0111.aae88e09ebd2adda.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.6e911e16e3dd3fa6.js`](./nordic.atlas-nodes.0112.6e911e16e3dd3fa6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.f97d3a6e10fb525a.js`](./nordic.atlas-nodes.0113.f97d3a6e10fb525a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.c87c401578970dbe.js`](./nordic.atlas-nodes.0114.c87c401578970dbe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.87a7a1d2f7a45c9c.js`](./nordic.atlas-nodes.0115.87a7a1d2f7a45c9c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.145935af15ec63da.js`](./nordic.atlas-nodes.0116.145935af15ec63da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.97cc7d807dadb9f6.js`](./nordic.atlas-nodes.0117.97cc7d807dadb9f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.0e30214fae29fa47.js`](./nordic.atlas-nodes.0118.0e30214fae29fa47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.42e726f82c4bc66e.js`](./nordic.atlas-nodes.0119.42e726f82c4bc66e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.2c7c8521c98ebb69.js`](./nordic.atlas-nodes.0120.2c7c8521c98ebb69.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.7753a67a0d93f521.js`](./nordic.atlas-nodes.0121.7753a67a0d93f521.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.832fdbb9c1725ef2.js`](./nordic.atlas-nodes.0122.832fdbb9c1725ef2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.84f823e15c07d8c6.js`](./nordic.atlas-nodes.0123.84f823e15c07d8c6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.debf0c1e146b6fd5.js`](./nordic.atlas-nodes.0124.debf0c1e146b6fd5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.982b26a418a0ee8d.js`](./nordic.atlas-nodes.0125.982b26a418a0ee8d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.f5b8b03eab924f5a.js`](./nordic.atlas-nodes.0126.f5b8b03eab924f5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.a6f91a8a6c41afd7.js`](./nordic.atlas-nodes.0127.a6f91a8a6c41afd7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.e409a9e8c568a700.js`](./nordic.atlas-nodes.0128.e409a9e8c568a700.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.5b4698eb690c51b7.js`](./nordic.atlas-nodes.0129.5b4698eb690c51b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.a928beda96e570a6.js`](./nordic.atlas-nodes.0130.a928beda96e570a6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.6672c2c0a2fc6ac4.js`](./nordic.atlas-nodes.0131.6672c2c0a2fc6ac4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.06b7073e5404b040.js`](./nordic.atlas-nodes.0132.06b7073e5404b040.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.f70c1865bd0dd179.js`](./nordic.atlas-nodes.0133.f70c1865bd0dd179.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.a92c836c17a0bc8a.js`](./nordic.atlas-nodes.0134.a92c836c17a0bc8a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.e61b73b927cc7fa4.js`](./nordic.atlas-nodes.0135.e61b73b927cc7fa4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.15fa378f451d37d1.js`](./nordic.atlas-nodes.0136.15fa378f451d37d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.a6994369c05a19b6.js`](./nordic.atlas-nodes.0137.a6994369c05a19b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.399adcaefae5204e.js`](./nordic.atlas-nodes.0138.399adcaefae5204e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.348bdd76af7dd043.js`](./nordic.atlas-nodes.0139.348bdd76af7dd043.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.9383a118640bce9b.js`](./nordic.atlas-nodes.0140.9383a118640bce9b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.02f944cbd4aea39f.js`](./nordic.atlas-nodes.0141.02f944cbd4aea39f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.68849c26e8250396.js`](./nordic.atlas-nodes.0142.68849c26e8250396.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.66a36e0e188761f1.js`](./nordic.atlas-nodes.0143.66a36e0e188761f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.6174ab14d41810af.js`](./nordic.atlas-nodes.0144.6174ab14d41810af.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.69f4e9d07630f0d5.js`](./nordic.atlas-nodes.0145.69f4e9d07630f0d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.3d0132cc88c05bbb.js`](./nordic.atlas-nodes.0146.3d0132cc88c05bbb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.f80de852d1706193.js`](./nordic.atlas-nodes.0147.f80de852d1706193.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.ec234558d40a45ab.js`](./nordic.atlas-nodes.0148.ec234558d40a45ab.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.961b36ed9dbe04e2.js`](./nordic.atlas-nodes.0149.961b36ed9dbe04e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.1ae1e1828fd99926.js`](./nordic.atlas-nodes.0150.1ae1e1828fd99926.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.c1d03f83bd4a1206.js`](./nordic.atlas-nodes.0151.c1d03f83bd4a1206.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.f75dd7299f92b5b1.js`](./nordic.atlas-nodes.0152.f75dd7299f92b5b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.d209019cc28e7cea.js`](./nordic.atlas-nodes.0153.d209019cc28e7cea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.f3c48c47389ccf01.js`](./nordic.atlas-nodes.0154.f3c48c47389ccf01.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.afb833be2ea6520e.js`](./nordic.atlas-nodes.0155.afb833be2ea6520e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.85142a8c52b0a47b.js`](./nordic.atlas-nodes.0156.85142a8c52b0a47b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.ab462ca15844e082.js`](./nordic.atlas-nodes.0157.ab462ca15844e082.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.669faf9b95e95720.js`](./nordic.atlas-nodes.0158.669faf9b95e95720.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.6b28ebf67aeccc72.js`](./nordic.atlas-nodes.0159.6b28ebf67aeccc72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.cda3a3947083d236.js`](./nordic.atlas-nodes.0160.cda3a3947083d236.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.a208dd36349aca8a.js`](./nordic.atlas-nodes.0161.a208dd36349aca8a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.77d547bce0133bff.js`](./nordic.atlas-nodes.0162.77d547bce0133bff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.3a4733bf9efdb7dd.js`](./nordic.atlas-nodes.0163.3a4733bf9efdb7dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.63d3070be5bf1d3c.js`](./nordic.atlas-nodes.0164.63d3070be5bf1d3c.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.2338220a22caa1bd.js`](./nordic.atlas-details.0165.2338220a22caa1bd.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.bbfc306aae199563.js`](./nordic.atlas-details.0166.bbfc306aae199563.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.786b45d37c7bf469.js`](./nordic.atlas-details.0167.786b45d37c7bf469.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.e8de92c0b90eee5c.js`](./nordic.atlas-details.0168.e8de92c0b90eee5c.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.c64ec1499c00d001.js`](./nordic.atlas-details.0169.c64ec1499c00d001.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.64b30c118ec3803f.js`](./nordic.atlas-details.0170.64b30c118ec3803f.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.5a745d65cb3953f8.js`](./nordic.atlas-details.0171.5a745d65cb3953f8.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.be53b92622029b77.js`](./nordic.atlas-details.0172.be53b92622029b77.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.c1117da7aaa37acd.js`](./nordic.atlas-details.0173.c1117da7aaa37acd.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.862568dc6217ead3.js`](./nordic.atlas-details.0174.862568dc6217ead3.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.4942da6b5b9d3228.js`](./nordic.atlas-details.0175.4942da6b5b9d3228.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.61ec8fd2da5178a3.js`](./nordic.atlas-details.0176.61ec8fd2da5178a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.5df42cc360bbd3c8.js`](./nordic.atlas-details.0177.5df42cc360bbd3c8.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.9cc7f301fe56fa88.js`](./nordic.atlas-details.0178.9cc7f301fe56fa88.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.0a9d311afa271560.js`](./nordic.atlas-details.0179.0a9d311afa271560.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.6ce6967794ffd735.js`](./nordic.atlas-details.0180.6ce6967794ffd735.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.a220b0a2c83cac47.js`](./nordic.atlas-details.0181.a220b0a2c83cac47.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.63d142ba333b150a.js`](./nordic.atlas-details.0182.63d142ba333b150a.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.135740465ca1322e.js`](./nordic.atlas-details.0183.135740465ca1322e.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.284c1dc7e211f852.js`](./nordic.atlas-details.0184.284c1dc7e211f852.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.7b32e25ee01bacb0.js`](./nordic.atlas-details.0185.7b32e25ee01bacb0.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.98967ef6dee2413b.js`](./nordic.atlas-details.0186.98967ef6dee2413b.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.0f7f6629cb18ff3d.js`](./nordic.atlas-details.0187.0f7f6629cb18ff3d.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.0c7702d0b6ef20ee.js`](./nordic.atlas-details.0188.0c7702d0b6ef20ee.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.654e7165e4e05935.js`](./nordic.atlas-details.0189.654e7165e4e05935.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.c31e73fd9be83002.js`](./nordic.atlas-details.0190.c31e73fd9be83002.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.7c35ea358c6191aa.js`](./nordic.atlas-details.0191.7c35ea358c6191aa.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.13e08d7cbc896a93.js`](./nordic.atlas-details.0192.13e08d7cbc896a93.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.77b3580c785732f3.js`](./nordic.atlas-details.0193.77b3580c785732f3.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.c39e24c5ef7f5a21.js`](./nordic.atlas-details.0194.c39e24c5ef7f5a21.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.c608e221a5eb1e32.js`](./nordic.atlas-details.0195.c608e221a5eb1e32.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.59dd9aad5706da05.js`](./nordic.atlas-details.0196.59dd9aad5706da05.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.112e6e9f988236e0.js`](./nordic.atlas-details.0197.112e6e9f988236e0.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.a8e79cfe93f3e2fe.js`](./nordic.atlas-details.0198.a8e79cfe93f3e2fe.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.05d2078936936da7.js`](./nordic.atlas-details.0199.05d2078936936da7.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.514f5b3a7bde9a3d.js`](./nordic.atlas-details.0200.514f5b3a7bde9a3d.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.768fabd13c574f07.js`](./nordic.atlas-details.0201.768fabd13c574f07.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.09dc00e1c99eaf4e.js`](./nordic.atlas-details.0202.09dc00e1c99eaf4e.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.080c914cdbe64435.js`](./nordic.atlas-details.0203.080c914cdbe64435.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.982f02a091e20231.js`](./nordic.atlas-details.0204.982f02a091e20231.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.6bbf944431d20527.js`](./nordic.atlas-details.0205.6bbf944431d20527.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.d291638f7e85b507.js`](./nordic.atlas-details.0206.d291638f7e85b507.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.403409fe0650b049.js`](./nordic.atlas-details.0207.403409fe0650b049.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.0611c7f8c3bc5eff.js`](./nordic.atlas-details.0208.0611c7f8c3bc5eff.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.5dfea635fa66b43a.js`](./nordic.atlas-details.0209.5dfea635fa66b43a.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.394ad6abe044234b.js`](./nordic.atlas-details.0210.394ad6abe044234b.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.b568ac3f5dc88eaf.js`](./nordic.atlas-details.0211.b568ac3f5dc88eaf.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.191a2f8a1c988cdd.js`](./nordic.atlas-details.0212.191a2f8a1c988cdd.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.312b2d666acdfce4.js`](./nordic.atlas-details.0213.312b2d666acdfce4.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.a97d6450a08ed623.js`](./nordic.atlas-details.0214.a97d6450a08ed623.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.622af55b5e8fe1e8.js`](./nordic.atlas-details.0215.622af55b5e8fe1e8.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.b7802a1f2cf1bb8e.js`](./nordic.atlas-details.0216.b7802a1f2cf1bb8e.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.13a8901f26f41c05.js`](./nordic.atlas-details.0217.13a8901f26f41c05.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.610aa379cac6c81d.js`](./nordic.atlas-details.0218.610aa379cac6c81d.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.8a117d02ba2a75b8.js`](./nordic.atlas-details.0219.8a117d02ba2a75b8.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.d408f0e99d593b86.js`](./nordic.atlas-details.0220.d408f0e99d593b86.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.e2519a5e0fa672d5.js`](./nordic.atlas-details.0221.e2519a5e0fa672d5.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.82bb2331ddf88e6a.js`](./nordic.atlas-details.0222.82bb2331ddf88e6a.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.b0c93d2c41ee2d59.js`](./nordic.atlas-details.0223.b0c93d2c41ee2d59.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.b5bb5c368754aba7.js`](./nordic.atlas-details.0224.b5bb5c368754aba7.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.567dd2bcdea24e1a.js`](./nordic.atlas-details.0225.567dd2bcdea24e1a.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.9bf081d23f512c3a.js`](./nordic.atlas-details.0226.9bf081d23f512c3a.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.c3780cd273e063af.js`](./nordic.atlas-details.0227.c3780cd273e063af.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.b1ff846913ecfc9c.js`](./nordic.atlas-details.0228.b1ff846913ecfc9c.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.db5c44c74cc2a33d.js`](./nordic.atlas-edges.0229.db5c44c74cc2a33d.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.dd8ae025e1eea794.js`](./nordic.atlas-sequences.0230.dd8ae025e1eea794.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.ac7ba13efad2b06f.js`](./nordic.atlas-indexes.0231.ac7ba13efad2b06f.js)
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


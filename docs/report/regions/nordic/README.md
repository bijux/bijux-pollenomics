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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.d524e45d8fc846be.js`](./nordic.atlas-provenance.0000.d524e45d8fc846be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.4982fa5040f3eb82.js`](./nordic.atlas-nodes.0001.4982fa5040f3eb82.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.38d03fdf6ee5c646.js`](./nordic.atlas-nodes.0002.38d03fdf6ee5c646.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.cdbb5d8f052a5da4.js`](./nordic.atlas-nodes.0003.cdbb5d8f052a5da4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.74b461edbcd72e92.js`](./nordic.atlas-nodes.0004.74b461edbcd72e92.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.a42c1891f3debe75.js`](./nordic.atlas-nodes.0005.a42c1891f3debe75.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.d0f763b1f7475454.js`](./nordic.atlas-nodes.0006.d0f763b1f7475454.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.e500d55580449879.js`](./nordic.atlas-nodes.0007.e500d55580449879.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.f7ab5dc2ba821168.js`](./nordic.atlas-nodes.0008.f7ab5dc2ba821168.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.65b398af184cd750.js`](./nordic.atlas-nodes.0009.65b398af184cd750.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.c568cd2d833bba79.js`](./nordic.atlas-nodes.0010.c568cd2d833bba79.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.1c4463574e0447e2.js`](./nordic.atlas-nodes.0011.1c4463574e0447e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.733369b89fb617c8.js`](./nordic.atlas-nodes.0012.733369b89fb617c8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.5b207fb3eeccfd5d.js`](./nordic.atlas-nodes.0013.5b207fb3eeccfd5d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.aa11c522e83c2c62.js`](./nordic.atlas-nodes.0014.aa11c522e83c2c62.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.5582cf26d62ec931.js`](./nordic.atlas-nodes.0015.5582cf26d62ec931.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.1f06f4ea053c3e96.js`](./nordic.atlas-nodes.0016.1f06f4ea053c3e96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.6a43285c255cd211.js`](./nordic.atlas-nodes.0017.6a43285c255cd211.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.344bfa33e637c2ab.js`](./nordic.atlas-nodes.0018.344bfa33e637c2ab.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.9e0281b247a439d0.js`](./nordic.atlas-nodes.0019.9e0281b247a439d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.86fb0d08d28c18b4.js`](./nordic.atlas-nodes.0020.86fb0d08d28c18b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.ab10a6a5c49d67ad.js`](./nordic.atlas-nodes.0021.ab10a6a5c49d67ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.43efcc37328079bb.js`](./nordic.atlas-nodes.0022.43efcc37328079bb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.78c34a398638b055.js`](./nordic.atlas-nodes.0023.78c34a398638b055.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.ab981b1e79bb9d46.js`](./nordic.atlas-nodes.0024.ab981b1e79bb9d46.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.8f8b901d05356874.js`](./nordic.atlas-nodes.0025.8f8b901d05356874.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.6e50289bae04c946.js`](./nordic.atlas-nodes.0026.6e50289bae04c946.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.fb34492a75b0275b.js`](./nordic.atlas-nodes.0027.fb34492a75b0275b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.84e8137ad3251d66.js`](./nordic.atlas-nodes.0028.84e8137ad3251d66.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.5a66f4be40dd101f.js`](./nordic.atlas-nodes.0029.5a66f4be40dd101f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.a48dbb26e9657cb5.js`](./nordic.atlas-nodes.0030.a48dbb26e9657cb5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.64d62152c92a5b2c.js`](./nordic.atlas-nodes.0031.64d62152c92a5b2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.45a828cb6e7a02bd.js`](./nordic.atlas-nodes.0032.45a828cb6e7a02bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.3e623cef7bf2a362.js`](./nordic.atlas-nodes.0033.3e623cef7bf2a362.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.f5e5399123d9dab9.js`](./nordic.atlas-nodes.0034.f5e5399123d9dab9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.29808a6378216140.js`](./nordic.atlas-nodes.0035.29808a6378216140.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.b2bdafc792df674d.js`](./nordic.atlas-nodes.0036.b2bdafc792df674d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.ec687e61681dad91.js`](./nordic.atlas-nodes.0037.ec687e61681dad91.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.1a677d1128bec792.js`](./nordic.atlas-nodes.0038.1a677d1128bec792.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.43c611f21b32857c.js`](./nordic.atlas-nodes.0039.43c611f21b32857c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.2b19eb839ec5d02b.js`](./nordic.atlas-nodes.0040.2b19eb839ec5d02b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.3b53905feabee29a.js`](./nordic.atlas-nodes.0041.3b53905feabee29a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.26b85c15bb3fe314.js`](./nordic.atlas-nodes.0042.26b85c15bb3fe314.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.1da12d69a61a6bd7.js`](./nordic.atlas-nodes.0043.1da12d69a61a6bd7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.41ec4aef900f85c3.js`](./nordic.atlas-nodes.0044.41ec4aef900f85c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.ff4f1591c1c52527.js`](./nordic.atlas-nodes.0045.ff4f1591c1c52527.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.a34af0ea6f0cc511.js`](./nordic.atlas-nodes.0046.a34af0ea6f0cc511.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.c5841503cf352910.js`](./nordic.atlas-nodes.0047.c5841503cf352910.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.82841fb1e2ec60c5.js`](./nordic.atlas-nodes.0048.82841fb1e2ec60c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.9f40989f003565b0.js`](./nordic.atlas-nodes.0049.9f40989f003565b0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.e95aaec08dc083c5.js`](./nordic.atlas-nodes.0050.e95aaec08dc083c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.8817231e1375ac08.js`](./nordic.atlas-nodes.0051.8817231e1375ac08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.d5e02a62a9678c4f.js`](./nordic.atlas-nodes.0052.d5e02a62a9678c4f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.edc80fbc9f49bb16.js`](./nordic.atlas-nodes.0053.edc80fbc9f49bb16.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.f7e81a1f178ab080.js`](./nordic.atlas-nodes.0054.f7e81a1f178ab080.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.6a6bbc77440585c5.js`](./nordic.atlas-nodes.0055.6a6bbc77440585c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.513f83cb419021db.js`](./nordic.atlas-nodes.0056.513f83cb419021db.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.077412b7df939723.js`](./nordic.atlas-nodes.0057.077412b7df939723.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.8a89c053faedf1e2.js`](./nordic.atlas-nodes.0058.8a89c053faedf1e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.fadc3c9f161e6c8d.js`](./nordic.atlas-nodes.0059.fadc3c9f161e6c8d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.c7556b983b634799.js`](./nordic.atlas-nodes.0060.c7556b983b634799.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.f512957de4181950.js`](./nordic.atlas-nodes.0061.f512957de4181950.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.35354eefa873e8f4.js`](./nordic.atlas-nodes.0062.35354eefa873e8f4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.17b506fdc992a8b9.js`](./nordic.atlas-nodes.0063.17b506fdc992a8b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.cca36c950a778745.js`](./nordic.atlas-nodes.0064.cca36c950a778745.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.573377d146042d2b.js`](./nordic.atlas-nodes.0065.573377d146042d2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.0dddbb95322214d7.js`](./nordic.atlas-nodes.0066.0dddbb95322214d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.1da2d20c62829cfc.js`](./nordic.atlas-nodes.0067.1da2d20c62829cfc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.3f73643054bc2367.js`](./nordic.atlas-nodes.0068.3f73643054bc2367.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.f361585552bd7c91.js`](./nordic.atlas-nodes.0069.f361585552bd7c91.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.869e8a6463439531.js`](./nordic.atlas-nodes.0070.869e8a6463439531.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.6cb3eadfab82a535.js`](./nordic.atlas-nodes.0071.6cb3eadfab82a535.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.ad6f22d9801f45ba.js`](./nordic.atlas-nodes.0072.ad6f22d9801f45ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.3ea4dc67f0a26851.js`](./nordic.atlas-nodes.0073.3ea4dc67f0a26851.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.0b0c37da4f6bb32a.js`](./nordic.atlas-nodes.0074.0b0c37da4f6bb32a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.b637fac66b1e5590.js`](./nordic.atlas-nodes.0075.b637fac66b1e5590.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.5981a074c3672f1d.js`](./nordic.atlas-nodes.0076.5981a074c3672f1d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.a67394f246bd5c02.js`](./nordic.atlas-nodes.0077.a67394f246bd5c02.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.d8a1955796a041ac.js`](./nordic.atlas-nodes.0078.d8a1955796a041ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.59d3510bceb1ee0c.js`](./nordic.atlas-nodes.0079.59d3510bceb1ee0c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.a72ab00ae300354f.js`](./nordic.atlas-nodes.0080.a72ab00ae300354f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.b25477180a9dcd3c.js`](./nordic.atlas-nodes.0081.b25477180a9dcd3c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.17b5fd7144252584.js`](./nordic.atlas-nodes.0082.17b5fd7144252584.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.0570f5eb19061bcd.js`](./nordic.atlas-nodes.0083.0570f5eb19061bcd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.d4ca7990ba8df423.js`](./nordic.atlas-nodes.0084.d4ca7990ba8df423.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.32406ad4cff1f28e.js`](./nordic.atlas-nodes.0085.32406ad4cff1f28e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.bac660d99f120ddf.js`](./nordic.atlas-nodes.0086.bac660d99f120ddf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.0a95d1fc050d9dbf.js`](./nordic.atlas-nodes.0087.0a95d1fc050d9dbf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.cae3e0f3164df3fb.js`](./nordic.atlas-nodes.0088.cae3e0f3164df3fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.a0122bae5420918f.js`](./nordic.atlas-nodes.0089.a0122bae5420918f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.25f23ba7eab038a3.js`](./nordic.atlas-nodes.0090.25f23ba7eab038a3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.356f9ff7e91e0cd5.js`](./nordic.atlas-nodes.0091.356f9ff7e91e0cd5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.550fbf84baae5c2c.js`](./nordic.atlas-nodes.0092.550fbf84baae5c2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.a9317efdeca7bb69.js`](./nordic.atlas-nodes.0093.a9317efdeca7bb69.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.d29abe4b0bc82868.js`](./nordic.atlas-nodes.0094.d29abe4b0bc82868.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.438074c2ab372d44.js`](./nordic.atlas-nodes.0095.438074c2ab372d44.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.4b7b5df3a16222ad.js`](./nordic.atlas-nodes.0096.4b7b5df3a16222ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.5b035a596e43a79b.js`](./nordic.atlas-nodes.0097.5b035a596e43a79b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.146aea8ac4fb3e25.js`](./nordic.atlas-nodes.0098.146aea8ac4fb3e25.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.dfdecee65b8f86b4.js`](./nordic.atlas-nodes.0099.dfdecee65b8f86b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.e889dcaa5023acb2.js`](./nordic.atlas-nodes.0100.e889dcaa5023acb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.3e608e8483bb78e3.js`](./nordic.atlas-nodes.0101.3e608e8483bb78e3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.f8e25b84e9f498e8.js`](./nordic.atlas-nodes.0102.f8e25b84e9f498e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.58a84b0930e13937.js`](./nordic.atlas-nodes.0103.58a84b0930e13937.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.3a2ad0f7add836ef.js`](./nordic.atlas-nodes.0104.3a2ad0f7add836ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.be7ee0a559b417e8.js`](./nordic.atlas-nodes.0105.be7ee0a559b417e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.842726d783ab8054.js`](./nordic.atlas-nodes.0106.842726d783ab8054.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.1a47fc309db2724d.js`](./nordic.atlas-nodes.0107.1a47fc309db2724d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.a36d2424535426db.js`](./nordic.atlas-nodes.0108.a36d2424535426db.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.79db4dd7e358f6dd.js`](./nordic.atlas-nodes.0109.79db4dd7e358f6dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.3c9b431f1a539f72.js`](./nordic.atlas-nodes.0110.3c9b431f1a539f72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.b232fdb05fd2d93a.js`](./nordic.atlas-nodes.0111.b232fdb05fd2d93a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.631f623640c88aee.js`](./nordic.atlas-nodes.0112.631f623640c88aee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.a703d08fa246e42e.js`](./nordic.atlas-nodes.0113.a703d08fa246e42e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.ea7dfac4d118f81d.js`](./nordic.atlas-nodes.0114.ea7dfac4d118f81d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.86697366f9cc0b94.js`](./nordic.atlas-nodes.0115.86697366f9cc0b94.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.ae891cbb0552f0cf.js`](./nordic.atlas-nodes.0116.ae891cbb0552f0cf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.58aa9c35ec90e6a8.js`](./nordic.atlas-nodes.0117.58aa9c35ec90e6a8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.9d3a581d5ee614e6.js`](./nordic.atlas-nodes.0118.9d3a581d5ee614e6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.5230a35a3cddf902.js`](./nordic.atlas-nodes.0119.5230a35a3cddf902.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.cefb14791ae22971.js`](./nordic.atlas-nodes.0120.cefb14791ae22971.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.84f196d20bf14a51.js`](./nordic.atlas-nodes.0121.84f196d20bf14a51.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.df946d55f72cd9d2.js`](./nordic.atlas-nodes.0122.df946d55f72cd9d2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.9f0aa32742f5d329.js`](./nordic.atlas-nodes.0123.9f0aa32742f5d329.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.7f6d1ae53741cab6.js`](./nordic.atlas-nodes.0124.7f6d1ae53741cab6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.2daa962ff800bb6d.js`](./nordic.atlas-nodes.0125.2daa962ff800bb6d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.78afcbfd832d682e.js`](./nordic.atlas-nodes.0126.78afcbfd832d682e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.f7dbd3805fb38a5c.js`](./nordic.atlas-nodes.0127.f7dbd3805fb38a5c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.6521eaceea9361fb.js`](./nordic.atlas-nodes.0128.6521eaceea9361fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.4487752659c138d0.js`](./nordic.atlas-nodes.0129.4487752659c138d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.c13520d434509c68.js`](./nordic.atlas-nodes.0130.c13520d434509c68.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.8ffbac1d6562a627.js`](./nordic.atlas-nodes.0131.8ffbac1d6562a627.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.e6a5658e9eb3d013.js`](./nordic.atlas-nodes.0132.e6a5658e9eb3d013.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.12af15607e423b41.js`](./nordic.atlas-nodes.0133.12af15607e423b41.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.ca989466033ee8e1.js`](./nordic.atlas-nodes.0134.ca989466033ee8e1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.645c80e21bd916e9.js`](./nordic.atlas-nodes.0135.645c80e21bd916e9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.175a699163797728.js`](./nordic.atlas-nodes.0136.175a699163797728.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.47db8dab7b9a631e.js`](./nordic.atlas-nodes.0137.47db8dab7b9a631e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.c49aeb91363e125f.js`](./nordic.atlas-nodes.0138.c49aeb91363e125f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.28c88d1ebf777777.js`](./nordic.atlas-nodes.0139.28c88d1ebf777777.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.80128b58cbe98d61.js`](./nordic.atlas-nodes.0140.80128b58cbe98d61.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.4f1dead00958e630.js`](./nordic.atlas-nodes.0141.4f1dead00958e630.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.2cf61ad77c8b487f.js`](./nordic.atlas-nodes.0142.2cf61ad77c8b487f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.578944d536ce76c2.js`](./nordic.atlas-nodes.0143.578944d536ce76c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.b64db3ca9592ba0f.js`](./nordic.atlas-nodes.0144.b64db3ca9592ba0f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.b295111b825cac88.js`](./nordic.atlas-nodes.0145.b295111b825cac88.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.9bce0ff5094af65f.js`](./nordic.atlas-nodes.0146.9bce0ff5094af65f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.f1580bb7dd132d9c.js`](./nordic.atlas-nodes.0147.f1580bb7dd132d9c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.b2ec8052107d4f22.js`](./nordic.atlas-nodes.0148.b2ec8052107d4f22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.9f92ee107cc3949a.js`](./nordic.atlas-nodes.0149.9f92ee107cc3949a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.f3cabaa3c32e3988.js`](./nordic.atlas-nodes.0150.f3cabaa3c32e3988.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.22536628088c8b11.js`](./nordic.atlas-nodes.0151.22536628088c8b11.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.0353a06926e85dea.js`](./nordic.atlas-nodes.0152.0353a06926e85dea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.50e7e1ca3891a08b.js`](./nordic.atlas-nodes.0153.50e7e1ca3891a08b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.db21406de6d55820.js`](./nordic.atlas-nodes.0154.db21406de6d55820.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.24e810966be75bc6.js`](./nordic.atlas-nodes.0155.24e810966be75bc6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.8a47a22f58872baf.js`](./nordic.atlas-nodes.0156.8a47a22f58872baf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.2a228f107c42910e.js`](./nordic.atlas-nodes.0157.2a228f107c42910e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.0d1bfde1e0e875df.js`](./nordic.atlas-nodes.0158.0d1bfde1e0e875df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.bc3b9c7281617d33.js`](./nordic.atlas-nodes.0159.bc3b9c7281617d33.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.231ad253ca45da6f.js`](./nordic.atlas-nodes.0160.231ad253ca45da6f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.6674491781d4d47f.js`](./nordic.atlas-nodes.0161.6674491781d4d47f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.00eacb59781a340e.js`](./nordic.atlas-nodes.0162.00eacb59781a340e.js)
- Static atlas data chunk: [`nordic.atlas-details.0163.7f53a6376c4aade2.js`](./nordic.atlas-details.0163.7f53a6376c4aade2.js)
- Static atlas data chunk: [`nordic.atlas-details.0164.7734d2919ae4d3e0.js`](./nordic.atlas-details.0164.7734d2919ae4d3e0.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.599b90fd08fa3c94.js`](./nordic.atlas-details.0165.599b90fd08fa3c94.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.54463ad3027bdb40.js`](./nordic.atlas-details.0166.54463ad3027bdb40.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.467241a9871712a8.js`](./nordic.atlas-details.0167.467241a9871712a8.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.4b0c31a2bbbd20e2.js`](./nordic.atlas-details.0168.4b0c31a2bbbd20e2.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.6df68d7b495e229f.js`](./nordic.atlas-details.0169.6df68d7b495e229f.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.8e6aecbf6eb3d158.js`](./nordic.atlas-details.0170.8e6aecbf6eb3d158.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.2a40d382535aaacb.js`](./nordic.atlas-details.0171.2a40d382535aaacb.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.3a3328f99d0aa6dc.js`](./nordic.atlas-details.0172.3a3328f99d0aa6dc.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.369f3af74e68d7ff.js`](./nordic.atlas-details.0173.369f3af74e68d7ff.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.cb32db9ac48ba4c5.js`](./nordic.atlas-details.0174.cb32db9ac48ba4c5.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.e7ff822d1e44c786.js`](./nordic.atlas-details.0175.e7ff822d1e44c786.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.d1cbd314e416e9cd.js`](./nordic.atlas-details.0176.d1cbd314e416e9cd.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.2033f4e571ec4838.js`](./nordic.atlas-details.0177.2033f4e571ec4838.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.ded262d38003caf6.js`](./nordic.atlas-details.0178.ded262d38003caf6.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.808a568ae1a5abc9.js`](./nordic.atlas-details.0179.808a568ae1a5abc9.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.8f6131ad837510d3.js`](./nordic.atlas-details.0180.8f6131ad837510d3.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.060698327497bc36.js`](./nordic.atlas-details.0181.060698327497bc36.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.691f0ed8a249745b.js`](./nordic.atlas-details.0182.691f0ed8a249745b.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.6af26fa114038c30.js`](./nordic.atlas-details.0183.6af26fa114038c30.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.2bb8ffa26e6d0f01.js`](./nordic.atlas-details.0184.2bb8ffa26e6d0f01.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.f47eeea4815d68ca.js`](./nordic.atlas-details.0185.f47eeea4815d68ca.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.75ff5b81d5df9dbb.js`](./nordic.atlas-details.0186.75ff5b81d5df9dbb.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.a07bed3b03e64008.js`](./nordic.atlas-details.0187.a07bed3b03e64008.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.8bf6b4187b60bd5a.js`](./nordic.atlas-details.0188.8bf6b4187b60bd5a.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.59de584e488cf5c6.js`](./nordic.atlas-details.0189.59de584e488cf5c6.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.740478e07f7d18a4.js`](./nordic.atlas-details.0190.740478e07f7d18a4.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.cfc18c848e652ffb.js`](./nordic.atlas-details.0191.cfc18c848e652ffb.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.b2b06f750465c2c0.js`](./nordic.atlas-details.0192.b2b06f750465c2c0.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.b1868e05cc27ec51.js`](./nordic.atlas-details.0193.b1868e05cc27ec51.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.9264d0094d89f95b.js`](./nordic.atlas-details.0194.9264d0094d89f95b.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.565b3bff7d5054f6.js`](./nordic.atlas-details.0195.565b3bff7d5054f6.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.a472a2b61a30ee7c.js`](./nordic.atlas-details.0196.a472a2b61a30ee7c.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.11f13117a4908b90.js`](./nordic.atlas-details.0197.11f13117a4908b90.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.c804210d0330f869.js`](./nordic.atlas-details.0198.c804210d0330f869.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.160be52a3154150c.js`](./nordic.atlas-details.0199.160be52a3154150c.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.2c568efc0283744c.js`](./nordic.atlas-details.0200.2c568efc0283744c.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.212ae6db7229a01e.js`](./nordic.atlas-details.0201.212ae6db7229a01e.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.b84afd76d710f83f.js`](./nordic.atlas-details.0202.b84afd76d710f83f.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.ad2dc6a36759e049.js`](./nordic.atlas-details.0203.ad2dc6a36759e049.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.d3b9685679799869.js`](./nordic.atlas-details.0204.d3b9685679799869.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.8070599c0bb72c3d.js`](./nordic.atlas-details.0205.8070599c0bb72c3d.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.ef8daff9d3915694.js`](./nordic.atlas-details.0206.ef8daff9d3915694.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.331b0920eff04e71.js`](./nordic.atlas-details.0207.331b0920eff04e71.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.ef588eebb6e4aaa3.js`](./nordic.atlas-details.0208.ef588eebb6e4aaa3.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.01c857d4847918af.js`](./nordic.atlas-details.0209.01c857d4847918af.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.d16a8a966ca1e093.js`](./nordic.atlas-details.0210.d16a8a966ca1e093.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.6972dd9cbd3e34d9.js`](./nordic.atlas-details.0211.6972dd9cbd3e34d9.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.671ca9d4c3d8b860.js`](./nordic.atlas-details.0212.671ca9d4c3d8b860.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.b16cb213a3846561.js`](./nordic.atlas-details.0213.b16cb213a3846561.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.9f745d40801fa9fd.js`](./nordic.atlas-details.0214.9f745d40801fa9fd.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.8887929da6b1aa9c.js`](./nordic.atlas-details.0215.8887929da6b1aa9c.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.d6e5b728bcc0e65e.js`](./nordic.atlas-details.0216.d6e5b728bcc0e65e.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.339dc61a1ce3477c.js`](./nordic.atlas-details.0217.339dc61a1ce3477c.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.dee6b6e93792e42f.js`](./nordic.atlas-details.0218.dee6b6e93792e42f.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.a2b902eefe7526d7.js`](./nordic.atlas-details.0219.a2b902eefe7526d7.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.dd295816f8890939.js`](./nordic.atlas-details.0220.dd295816f8890939.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.88f22b8e9b54a812.js`](./nordic.atlas-details.0221.88f22b8e9b54a812.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.1313445033463cba.js`](./nordic.atlas-details.0222.1313445033463cba.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.1b2de290e2c06ae6.js`](./nordic.atlas-details.0223.1b2de290e2c06ae6.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.0acaa422294418cb.js`](./nordic.atlas-details.0224.0acaa422294418cb.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.d9216a33eec7d562.js`](./nordic.atlas-details.0225.d9216a33eec7d562.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.8075a166be2bbfdb.js`](./nordic.atlas-details.0226.8075a166be2bbfdb.js)
- Static atlas data chunk: [`nordic.atlas-edges.0227.01f3bb24b58dd12f.js`](./nordic.atlas-edges.0227.01f3bb24b58dd12f.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0228.34f1c155977715f1.js`](./nordic.atlas-sequences.0228.34f1c155977715f1.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0229.65d170601fedff8f.js`](./nordic.atlas-indexes.0229.65d170601fedff8f.js)
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


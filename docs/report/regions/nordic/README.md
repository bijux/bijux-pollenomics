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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.f13d07100f882092.js`](./nordic.atlas-provenance.0000.f13d07100f882092.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.6bbb24267a9fcbde.js`](./nordic.atlas-nodes.0001.6bbb24267a9fcbde.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.847eba55ffaaea7e.js`](./nordic.atlas-nodes.0002.847eba55ffaaea7e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.7a96a0d498ec06c1.js`](./nordic.atlas-nodes.0003.7a96a0d498ec06c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.14f23325e9fed78e.js`](./nordic.atlas-nodes.0004.14f23325e9fed78e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.fd61d186cc57442c.js`](./nordic.atlas-nodes.0005.fd61d186cc57442c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.ccccf75909eedc27.js`](./nordic.atlas-nodes.0006.ccccf75909eedc27.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.4763e402efd2f00a.js`](./nordic.atlas-nodes.0007.4763e402efd2f00a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.7fe242ac87c92069.js`](./nordic.atlas-nodes.0008.7fe242ac87c92069.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.bd029b508b8b81f6.js`](./nordic.atlas-nodes.0009.bd029b508b8b81f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.5cd96aadfa78fd0c.js`](./nordic.atlas-nodes.0010.5cd96aadfa78fd0c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.65f5d66055c0de41.js`](./nordic.atlas-nodes.0011.65f5d66055c0de41.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.1a95e06e6328ada1.js`](./nordic.atlas-nodes.0012.1a95e06e6328ada1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.48b88d6bfd551b53.js`](./nordic.atlas-nodes.0013.48b88d6bfd551b53.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.77d4004f66146615.js`](./nordic.atlas-nodes.0014.77d4004f66146615.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.d58fdeccc16dd3a0.js`](./nordic.atlas-nodes.0015.d58fdeccc16dd3a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.d2575fdded2d84b0.js`](./nordic.atlas-nodes.0016.d2575fdded2d84b0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.6cf2c2564f35002d.js`](./nordic.atlas-nodes.0017.6cf2c2564f35002d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.5cf58152ee54a86d.js`](./nordic.atlas-nodes.0018.5cf58152ee54a86d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.4e5c655888f58cac.js`](./nordic.atlas-nodes.0019.4e5c655888f58cac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.2af7d0550e2f80e0.js`](./nordic.atlas-nodes.0020.2af7d0550e2f80e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.2865fe966a4c14ca.js`](./nordic.atlas-nodes.0021.2865fe966a4c14ca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.ad6d05d7e20c0c23.js`](./nordic.atlas-nodes.0022.ad6d05d7e20c0c23.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.101d89a4e69a50ad.js`](./nordic.atlas-nodes.0023.101d89a4e69a50ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.91e829fded707f47.js`](./nordic.atlas-nodes.0024.91e829fded707f47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.f523368c0db04c08.js`](./nordic.atlas-nodes.0025.f523368c0db04c08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.84bdd6b667006476.js`](./nordic.atlas-nodes.0026.84bdd6b667006476.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.de0f5c56b12d873f.js`](./nordic.atlas-nodes.0027.de0f5c56b12d873f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.53e3b66b8f0ad3fa.js`](./nordic.atlas-nodes.0028.53e3b66b8f0ad3fa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.66c063cd217fc9b7.js`](./nordic.atlas-nodes.0029.66c063cd217fc9b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.e7204f51f916364d.js`](./nordic.atlas-nodes.0030.e7204f51f916364d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.2aadb48fcfa656f8.js`](./nordic.atlas-nodes.0031.2aadb48fcfa656f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.77e43bc7a50df339.js`](./nordic.atlas-nodes.0032.77e43bc7a50df339.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.c9550d8e8c95fbba.js`](./nordic.atlas-nodes.0033.c9550d8e8c95fbba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.251dceb3e971c2e2.js`](./nordic.atlas-nodes.0034.251dceb3e971c2e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.a79d45cb6912974e.js`](./nordic.atlas-nodes.0035.a79d45cb6912974e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.81c17b3e10c13161.js`](./nordic.atlas-nodes.0036.81c17b3e10c13161.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.9a844334f3be7de3.js`](./nordic.atlas-nodes.0037.9a844334f3be7de3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.3af1b3d4004accbb.js`](./nordic.atlas-nodes.0038.3af1b3d4004accbb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.db78ef14cef5c941.js`](./nordic.atlas-nodes.0039.db78ef14cef5c941.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.d62357cba5a0597a.js`](./nordic.atlas-nodes.0040.d62357cba5a0597a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.a0237bea5209f8a3.js`](./nordic.atlas-nodes.0041.a0237bea5209f8a3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.c8d27fff66c36b78.js`](./nordic.atlas-nodes.0042.c8d27fff66c36b78.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.896b61ad4fa280c1.js`](./nordic.atlas-nodes.0043.896b61ad4fa280c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.0d4dc55b5e8de1d8.js`](./nordic.atlas-nodes.0044.0d4dc55b5e8de1d8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.9d402c9bcd30da23.js`](./nordic.atlas-nodes.0045.9d402c9bcd30da23.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.53152618cefc99b6.js`](./nordic.atlas-nodes.0046.53152618cefc99b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.2ca8eb348c14e709.js`](./nordic.atlas-nodes.0047.2ca8eb348c14e709.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.c12a28cf9bea3e42.js`](./nordic.atlas-nodes.0048.c12a28cf9bea3e42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.98b3133b5ae79d6b.js`](./nordic.atlas-nodes.0049.98b3133b5ae79d6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.75ba4302b59ee740.js`](./nordic.atlas-nodes.0050.75ba4302b59ee740.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.5f6676faeaeb4924.js`](./nordic.atlas-nodes.0051.5f6676faeaeb4924.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.21b31b4f6f98d036.js`](./nordic.atlas-nodes.0052.21b31b4f6f98d036.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.df93a1dbcfb3cbe4.js`](./nordic.atlas-nodes.0053.df93a1dbcfb3cbe4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.5297e9f3d5baa676.js`](./nordic.atlas-nodes.0054.5297e9f3d5baa676.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.101d497a1be759d7.js`](./nordic.atlas-nodes.0055.101d497a1be759d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.0be8c96aa8b13b43.js`](./nordic.atlas-nodes.0056.0be8c96aa8b13b43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.fd38b2d368966767.js`](./nordic.atlas-nodes.0057.fd38b2d368966767.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.8650db1ba23f1ea9.js`](./nordic.atlas-nodes.0058.8650db1ba23f1ea9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.43238f0efe63d1c5.js`](./nordic.atlas-nodes.0059.43238f0efe63d1c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.0bf470aeb73bd3c7.js`](./nordic.atlas-nodes.0060.0bf470aeb73bd3c7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.7eaeb05f10fa17b8.js`](./nordic.atlas-nodes.0061.7eaeb05f10fa17b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.131dacc955d29c25.js`](./nordic.atlas-nodes.0062.131dacc955d29c25.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.2742bfe766ac8216.js`](./nordic.atlas-nodes.0063.2742bfe766ac8216.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.5e1a3ffa6baa1009.js`](./nordic.atlas-nodes.0064.5e1a3ffa6baa1009.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.9ed66d7c8d818c4f.js`](./nordic.atlas-nodes.0065.9ed66d7c8d818c4f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.764c3739d2b8b05b.js`](./nordic.atlas-nodes.0066.764c3739d2b8b05b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.9a5789b6f60201d8.js`](./nordic.atlas-nodes.0067.9a5789b6f60201d8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.484539e5216c489a.js`](./nordic.atlas-nodes.0068.484539e5216c489a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.f58a1cc5f10ba1ba.js`](./nordic.atlas-nodes.0069.f58a1cc5f10ba1ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.7e365924909f8cfb.js`](./nordic.atlas-nodes.0070.7e365924909f8cfb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.69f2e550768ab249.js`](./nordic.atlas-nodes.0071.69f2e550768ab249.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.33a32f80ceb98b3e.js`](./nordic.atlas-nodes.0072.33a32f80ceb98b3e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.4fbdb0ce3204eebc.js`](./nordic.atlas-nodes.0073.4fbdb0ce3204eebc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.893aa99700626c96.js`](./nordic.atlas-nodes.0074.893aa99700626c96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.c5c428771371f089.js`](./nordic.atlas-nodes.0075.c5c428771371f089.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.e2b83efec9dcfa31.js`](./nordic.atlas-nodes.0076.e2b83efec9dcfa31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.9024f40713269388.js`](./nordic.atlas-nodes.0077.9024f40713269388.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.a1714a97a4a4af31.js`](./nordic.atlas-nodes.0078.a1714a97a4a4af31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.2bb1ddcaa9f3c18e.js`](./nordic.atlas-nodes.0079.2bb1ddcaa9f3c18e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.f416ca946481855d.js`](./nordic.atlas-nodes.0080.f416ca946481855d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.240a7c744a534158.js`](./nordic.atlas-nodes.0081.240a7c744a534158.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.5208dcdbebc65309.js`](./nordic.atlas-nodes.0082.5208dcdbebc65309.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.2a4a764a38e957ff.js`](./nordic.atlas-nodes.0083.2a4a764a38e957ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.73801b7199c2a3b3.js`](./nordic.atlas-nodes.0084.73801b7199c2a3b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.0c9adbaf9e54f2cf.js`](./nordic.atlas-nodes.0085.0c9adbaf9e54f2cf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.a94c81870364a065.js`](./nordic.atlas-nodes.0086.a94c81870364a065.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.426dc7642a6ceb7e.js`](./nordic.atlas-nodes.0087.426dc7642a6ceb7e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.edae2db4a2e26233.js`](./nordic.atlas-nodes.0088.edae2db4a2e26233.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.6a0fbdc41924845b.js`](./nordic.atlas-nodes.0089.6a0fbdc41924845b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.6f76f8ec7d26f762.js`](./nordic.atlas-nodes.0090.6f76f8ec7d26f762.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.a09954e23f1ad181.js`](./nordic.atlas-nodes.0091.a09954e23f1ad181.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.881a3afb100c9108.js`](./nordic.atlas-nodes.0092.881a3afb100c9108.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.f8d3c1dc3af89b20.js`](./nordic.atlas-nodes.0093.f8d3c1dc3af89b20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.029bc1ad74fc2a71.js`](./nordic.atlas-nodes.0094.029bc1ad74fc2a71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.c2d7dbb26001576c.js`](./nordic.atlas-nodes.0095.c2d7dbb26001576c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.043e8980712a858a.js`](./nordic.atlas-nodes.0096.043e8980712a858a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.e190ead82b88cf16.js`](./nordic.atlas-nodes.0097.e190ead82b88cf16.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.632d544e58f5104f.js`](./nordic.atlas-nodes.0098.632d544e58f5104f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.9bdeaf20ef2fe19f.js`](./nordic.atlas-nodes.0099.9bdeaf20ef2fe19f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.0e5f8b20172d1cf8.js`](./nordic.atlas-nodes.0100.0e5f8b20172d1cf8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.56145d9f74a62c42.js`](./nordic.atlas-nodes.0101.56145d9f74a62c42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.83d12171dac2e7e8.js`](./nordic.atlas-nodes.0102.83d12171dac2e7e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.11371c88ef446676.js`](./nordic.atlas-nodes.0103.11371c88ef446676.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.a385039b24f75227.js`](./nordic.atlas-nodes.0104.a385039b24f75227.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.d2e25ae05ba4961a.js`](./nordic.atlas-nodes.0105.d2e25ae05ba4961a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.cf0d555cba54045e.js`](./nordic.atlas-nodes.0106.cf0d555cba54045e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.ef6fff2b593c1b37.js`](./nordic.atlas-nodes.0107.ef6fff2b593c1b37.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.75874143f9907d4b.js`](./nordic.atlas-nodes.0108.75874143f9907d4b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.04a3982e7fd69157.js`](./nordic.atlas-nodes.0109.04a3982e7fd69157.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.d218e56aa830a734.js`](./nordic.atlas-nodes.0110.d218e56aa830a734.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.8a59d32f3d13f586.js`](./nordic.atlas-nodes.0111.8a59d32f3d13f586.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.12bb8b981a4e399f.js`](./nordic.atlas-nodes.0112.12bb8b981a4e399f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.65c43fd69b5eb1b1.js`](./nordic.atlas-nodes.0113.65c43fd69b5eb1b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.073b9a3db9761f20.js`](./nordic.atlas-nodes.0114.073b9a3db9761f20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.2c4c557c19d7c515.js`](./nordic.atlas-nodes.0115.2c4c557c19d7c515.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.76e0c885631d92a9.js`](./nordic.atlas-nodes.0116.76e0c885631d92a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.3d0f09a1e775420f.js`](./nordic.atlas-nodes.0117.3d0f09a1e775420f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.566dd930d8c3313c.js`](./nordic.atlas-nodes.0118.566dd930d8c3313c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.3efe7f1fe19ef6b7.js`](./nordic.atlas-nodes.0119.3efe7f1fe19ef6b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.459af8e86cf8f9e8.js`](./nordic.atlas-nodes.0120.459af8e86cf8f9e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.031283829ff607fe.js`](./nordic.atlas-nodes.0121.031283829ff607fe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.2d4f6b8486732b0c.js`](./nordic.atlas-nodes.0122.2d4f6b8486732b0c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.b69a98854f5cde93.js`](./nordic.atlas-nodes.0123.b69a98854f5cde93.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.f22883eae57d3f33.js`](./nordic.atlas-nodes.0124.f22883eae57d3f33.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.0f17b926e386cca7.js`](./nordic.atlas-nodes.0125.0f17b926e386cca7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.902b9a912a2115f1.js`](./nordic.atlas-nodes.0126.902b9a912a2115f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.b2229498febda4e5.js`](./nordic.atlas-nodes.0127.b2229498febda4e5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.f0e06604055306d0.js`](./nordic.atlas-nodes.0128.f0e06604055306d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.809dff13e5798745.js`](./nordic.atlas-nodes.0129.809dff13e5798745.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.ba7dacf81b77f7b1.js`](./nordic.atlas-nodes.0130.ba7dacf81b77f7b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.577e1f63e864fdc7.js`](./nordic.atlas-nodes.0131.577e1f63e864fdc7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.32b7caaacba6444a.js`](./nordic.atlas-nodes.0132.32b7caaacba6444a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.7b38a4b29ef8f953.js`](./nordic.atlas-nodes.0133.7b38a4b29ef8f953.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.0d7eff23f199fec3.js`](./nordic.atlas-nodes.0134.0d7eff23f199fec3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.cd6abab53df9a7e3.js`](./nordic.atlas-nodes.0135.cd6abab53df9a7e3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.6a5d7a7557d51569.js`](./nordic.atlas-nodes.0136.6a5d7a7557d51569.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.3bc5c8271237ee4a.js`](./nordic.atlas-nodes.0137.3bc5c8271237ee4a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.7a53a71ba9d7814a.js`](./nordic.atlas-nodes.0138.7a53a71ba9d7814a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.4f5b9d6228643718.js`](./nordic.atlas-nodes.0139.4f5b9d6228643718.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.5772e5f0a172a1dd.js`](./nordic.atlas-nodes.0140.5772e5f0a172a1dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.5f167867b45270a4.js`](./nordic.atlas-nodes.0141.5f167867b45270a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.2b2e3d1484ad6056.js`](./nordic.atlas-nodes.0142.2b2e3d1484ad6056.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.35825c09d87e7750.js`](./nordic.atlas-nodes.0143.35825c09d87e7750.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.f7f8adbf70aaf367.js`](./nordic.atlas-nodes.0144.f7f8adbf70aaf367.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.c6d5ac7d15663f8b.js`](./nordic.atlas-nodes.0145.c6d5ac7d15663f8b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.1149efde4cdcac62.js`](./nordic.atlas-nodes.0146.1149efde4cdcac62.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.ee068772fc3b64bd.js`](./nordic.atlas-nodes.0147.ee068772fc3b64bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.e30c6e57250dcfae.js`](./nordic.atlas-nodes.0148.e30c6e57250dcfae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.874ed61e291703ff.js`](./nordic.atlas-nodes.0149.874ed61e291703ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.4419f17f0fd62c8f.js`](./nordic.atlas-nodes.0150.4419f17f0fd62c8f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.0ff5cfecdd7cca3c.js`](./nordic.atlas-nodes.0151.0ff5cfecdd7cca3c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.503eb149e2ed72ad.js`](./nordic.atlas-nodes.0152.503eb149e2ed72ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.61d4871b2393846a.js`](./nordic.atlas-nodes.0153.61d4871b2393846a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.a329d4b47f4efcd7.js`](./nordic.atlas-nodes.0154.a329d4b47f4efcd7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.affd74b7f1725e8c.js`](./nordic.atlas-nodes.0155.affd74b7f1725e8c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.88401af6ec81ccc1.js`](./nordic.atlas-nodes.0156.88401af6ec81ccc1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.9bf2feb78f6b7779.js`](./nordic.atlas-nodes.0157.9bf2feb78f6b7779.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.65dda45b0a4cfb65.js`](./nordic.atlas-nodes.0158.65dda45b0a4cfb65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.a0a21099f786c9f3.js`](./nordic.atlas-nodes.0159.a0a21099f786c9f3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.13b459e534be06c2.js`](./nordic.atlas-nodes.0160.13b459e534be06c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.92279e6c78e6d8b4.js`](./nordic.atlas-nodes.0161.92279e6c78e6d8b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.31275507a537fa19.js`](./nordic.atlas-nodes.0162.31275507a537fa19.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.cce78d70d6d4945b.js`](./nordic.atlas-nodes.0163.cce78d70d6d4945b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.6e0bf56dee1a13a5.js`](./nordic.atlas-nodes.0164.6e0bf56dee1a13a5.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.563ecff5b8e325c6.js`](./nordic.atlas-details.0165.563ecff5b8e325c6.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.e85ad71c87e464e4.js`](./nordic.atlas-details.0166.e85ad71c87e464e4.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.aed8af1683a63fe2.js`](./nordic.atlas-details.0167.aed8af1683a63fe2.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.faff3566747e3f87.js`](./nordic.atlas-details.0168.faff3566747e3f87.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.939fdec43c093ea2.js`](./nordic.atlas-details.0169.939fdec43c093ea2.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.6634d86c624dadb4.js`](./nordic.atlas-details.0170.6634d86c624dadb4.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.c141edbca3494c91.js`](./nordic.atlas-details.0171.c141edbca3494c91.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.3fcd9f033c846fb9.js`](./nordic.atlas-details.0172.3fcd9f033c846fb9.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.58f93b2d8711234b.js`](./nordic.atlas-details.0173.58f93b2d8711234b.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.cdb76cb5c1abf10c.js`](./nordic.atlas-details.0174.cdb76cb5c1abf10c.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.b97dd0c07033660a.js`](./nordic.atlas-details.0175.b97dd0c07033660a.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.7e30b4f93e840336.js`](./nordic.atlas-details.0176.7e30b4f93e840336.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.de8599918d16a375.js`](./nordic.atlas-details.0177.de8599918d16a375.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.3a57783e501719e8.js`](./nordic.atlas-details.0178.3a57783e501719e8.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.885ade7071ef2242.js`](./nordic.atlas-details.0179.885ade7071ef2242.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.7beb385a54572fae.js`](./nordic.atlas-details.0180.7beb385a54572fae.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.2f5f2e1ceefee99a.js`](./nordic.atlas-details.0181.2f5f2e1ceefee99a.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.ceaf7ce4b1526f02.js`](./nordic.atlas-details.0182.ceaf7ce4b1526f02.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.b63bd718facb5e38.js`](./nordic.atlas-details.0183.b63bd718facb5e38.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.a24cc50729e4e56b.js`](./nordic.atlas-details.0184.a24cc50729e4e56b.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.7b576b62db37f443.js`](./nordic.atlas-details.0185.7b576b62db37f443.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.d6208576ba32b8be.js`](./nordic.atlas-details.0186.d6208576ba32b8be.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.344a1ccd9019ae14.js`](./nordic.atlas-details.0187.344a1ccd9019ae14.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.f5bf0b21b25889c6.js`](./nordic.atlas-details.0188.f5bf0b21b25889c6.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.5d33350a3bcc70f3.js`](./nordic.atlas-details.0189.5d33350a3bcc70f3.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.4a1e0c6a055fdaae.js`](./nordic.atlas-details.0190.4a1e0c6a055fdaae.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.784fd426d4367897.js`](./nordic.atlas-details.0191.784fd426d4367897.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.8c7710420b4e83ff.js`](./nordic.atlas-details.0192.8c7710420b4e83ff.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.5ae49d383c500dee.js`](./nordic.atlas-details.0193.5ae49d383c500dee.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.6d1edb993c9e3325.js`](./nordic.atlas-details.0194.6d1edb993c9e3325.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.557769a1bc062596.js`](./nordic.atlas-details.0195.557769a1bc062596.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.32e3ef6ed8ffd44d.js`](./nordic.atlas-details.0196.32e3ef6ed8ffd44d.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.8c399fb2da6802e1.js`](./nordic.atlas-details.0197.8c399fb2da6802e1.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.df5465b5886a47ea.js`](./nordic.atlas-details.0198.df5465b5886a47ea.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.9053e687cf74e1e5.js`](./nordic.atlas-details.0199.9053e687cf74e1e5.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.b5d25de5db8d926a.js`](./nordic.atlas-details.0200.b5d25de5db8d926a.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.69201acb0037bdf0.js`](./nordic.atlas-details.0201.69201acb0037bdf0.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.4f23bf9587847670.js`](./nordic.atlas-details.0202.4f23bf9587847670.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.d0a30b439f1245b5.js`](./nordic.atlas-details.0203.d0a30b439f1245b5.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.312b9ce51b1c934b.js`](./nordic.atlas-details.0204.312b9ce51b1c934b.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.2cee24d8378ce659.js`](./nordic.atlas-details.0205.2cee24d8378ce659.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.d9a730b6b186e6a3.js`](./nordic.atlas-details.0206.d9a730b6b186e6a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.8f74b0def14ddf4c.js`](./nordic.atlas-details.0207.8f74b0def14ddf4c.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.095c1fc6341d4bae.js`](./nordic.atlas-details.0208.095c1fc6341d4bae.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.54dfa860359c880a.js`](./nordic.atlas-details.0209.54dfa860359c880a.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.4335a879330c439c.js`](./nordic.atlas-details.0210.4335a879330c439c.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.441524a5f0fb9ea5.js`](./nordic.atlas-details.0211.441524a5f0fb9ea5.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.30a3deea89b7a055.js`](./nordic.atlas-details.0212.30a3deea89b7a055.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.23c9ffd64075fd65.js`](./nordic.atlas-details.0213.23c9ffd64075fd65.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.33166f16dbf4bf26.js`](./nordic.atlas-details.0214.33166f16dbf4bf26.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.bfc41ba8d965bf2d.js`](./nordic.atlas-details.0215.bfc41ba8d965bf2d.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.b7b89c4c11617154.js`](./nordic.atlas-details.0216.b7b89c4c11617154.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.a81d082e40639814.js`](./nordic.atlas-details.0217.a81d082e40639814.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.7947828cc019672e.js`](./nordic.atlas-details.0218.7947828cc019672e.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.fa6354fe78a2bd72.js`](./nordic.atlas-details.0219.fa6354fe78a2bd72.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.3f736c96d5a5901e.js`](./nordic.atlas-details.0220.3f736c96d5a5901e.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.2b6155b1cfba8bb3.js`](./nordic.atlas-details.0221.2b6155b1cfba8bb3.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.a194d2a8a1b25da2.js`](./nordic.atlas-details.0222.a194d2a8a1b25da2.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.26bf2619a3b4854c.js`](./nordic.atlas-details.0223.26bf2619a3b4854c.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.3e392f42e1e1dabe.js`](./nordic.atlas-details.0224.3e392f42e1e1dabe.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.a3f1c8a51f6af3e3.js`](./nordic.atlas-details.0225.a3f1c8a51f6af3e3.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.ba81f23eb7300e50.js`](./nordic.atlas-details.0226.ba81f23eb7300e50.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.fc0e087f09e52701.js`](./nordic.atlas-details.0227.fc0e087f09e52701.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.375cf78802c6aea7.js`](./nordic.atlas-details.0228.375cf78802c6aea7.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.07d49d6264aa7574.js`](./nordic.atlas-edges.0229.07d49d6264aa7574.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.30bd8868f878d295.js`](./nordic.atlas-sequences.0230.30bd8868f878d295.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.3eb2068ae24e43ed.js`](./nordic.atlas-indexes.0231.3eb2068ae24e43ed.js)
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


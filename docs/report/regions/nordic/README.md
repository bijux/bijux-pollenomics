# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-29` from Homo
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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.06c399b9eb416c75.js`](./nordic.atlas-provenance.0000.06c399b9eb416c75.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.8a0e2b1a5005eb83.js`](./nordic.atlas-nodes.0001.8a0e2b1a5005eb83.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.478cdfc0c05c1549.js`](./nordic.atlas-nodes.0002.478cdfc0c05c1549.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.7f63e2b0c617859d.js`](./nordic.atlas-nodes.0003.7f63e2b0c617859d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.03577d85f6e78b36.js`](./nordic.atlas-nodes.0004.03577d85f6e78b36.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.a2cb54ce0991e2bc.js`](./nordic.atlas-nodes.0005.a2cb54ce0991e2bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.7eb19e5bc354081d.js`](./nordic.atlas-nodes.0006.7eb19e5bc354081d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.999b6af1955cc075.js`](./nordic.atlas-nodes.0007.999b6af1955cc075.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.e7dac3c1499c042b.js`](./nordic.atlas-nodes.0008.e7dac3c1499c042b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.ded63832ba8f8527.js`](./nordic.atlas-nodes.0009.ded63832ba8f8527.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.cb1cfa6ca01703d7.js`](./nordic.atlas-nodes.0010.cb1cfa6ca01703d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.568cc86fbd6d766b.js`](./nordic.atlas-nodes.0011.568cc86fbd6d766b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.be7c91f190a96a2c.js`](./nordic.atlas-nodes.0012.be7c91f190a96a2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.3c388d69a96aca66.js`](./nordic.atlas-nodes.0013.3c388d69a96aca66.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.ac1446054a4fe63d.js`](./nordic.atlas-nodes.0014.ac1446054a4fe63d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.787aaa06663eec2b.js`](./nordic.atlas-nodes.0015.787aaa06663eec2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.3e6da6f29f838c72.js`](./nordic.atlas-nodes.0016.3e6da6f29f838c72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.484db697e8247ae4.js`](./nordic.atlas-nodes.0017.484db697e8247ae4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.ec43d82e3cad977d.js`](./nordic.atlas-nodes.0018.ec43d82e3cad977d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.057f054af9b444fb.js`](./nordic.atlas-nodes.0019.057f054af9b444fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.60fbed024d253672.js`](./nordic.atlas-nodes.0020.60fbed024d253672.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.92b6e8ed87ea6b2d.js`](./nordic.atlas-nodes.0021.92b6e8ed87ea6b2d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.26503fbd1483b296.js`](./nordic.atlas-nodes.0022.26503fbd1483b296.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.bc1489cb04bb13ba.js`](./nordic.atlas-nodes.0023.bc1489cb04bb13ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.3569b70b33851e1c.js`](./nordic.atlas-nodes.0024.3569b70b33851e1c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.77dcbf312d5bdbac.js`](./nordic.atlas-nodes.0025.77dcbf312d5bdbac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.d99e91d5278b097d.js`](./nordic.atlas-nodes.0026.d99e91d5278b097d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.a56793fac6053f62.js`](./nordic.atlas-nodes.0027.a56793fac6053f62.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.b591353c2062ba94.js`](./nordic.atlas-nodes.0028.b591353c2062ba94.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.82b115fc76f95f7e.js`](./nordic.atlas-nodes.0029.82b115fc76f95f7e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.334d99d2eabe093a.js`](./nordic.atlas-nodes.0030.334d99d2eabe093a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.eaaac18963d7b539.js`](./nordic.atlas-nodes.0031.eaaac18963d7b539.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.72f5e8af1e4a7e65.js`](./nordic.atlas-nodes.0032.72f5e8af1e4a7e65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.d5bd7d3748ef6acb.js`](./nordic.atlas-nodes.0033.d5bd7d3748ef6acb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.cfcc56ef86fe57f0.js`](./nordic.atlas-nodes.0034.cfcc56ef86fe57f0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.9602dde435ce1290.js`](./nordic.atlas-nodes.0035.9602dde435ce1290.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.8d6b68e1cf392606.js`](./nordic.atlas-nodes.0036.8d6b68e1cf392606.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.1ec082a737a156c2.js`](./nordic.atlas-nodes.0037.1ec082a737a156c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.025b79bffa81ec21.js`](./nordic.atlas-nodes.0038.025b79bffa81ec21.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.6a463ede69318ab6.js`](./nordic.atlas-nodes.0039.6a463ede69318ab6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.bf0e8e52bbc58ba6.js`](./nordic.atlas-nodes.0040.bf0e8e52bbc58ba6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.0e86ec0608f3be96.js`](./nordic.atlas-nodes.0041.0e86ec0608f3be96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.87fd228f3bc4c552.js`](./nordic.atlas-nodes.0042.87fd228f3bc4c552.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.5e53fc43fce0b2ff.js`](./nordic.atlas-nodes.0043.5e53fc43fce0b2ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.7f77447999dbe1e2.js`](./nordic.atlas-nodes.0044.7f77447999dbe1e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.bd6b92dfa51c49ae.js`](./nordic.atlas-nodes.0045.bd6b92dfa51c49ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.45ae1580eadf33cb.js`](./nordic.atlas-nodes.0046.45ae1580eadf33cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.ded3a5b92b3e5470.js`](./nordic.atlas-nodes.0047.ded3a5b92b3e5470.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.4b6b6bd54f76d384.js`](./nordic.atlas-nodes.0048.4b6b6bd54f76d384.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.cd9ba6cb24ab6126.js`](./nordic.atlas-nodes.0049.cd9ba6cb24ab6126.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.edec78b82b27d29b.js`](./nordic.atlas-nodes.0050.edec78b82b27d29b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.f477e8510184fc1a.js`](./nordic.atlas-nodes.0051.f477e8510184fc1a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.84e5eb36af6775fa.js`](./nordic.atlas-nodes.0052.84e5eb36af6775fa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.f21e0d54302e6f2e.js`](./nordic.atlas-nodes.0053.f21e0d54302e6f2e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.2edfbf66495e4989.js`](./nordic.atlas-nodes.0054.2edfbf66495e4989.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.5be030bb4bf70fa7.js`](./nordic.atlas-nodes.0055.5be030bb4bf70fa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.24df2acae6957820.js`](./nordic.atlas-nodes.0056.24df2acae6957820.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.b35be96dfce30c2a.js`](./nordic.atlas-nodes.0057.b35be96dfce30c2a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.47d84ab5f5d51803.js`](./nordic.atlas-nodes.0058.47d84ab5f5d51803.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.61c25a8114b6041f.js`](./nordic.atlas-nodes.0059.61c25a8114b6041f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.296021b0ae07cf5f.js`](./nordic.atlas-nodes.0060.296021b0ae07cf5f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.857e89047d523b6e.js`](./nordic.atlas-nodes.0061.857e89047d523b6e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.008cda15d414139f.js`](./nordic.atlas-nodes.0062.008cda15d414139f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.b0a2a0998438d6b7.js`](./nordic.atlas-nodes.0063.b0a2a0998438d6b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.1f2f779b60efa769.js`](./nordic.atlas-nodes.0064.1f2f779b60efa769.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.8a9c06752c363225.js`](./nordic.atlas-nodes.0065.8a9c06752c363225.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.c7d5cad0342e0bba.js`](./nordic.atlas-nodes.0066.c7d5cad0342e0bba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.cc7fdbe2d09b130f.js`](./nordic.atlas-nodes.0067.cc7fdbe2d09b130f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.8470af5f4f94dbe8.js`](./nordic.atlas-nodes.0068.8470af5f4f94dbe8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.27b70ef50b0b7df8.js`](./nordic.atlas-nodes.0069.27b70ef50b0b7df8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.26e498c023154e35.js`](./nordic.atlas-nodes.0070.26e498c023154e35.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.dd4389ec34aaa3a1.js`](./nordic.atlas-nodes.0071.dd4389ec34aaa3a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.46d77968b6278f84.js`](./nordic.atlas-nodes.0072.46d77968b6278f84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.0162d9b624d68dde.js`](./nordic.atlas-nodes.0073.0162d9b624d68dde.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.97f4e749ed076d0f.js`](./nordic.atlas-nodes.0074.97f4e749ed076d0f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.febe590e8d33ed44.js`](./nordic.atlas-nodes.0075.febe590e8d33ed44.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.baad35467f79bc06.js`](./nordic.atlas-nodes.0076.baad35467f79bc06.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.9876529c6480b330.js`](./nordic.atlas-nodes.0077.9876529c6480b330.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.fa9539e7f689fae3.js`](./nordic.atlas-nodes.0078.fa9539e7f689fae3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.f09d128a6b15c344.js`](./nordic.atlas-nodes.0079.f09d128a6b15c344.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.6c9358a6681178c7.js`](./nordic.atlas-nodes.0080.6c9358a6681178c7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.fe4a76f63506e08a.js`](./nordic.atlas-nodes.0081.fe4a76f63506e08a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.6aaa2fdf5f3610bb.js`](./nordic.atlas-nodes.0082.6aaa2fdf5f3610bb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.fadaaee5b7f60bf8.js`](./nordic.atlas-nodes.0083.fadaaee5b7f60bf8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.2569c5cdc86b74a2.js`](./nordic.atlas-nodes.0084.2569c5cdc86b74a2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.5f205418c82a2bdf.js`](./nordic.atlas-nodes.0085.5f205418c82a2bdf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.086432ab0c508dc2.js`](./nordic.atlas-nodes.0086.086432ab0c508dc2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.fe70c5800e504bc3.js`](./nordic.atlas-nodes.0087.fe70c5800e504bc3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.8933a16029f5956d.js`](./nordic.atlas-nodes.0088.8933a16029f5956d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.11359687f4ee54a2.js`](./nordic.atlas-nodes.0089.11359687f4ee54a2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.e04c0d688b744345.js`](./nordic.atlas-nodes.0090.e04c0d688b744345.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.5f4902aff477031a.js`](./nordic.atlas-nodes.0091.5f4902aff477031a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.fb1f60e75bd4cc59.js`](./nordic.atlas-nodes.0092.fb1f60e75bd4cc59.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.3175348722174ffe.js`](./nordic.atlas-nodes.0093.3175348722174ffe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.ddb0dd32b214f918.js`](./nordic.atlas-nodes.0094.ddb0dd32b214f918.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.ceb4a28380590f2e.js`](./nordic.atlas-nodes.0095.ceb4a28380590f2e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.058d7c3facefdbe7.js`](./nordic.atlas-nodes.0096.058d7c3facefdbe7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.8c0d6dc315f99190.js`](./nordic.atlas-nodes.0097.8c0d6dc315f99190.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.1daf5c1ea2d390cb.js`](./nordic.atlas-nodes.0098.1daf5c1ea2d390cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.3b83ab3c93cb18b3.js`](./nordic.atlas-nodes.0099.3b83ab3c93cb18b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.48b467fc35eb5926.js`](./nordic.atlas-nodes.0100.48b467fc35eb5926.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.a771f81c7477ca33.js`](./nordic.atlas-nodes.0101.a771f81c7477ca33.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.332892fb8afdeb33.js`](./nordic.atlas-nodes.0102.332892fb8afdeb33.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.ac9e1cc64222e95b.js`](./nordic.atlas-nodes.0103.ac9e1cc64222e95b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.03730eb2d879bfdd.js`](./nordic.atlas-nodes.0104.03730eb2d879bfdd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.2ffc7cad80d2b938.js`](./nordic.atlas-nodes.0105.2ffc7cad80d2b938.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.807f4479851b0af5.js`](./nordic.atlas-nodes.0106.807f4479851b0af5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.62e559a44f8e3dc1.js`](./nordic.atlas-nodes.0107.62e559a44f8e3dc1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.a9fb46061f587e3a.js`](./nordic.atlas-nodes.0108.a9fb46061f587e3a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.68c633d1b5cb7b2a.js`](./nordic.atlas-nodes.0109.68c633d1b5cb7b2a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.c868ed6280699303.js`](./nordic.atlas-nodes.0110.c868ed6280699303.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.1ba9463acb980fc3.js`](./nordic.atlas-nodes.0111.1ba9463acb980fc3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.1d050c03d226cc5a.js`](./nordic.atlas-nodes.0112.1d050c03d226cc5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.02f2e8a96524ad11.js`](./nordic.atlas-nodes.0113.02f2e8a96524ad11.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.12d9e1e00d5f41d1.js`](./nordic.atlas-nodes.0114.12d9e1e00d5f41d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.4176fcd43d048ba9.js`](./nordic.atlas-nodes.0115.4176fcd43d048ba9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.bbba2064153f425d.js`](./nordic.atlas-nodes.0116.bbba2064153f425d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.ea6c1cdb935165df.js`](./nordic.atlas-nodes.0117.ea6c1cdb935165df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.9efa46a7b927f2f2.js`](./nordic.atlas-nodes.0118.9efa46a7b927f2f2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.fba2db1184afee1b.js`](./nordic.atlas-nodes.0119.fba2db1184afee1b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.18c094e337250151.js`](./nordic.atlas-nodes.0120.18c094e337250151.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.0a07df36008ede81.js`](./nordic.atlas-nodes.0121.0a07df36008ede81.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.87b88ebbfc529abb.js`](./nordic.atlas-nodes.0122.87b88ebbfc529abb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.c36b7c5bd68219f1.js`](./nordic.atlas-nodes.0123.c36b7c5bd68219f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.0aae47b49d9bb307.js`](./nordic.atlas-nodes.0124.0aae47b49d9bb307.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.60b198d93e7d325c.js`](./nordic.atlas-nodes.0125.60b198d93e7d325c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.1581c381f414901d.js`](./nordic.atlas-nodes.0126.1581c381f414901d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.9cca12c5878f878c.js`](./nordic.atlas-nodes.0127.9cca12c5878f878c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.164df7436191d3e0.js`](./nordic.atlas-nodes.0128.164df7436191d3e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.34d50cb2ee192e49.js`](./nordic.atlas-nodes.0129.34d50cb2ee192e49.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.d61e4aae5cdb13c5.js`](./nordic.atlas-nodes.0130.d61e4aae5cdb13c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.f087cb525bf3cc8a.js`](./nordic.atlas-nodes.0131.f087cb525bf3cc8a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.ae9f7e0a0450d46b.js`](./nordic.atlas-nodes.0132.ae9f7e0a0450d46b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.3f2c68e4e50c5cdb.js`](./nordic.atlas-nodes.0133.3f2c68e4e50c5cdb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.066102070c4e5471.js`](./nordic.atlas-nodes.0134.066102070c4e5471.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.b5f23dd6c3606c55.js`](./nordic.atlas-nodes.0135.b5f23dd6c3606c55.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.0ce0f6c3ec5daa6e.js`](./nordic.atlas-nodes.0136.0ce0f6c3ec5daa6e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.20da8416f44c0e95.js`](./nordic.atlas-nodes.0137.20da8416f44c0e95.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.2059dcd49d5862f3.js`](./nordic.atlas-nodes.0138.2059dcd49d5862f3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.fff8b30f3b2e9b23.js`](./nordic.atlas-nodes.0139.fff8b30f3b2e9b23.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.beb14f0b9f288b40.js`](./nordic.atlas-nodes.0140.beb14f0b9f288b40.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.339a270d6d5819e4.js`](./nordic.atlas-nodes.0141.339a270d6d5819e4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.f29a98a286e3e5ca.js`](./nordic.atlas-nodes.0142.f29a98a286e3e5ca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.4852f144f8f0f051.js`](./nordic.atlas-nodes.0143.4852f144f8f0f051.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.30d1b9e84aebbb9a.js`](./nordic.atlas-nodes.0144.30d1b9e84aebbb9a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.52f6f13be4dc72b3.js`](./nordic.atlas-nodes.0145.52f6f13be4dc72b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.67d304c68a242cd6.js`](./nordic.atlas-nodes.0146.67d304c68a242cd6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.15a853ce8244e540.js`](./nordic.atlas-nodes.0147.15a853ce8244e540.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.21ebdeff6840e786.js`](./nordic.atlas-nodes.0148.21ebdeff6840e786.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.d275f0117d6d902c.js`](./nordic.atlas-nodes.0149.d275f0117d6d902c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.dcdecd6dd1d50ea3.js`](./nordic.atlas-nodes.0150.dcdecd6dd1d50ea3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.87fa1e2997a2eaa7.js`](./nordic.atlas-nodes.0151.87fa1e2997a2eaa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.5651b2e4ff9ab90b.js`](./nordic.atlas-nodes.0152.5651b2e4ff9ab90b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.a62611565e8f0a55.js`](./nordic.atlas-nodes.0153.a62611565e8f0a55.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.3632de6b679ae0bb.js`](./nordic.atlas-nodes.0154.3632de6b679ae0bb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.5d23f8dbe5406f8d.js`](./nordic.atlas-nodes.0155.5d23f8dbe5406f8d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.052405fd90e6eb54.js`](./nordic.atlas-nodes.0156.052405fd90e6eb54.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.83f48b321f46b968.js`](./nordic.atlas-nodes.0157.83f48b321f46b968.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.35bab5eb754c1827.js`](./nordic.atlas-nodes.0158.35bab5eb754c1827.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.19a3a7d9db56f1e0.js`](./nordic.atlas-nodes.0159.19a3a7d9db56f1e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.b3424eefc45d49f1.js`](./nordic.atlas-nodes.0160.b3424eefc45d49f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.774a53d43cae788d.js`](./nordic.atlas-nodes.0161.774a53d43cae788d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.177dd6a3869bc753.js`](./nordic.atlas-nodes.0162.177dd6a3869bc753.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.cf90cf5d778788a8.js`](./nordic.atlas-nodes.0163.cf90cf5d778788a8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.141e19497aadfb45.js`](./nordic.atlas-nodes.0164.141e19497aadfb45.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.ea892ce501351419.js`](./nordic.atlas-nodes.0165.ea892ce501351419.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.f7521fc86823ed5b.js`](./nordic.atlas-nodes.0166.f7521fc86823ed5b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.00cc42f6846283c9.js`](./nordic.atlas-nodes.0167.00cc42f6846283c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.236dda785e1009eb.js`](./nordic.atlas-nodes.0168.236dda785e1009eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.256f39eebedf5d7c.js`](./nordic.atlas-nodes.0169.256f39eebedf5d7c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.43ad9fc90c16c989.js`](./nordic.atlas-nodes.0170.43ad9fc90c16c989.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.da3dde265258528d.js`](./nordic.atlas-details.0171.da3dde265258528d.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.c5658d08b90bbcc7.js`](./nordic.atlas-details.0172.c5658d08b90bbcc7.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.ac798029e3ff4be0.js`](./nordic.atlas-details.0173.ac798029e3ff4be0.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.24bb0ebd82ab0773.js`](./nordic.atlas-details.0174.24bb0ebd82ab0773.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.d5a2d12991254cbb.js`](./nordic.atlas-details.0175.d5a2d12991254cbb.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.b444284416da6bd1.js`](./nordic.atlas-details.0176.b444284416da6bd1.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.872fc38d0a3fa0de.js`](./nordic.atlas-details.0177.872fc38d0a3fa0de.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.3d7ab12ac38322d9.js`](./nordic.atlas-details.0178.3d7ab12ac38322d9.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.6f6c9eba5d085e3d.js`](./nordic.atlas-details.0179.6f6c9eba5d085e3d.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.4216c656edae3419.js`](./nordic.atlas-details.0180.4216c656edae3419.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.5c2ef8aac6366e0e.js`](./nordic.atlas-details.0181.5c2ef8aac6366e0e.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.f40cae4df0468493.js`](./nordic.atlas-details.0182.f40cae4df0468493.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.e8ad021376c42444.js`](./nordic.atlas-details.0183.e8ad021376c42444.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.633dd32a2ead6210.js`](./nordic.atlas-details.0184.633dd32a2ead6210.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.4516c34fe3d341b7.js`](./nordic.atlas-details.0185.4516c34fe3d341b7.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.96d115608635e230.js`](./nordic.atlas-details.0186.96d115608635e230.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.47b85ef72fe85f14.js`](./nordic.atlas-details.0187.47b85ef72fe85f14.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.c333d6b06ef8c6ff.js`](./nordic.atlas-details.0188.c333d6b06ef8c6ff.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.b3badfc0b9b94e8e.js`](./nordic.atlas-details.0189.b3badfc0b9b94e8e.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.105c846b513fe36c.js`](./nordic.atlas-details.0190.105c846b513fe36c.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.1701cec62c6c24d6.js`](./nordic.atlas-details.0191.1701cec62c6c24d6.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.183fa02abea29bff.js`](./nordic.atlas-details.0192.183fa02abea29bff.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.e0e2a9a9fb79bde1.js`](./nordic.atlas-details.0193.e0e2a9a9fb79bde1.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.25bdec00a38caa42.js`](./nordic.atlas-details.0194.25bdec00a38caa42.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.3442aa5919b6e753.js`](./nordic.atlas-details.0195.3442aa5919b6e753.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.9ce133b516b1aa0b.js`](./nordic.atlas-details.0196.9ce133b516b1aa0b.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.87bc72d1b33a1416.js`](./nordic.atlas-details.0197.87bc72d1b33a1416.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.927a6ca41ed25499.js`](./nordic.atlas-details.0198.927a6ca41ed25499.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.b9758526769084d1.js`](./nordic.atlas-details.0199.b9758526769084d1.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.6f72016c28eb270f.js`](./nordic.atlas-details.0200.6f72016c28eb270f.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.fc82180e199efd31.js`](./nordic.atlas-details.0201.fc82180e199efd31.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.c151df7b89e81b47.js`](./nordic.atlas-details.0202.c151df7b89e81b47.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.e4f26322141fd393.js`](./nordic.atlas-details.0203.e4f26322141fd393.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.2ec59d5986fb673e.js`](./nordic.atlas-details.0204.2ec59d5986fb673e.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.8d927ca91da0384a.js`](./nordic.atlas-details.0205.8d927ca91da0384a.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.9c231af72ff68a95.js`](./nordic.atlas-details.0206.9c231af72ff68a95.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.b9f542a7d63ccae7.js`](./nordic.atlas-details.0207.b9f542a7d63ccae7.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.5c8ddfd345b4ea14.js`](./nordic.atlas-details.0208.5c8ddfd345b4ea14.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.27271253c4fc0211.js`](./nordic.atlas-details.0209.27271253c4fc0211.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.03df37c27a592bc7.js`](./nordic.atlas-details.0210.03df37c27a592bc7.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.04c5b479c988438a.js`](./nordic.atlas-details.0211.04c5b479c988438a.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.295b97c636cbb086.js`](./nordic.atlas-details.0212.295b97c636cbb086.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.94a4a1587cef984c.js`](./nordic.atlas-details.0213.94a4a1587cef984c.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.ae68a1b8ee0cdc7f.js`](./nordic.atlas-details.0214.ae68a1b8ee0cdc7f.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.a1433ee6f7661896.js`](./nordic.atlas-details.0215.a1433ee6f7661896.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.13050544dc4515bb.js`](./nordic.atlas-details.0216.13050544dc4515bb.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.fbfe5730ac4c1d00.js`](./nordic.atlas-details.0217.fbfe5730ac4c1d00.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.b1ec4702829ff4e4.js`](./nordic.atlas-details.0218.b1ec4702829ff4e4.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.28d1bce1d3f1bc1d.js`](./nordic.atlas-details.0219.28d1bce1d3f1bc1d.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.a36b3e03d2777220.js`](./nordic.atlas-details.0220.a36b3e03d2777220.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.8e2ce2e3637d4b1f.js`](./nordic.atlas-details.0221.8e2ce2e3637d4b1f.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.f7ffbaa2f37ca361.js`](./nordic.atlas-details.0222.f7ffbaa2f37ca361.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.9855da0c89c64e45.js`](./nordic.atlas-details.0223.9855da0c89c64e45.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.59b05573efe418b1.js`](./nordic.atlas-details.0224.59b05573efe418b1.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.3c3b5ec4e7bfcdf4.js`](./nordic.atlas-details.0225.3c3b5ec4e7bfcdf4.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.da98d423b75004c8.js`](./nordic.atlas-details.0226.da98d423b75004c8.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.8a96cd2ab5b9665f.js`](./nordic.atlas-details.0227.8a96cd2ab5b9665f.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.e4930eca98565c18.js`](./nordic.atlas-details.0228.e4930eca98565c18.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.ef8f31496bbe9a92.js`](./nordic.atlas-details.0229.ef8f31496bbe9a92.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.4b3885f9877ae9a9.js`](./nordic.atlas-details.0230.4b3885f9877ae9a9.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.a4e1e3f95cac25d1.js`](./nordic.atlas-details.0231.a4e1e3f95cac25d1.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.def05891a0dbb366.js`](./nordic.atlas-details.0232.def05891a0dbb366.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.3972c5b9549b6e27.js`](./nordic.atlas-details.0233.3972c5b9549b6e27.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.6c799e73f4bed672.js`](./nordic.atlas-details.0234.6c799e73f4bed672.js)
- Static atlas data chunk: [`nordic.atlas-edges.0235.e023f73a7068c3bd.js`](./nordic.atlas-edges.0235.e023f73a7068c3bd.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0236.5cd1758b77646373.js`](./nordic.atlas-sequences.0236.5cd1758b77646373.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0237.cc545de0fd4f9298.js`](./nordic.atlas-indexes.0237.cc545de0fd4f9298.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0238.d0efdb7902e8ee91.js`](./nordic.atlas-indexes.0238.d0efdb7902e8ee91.js)
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
- Static atlas runtime: [`nordic_map.atlas-runtime.c7b264756b4cae81.js`](./nordic_map.atlas-runtime.c7b264756b4cae81.js)
- Interactive evidence tools: [`nordic_map.atlas-evidence-tools.bac3f9295a5c95bb.js`](./nordic_map.atlas-evidence-tools.bac3f9295a5c95bb.js)
- Static atlas index transport: [`nordic_map.atlas-index-transport.2168d29af8354bcb.js`](./nordic_map.atlas-index-transport.2168d29af8354bcb.js)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | Pollen sequences staged from the LandClim normalization bundle. | `490` |
| Neotoma pollen sites | `scope_specific_overlay` | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `193` |
| SEAD sites | `scope_specific_overlay` | SEAD site inventory for spatial context. Site envelopes summarize source chronology and are not dated events or interval evidence. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `8799` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `2` |
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



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The retained Nordic bundle adds governed pollen, archaeology, modeled, boundary and fieldwork overlays to the same shared human/animal publication engine.

**Unsupported claim.** Overlay co-location is not causal farming history, scientific admission of pollen/LRA inputs, genotype-aware analysis or measured vegetation accuracy.

**Actual verification performed.** The retained saved atlas consumer at 1b338ee91 reconciles all 1,481 normalized source records. Native map assembly at that source passed in 333.12 seconds, RSS 5,366,333,440 B; independent decoded preservation and search references passed in 35.10 seconds, RSS 708,460,544 B. All unrelated scientific payloads, dates and coordinates are preserved. Current world/Europe index factories pass; Nordic qualification is reused only after exact code, bootstrap, controller, wire and semantic equality. Actual served runtime passes 27 cases, including four contextual Qinghai dates and a recovered horse owner. Seventeen targeted reader guards pass. Prior failures and their corrections are retained; no model or source census replay. Current chronology metadata at b3e8a50528562486a8c1c98f77e147f4bf23f603 prepares twelve JSONs in0.856s/RSS109969408B;565inputs+HEAD/index stable. Independent0.669s binds all121sourcepins and exact3native sidecars/9owned copies, changing only3identities+refusal1157→1158 percopy. All430HTML/static/controller/index files and relevant renderer code remain exact originalmap output/epoch; no fullmap, index or browser rerun. Three sourcepointlayers remain exact335/13/13. Current comparator metadata at2001492b94bb345509979cea924b56245e5392fa prepares12JSONs in1.028s/RSS119685120B;578inputs+HEAD/index stable. One master rawidentity changes; eachownedcopy changes only input/corpus/content hashes. All1158refusals/335world+13regional nodes/dates/countrycounts and430runtimefiles remainexact. Actualcurrentmapped/excluded APIs and13entityinputs exact; no entity/model/map/browser/index replay. Earlier actuals retain their own epochs.

**Remaining input or review.** Each layer retains its own chronology, entity, rights and scientific decisions. Actual shared-runtime World temporal cases do not substitute broader browser/provider, latency or ecological qualification.

**Cause category.** Regional context publication with mixed source families.

**Consequence.** Nordic overlays remain local scope evidence; a map display cannot transfer biological or chronological authority between layers.

**Precise next acceptance route.** Inspect the qualified current Nordic source-sample, exact-label and model-window lineage; admit observations and source roles before a named scientific cross-layer comparison.

**Negative or refused result.** Unresolved animal chronology and approximate locality warnings remain visible. Missing external basemap tiles offline are not an empty scientific layer.

**Matched denominator.** Four-country human display totals1,231 samples (SE416/NO130/FI32/DK653); eight animal locality points and one documented fieldwork location are separate evidence populations.

- [Retained qualification evidence: docs/report/regions/nordic/nordic_summary.json](nordic_summary.json) (SHA-256 `380818ce3f5ae1ac6aa7756e0a57adeb44bdf02cfee4e305c65ca7b8f15c5899`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

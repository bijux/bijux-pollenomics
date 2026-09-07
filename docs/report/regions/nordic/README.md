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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.81966d707e751ffb.js`](./nordic.atlas-provenance.0000.81966d707e751ffb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.a3c9040736230331.js`](./nordic.atlas-nodes.0001.a3c9040736230331.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.489f63b27f9cd267.js`](./nordic.atlas-nodes.0002.489f63b27f9cd267.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.e7b79f12f575d1c8.js`](./nordic.atlas-nodes.0003.e7b79f12f575d1c8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.55795b283f24d9cb.js`](./nordic.atlas-nodes.0004.55795b283f24d9cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.3f55070b77b343ad.js`](./nordic.atlas-nodes.0005.3f55070b77b343ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.7cbe0db782000644.js`](./nordic.atlas-nodes.0006.7cbe0db782000644.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.51b57b87e2dd82fb.js`](./nordic.atlas-nodes.0007.51b57b87e2dd82fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.e52e5080170b5710.js`](./nordic.atlas-nodes.0008.e52e5080170b5710.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.48fd2e2915cfd67b.js`](./nordic.atlas-nodes.0009.48fd2e2915cfd67b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.58eb563d5e1ba3fb.js`](./nordic.atlas-nodes.0010.58eb563d5e1ba3fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.70e7532123f1de17.js`](./nordic.atlas-nodes.0011.70e7532123f1de17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.3943268cce91ab37.js`](./nordic.atlas-nodes.0012.3943268cce91ab37.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.f58abcce7e69b533.js`](./nordic.atlas-nodes.0013.f58abcce7e69b533.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.77970bbb2980d51b.js`](./nordic.atlas-nodes.0014.77970bbb2980d51b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.232b53d2fc08b1d3.js`](./nordic.atlas-nodes.0015.232b53d2fc08b1d3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.7dc129f66573b307.js`](./nordic.atlas-nodes.0016.7dc129f66573b307.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.523e0604376d6979.js`](./nordic.atlas-nodes.0017.523e0604376d6979.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.62250b64fe4e1434.js`](./nordic.atlas-nodes.0018.62250b64fe4e1434.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.471acfb6a8e1fe64.js`](./nordic.atlas-nodes.0019.471acfb6a8e1fe64.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.6211cc13596ca080.js`](./nordic.atlas-nodes.0020.6211cc13596ca080.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.d637efaae88815b4.js`](./nordic.atlas-nodes.0021.d637efaae88815b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.f9fbf4e8ef2ca6a9.js`](./nordic.atlas-nodes.0022.f9fbf4e8ef2ca6a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.35fb12364ddf27c4.js`](./nordic.atlas-nodes.0023.35fb12364ddf27c4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.434a80b978fbb5b2.js`](./nordic.atlas-nodes.0024.434a80b978fbb5b2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.ee42f0e0471b904d.js`](./nordic.atlas-nodes.0025.ee42f0e0471b904d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.93587a686f604d85.js`](./nordic.atlas-nodes.0026.93587a686f604d85.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.a6b3766ceb3473e1.js`](./nordic.atlas-nodes.0027.a6b3766ceb3473e1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.a3c5105d2b27754c.js`](./nordic.atlas-nodes.0028.a3c5105d2b27754c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.6d8b1a7cbbe8a664.js`](./nordic.atlas-nodes.0029.6d8b1a7cbbe8a664.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.104bb146399d1e2c.js`](./nordic.atlas-nodes.0030.104bb146399d1e2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.b6eb58a6922e808b.js`](./nordic.atlas-nodes.0031.b6eb58a6922e808b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.0dfeaffe1df427af.js`](./nordic.atlas-nodes.0032.0dfeaffe1df427af.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.d75aca3d4339f422.js`](./nordic.atlas-nodes.0033.d75aca3d4339f422.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.a96925d1fb18b6d8.js`](./nordic.atlas-nodes.0034.a96925d1fb18b6d8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.80ba73b33d99d81f.js`](./nordic.atlas-nodes.0035.80ba73b33d99d81f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.f598c5569ca9898a.js`](./nordic.atlas-nodes.0036.f598c5569ca9898a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.8ef4f99c3837aba2.js`](./nordic.atlas-nodes.0037.8ef4f99c3837aba2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.3ad48e1af066f0bc.js`](./nordic.atlas-nodes.0038.3ad48e1af066f0bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.1fc303ec3e07f2ae.js`](./nordic.atlas-nodes.0039.1fc303ec3e07f2ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.7cc6a7fa63026e7a.js`](./nordic.atlas-nodes.0040.7cc6a7fa63026e7a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.14fb50d94f2bc949.js`](./nordic.atlas-nodes.0041.14fb50d94f2bc949.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.54ad03b3dfba9ac9.js`](./nordic.atlas-nodes.0042.54ad03b3dfba9ac9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.db8e639d90e706e0.js`](./nordic.atlas-nodes.0043.db8e639d90e706e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.a433cac4fab77af4.js`](./nordic.atlas-nodes.0044.a433cac4fab77af4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.eedb618f91ae8754.js`](./nordic.atlas-nodes.0045.eedb618f91ae8754.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.677a23922e04788a.js`](./nordic.atlas-nodes.0046.677a23922e04788a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.d7e7994b80ed67a8.js`](./nordic.atlas-nodes.0047.d7e7994b80ed67a8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.21147d57a4c799c9.js`](./nordic.atlas-nodes.0048.21147d57a4c799c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.f57b65477099f65c.js`](./nordic.atlas-nodes.0049.f57b65477099f65c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.bf2cb72dabff3cad.js`](./nordic.atlas-nodes.0050.bf2cb72dabff3cad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.c54bdb5041aa9a76.js`](./nordic.atlas-nodes.0051.c54bdb5041aa9a76.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.6b6a76be92997d0e.js`](./nordic.atlas-nodes.0052.6b6a76be92997d0e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.5bf7dd1d1ce167e5.js`](./nordic.atlas-nodes.0053.5bf7dd1d1ce167e5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.6f5bb715f080ab71.js`](./nordic.atlas-nodes.0054.6f5bb715f080ab71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.18fcb122854a1784.js`](./nordic.atlas-nodes.0055.18fcb122854a1784.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.a09aa0d02851a935.js`](./nordic.atlas-nodes.0056.a09aa0d02851a935.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.7f888f13ce8169be.js`](./nordic.atlas-nodes.0057.7f888f13ce8169be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.413bc7e40236c847.js`](./nordic.atlas-nodes.0058.413bc7e40236c847.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.f6a9f5ed4cb40128.js`](./nordic.atlas-nodes.0059.f6a9f5ed4cb40128.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.0b5d4c5808795abd.js`](./nordic.atlas-nodes.0060.0b5d4c5808795abd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.6691c5918fd50758.js`](./nordic.atlas-nodes.0061.6691c5918fd50758.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.37d1a5b9d5bae79b.js`](./nordic.atlas-nodes.0062.37d1a5b9d5bae79b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.93fe76861ea818d6.js`](./nordic.atlas-nodes.0063.93fe76861ea818d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.98af59bdedab63c1.js`](./nordic.atlas-nodes.0064.98af59bdedab63c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.618dfddd3630f5e1.js`](./nordic.atlas-nodes.0065.618dfddd3630f5e1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.a68296ee15009e58.js`](./nordic.atlas-nodes.0066.a68296ee15009e58.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.db175c6642502a0b.js`](./nordic.atlas-nodes.0067.db175c6642502a0b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.015edbf2bffcc8c5.js`](./nordic.atlas-nodes.0068.015edbf2bffcc8c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.cdad2e9083f85213.js`](./nordic.atlas-nodes.0069.cdad2e9083f85213.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.f78f4a3dc423ac4e.js`](./nordic.atlas-nodes.0070.f78f4a3dc423ac4e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.4a0493f4988a9a2d.js`](./nordic.atlas-nodes.0071.4a0493f4988a9a2d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.06123ea4a5b923b7.js`](./nordic.atlas-nodes.0072.06123ea4a5b923b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.a20d25e4495e1262.js`](./nordic.atlas-nodes.0073.a20d25e4495e1262.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.22c2d2a18c1a40a8.js`](./nordic.atlas-nodes.0074.22c2d2a18c1a40a8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.9753b9780c7e6ab7.js`](./nordic.atlas-nodes.0075.9753b9780c7e6ab7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.eec8e796eb2be0b8.js`](./nordic.atlas-nodes.0076.eec8e796eb2be0b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.854a7284040d13ec.js`](./nordic.atlas-nodes.0077.854a7284040d13ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.2ded7501294d7ff6.js`](./nordic.atlas-nodes.0078.2ded7501294d7ff6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.0d3228822d09d61a.js`](./nordic.atlas-nodes.0079.0d3228822d09d61a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.9e3237598a460b6f.js`](./nordic.atlas-nodes.0080.9e3237598a460b6f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.01cbdec58b9fc053.js`](./nordic.atlas-nodes.0081.01cbdec58b9fc053.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.6737d5e3a284c56a.js`](./nordic.atlas-nodes.0082.6737d5e3a284c56a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.6c33a355bf588d4f.js`](./nordic.atlas-nodes.0083.6c33a355bf588d4f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.bc54f54ad0789dad.js`](./nordic.atlas-nodes.0084.bc54f54ad0789dad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.6546e7ea226c0e22.js`](./nordic.atlas-nodes.0085.6546e7ea226c0e22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.a80dc403d921c184.js`](./nordic.atlas-nodes.0086.a80dc403d921c184.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.d0294241bd99de44.js`](./nordic.atlas-nodes.0087.d0294241bd99de44.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.ac45ac1f1b7a0eaf.js`](./nordic.atlas-nodes.0088.ac45ac1f1b7a0eaf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.a5a0bcf2b9893d0f.js`](./nordic.atlas-nodes.0089.a5a0bcf2b9893d0f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.53c339a139fe802d.js`](./nordic.atlas-nodes.0090.53c339a139fe802d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.4634e01f7cab2538.js`](./nordic.atlas-nodes.0091.4634e01f7cab2538.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.9353d7bf2a1f64cc.js`](./nordic.atlas-nodes.0092.9353d7bf2a1f64cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.d5f1c92e1f658ed7.js`](./nordic.atlas-nodes.0093.d5f1c92e1f658ed7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.70369a60f8e2b38e.js`](./nordic.atlas-nodes.0094.70369a60f8e2b38e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.0940c9f0424afff3.js`](./nordic.atlas-nodes.0095.0940c9f0424afff3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.9711ac109063fa67.js`](./nordic.atlas-nodes.0096.9711ac109063fa67.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.16fb377387ab72fc.js`](./nordic.atlas-nodes.0097.16fb377387ab72fc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.163fe3dd36a08cdd.js`](./nordic.atlas-nodes.0098.163fe3dd36a08cdd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.a95bd4dac1d0a81f.js`](./nordic.atlas-nodes.0099.a95bd4dac1d0a81f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.f542096e0723b15d.js`](./nordic.atlas-nodes.0100.f542096e0723b15d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.99e396ce0cebc881.js`](./nordic.atlas-nodes.0101.99e396ce0cebc881.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.8c853d9458018cbb.js`](./nordic.atlas-nodes.0102.8c853d9458018cbb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.7ffbb02a56006386.js`](./nordic.atlas-nodes.0103.7ffbb02a56006386.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.c7e86a28cf0a1248.js`](./nordic.atlas-nodes.0104.c7e86a28cf0a1248.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.497fadfaf60d4164.js`](./nordic.atlas-nodes.0105.497fadfaf60d4164.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.8aef3aaf3a3d10dc.js`](./nordic.atlas-nodes.0106.8aef3aaf3a3d10dc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.454819316ead18ae.js`](./nordic.atlas-nodes.0107.454819316ead18ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.141e9d1677c695bd.js`](./nordic.atlas-nodes.0108.141e9d1677c695bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.79c3e593367a5146.js`](./nordic.atlas-nodes.0109.79c3e593367a5146.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.b945118d79a7c7d9.js`](./nordic.atlas-nodes.0110.b945118d79a7c7d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.4404ab57b531631d.js`](./nordic.atlas-nodes.0111.4404ab57b531631d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.3b0973a125043f01.js`](./nordic.atlas-nodes.0112.3b0973a125043f01.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.f34772ab36f26a77.js`](./nordic.atlas-nodes.0113.f34772ab36f26a77.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.6ca3b6ebdf7ea71d.js`](./nordic.atlas-nodes.0114.6ca3b6ebdf7ea71d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.3e94b42417a32f1d.js`](./nordic.atlas-nodes.0115.3e94b42417a32f1d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.6ff19d840e371a2b.js`](./nordic.atlas-nodes.0116.6ff19d840e371a2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.b85fa35234e53c09.js`](./nordic.atlas-nodes.0117.b85fa35234e53c09.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.4a32ffc185c8b8c7.js`](./nordic.atlas-nodes.0118.4a32ffc185c8b8c7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.dafeb7c37a43a2ac.js`](./nordic.atlas-nodes.0119.dafeb7c37a43a2ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.48851530385a4b3e.js`](./nordic.atlas-nodes.0120.48851530385a4b3e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.6197d973271b8fbe.js`](./nordic.atlas-nodes.0121.6197d973271b8fbe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.853a2375465f6b58.js`](./nordic.atlas-nodes.0122.853a2375465f6b58.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.fba966caa5214651.js`](./nordic.atlas-nodes.0123.fba966caa5214651.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.d61964422d465250.js`](./nordic.atlas-nodes.0124.d61964422d465250.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.6926fa541d604bf9.js`](./nordic.atlas-nodes.0125.6926fa541d604bf9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.038adee401ca0bc2.js`](./nordic.atlas-nodes.0126.038adee401ca0bc2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.e4d209c14861f73a.js`](./nordic.atlas-nodes.0127.e4d209c14861f73a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.486a7b584f1b3e7c.js`](./nordic.atlas-nodes.0128.486a7b584f1b3e7c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.167f0b54166d62e5.js`](./nordic.atlas-nodes.0129.167f0b54166d62e5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.05d5195ad8cf2304.js`](./nordic.atlas-nodes.0130.05d5195ad8cf2304.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.56b90569b31f9eb0.js`](./nordic.atlas-nodes.0131.56b90569b31f9eb0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.cdca0c04b8d884f6.js`](./nordic.atlas-nodes.0132.cdca0c04b8d884f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.082ee21f19c0ed5a.js`](./nordic.atlas-nodes.0133.082ee21f19c0ed5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.d2656161eeaed3d9.js`](./nordic.atlas-nodes.0134.d2656161eeaed3d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.b08d7ca7e7f19894.js`](./nordic.atlas-nodes.0135.b08d7ca7e7f19894.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.868d6a0f4b6d9310.js`](./nordic.atlas-nodes.0136.868d6a0f4b6d9310.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.df6c2facfefc3e19.js`](./nordic.atlas-nodes.0137.df6c2facfefc3e19.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.e1712d708c23289c.js`](./nordic.atlas-nodes.0138.e1712d708c23289c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.a5d55a8619ae886e.js`](./nordic.atlas-nodes.0139.a5d55a8619ae886e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.0a0cbd66290e879c.js`](./nordic.atlas-nodes.0140.0a0cbd66290e879c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.0ffb3dee4c5573cf.js`](./nordic.atlas-nodes.0141.0ffb3dee4c5573cf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.92d75687ce63233d.js`](./nordic.atlas-nodes.0142.92d75687ce63233d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.bec0ddd5c79277d9.js`](./nordic.atlas-nodes.0143.bec0ddd5c79277d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.4b2b40bd3fb12ca6.js`](./nordic.atlas-nodes.0144.4b2b40bd3fb12ca6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.38490bb41d40e291.js`](./nordic.atlas-nodes.0145.38490bb41d40e291.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.dfe7e228f874460e.js`](./nordic.atlas-nodes.0146.dfe7e228f874460e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.4643f56880c42d10.js`](./nordic.atlas-nodes.0147.4643f56880c42d10.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.803e042436d45e3c.js`](./nordic.atlas-nodes.0148.803e042436d45e3c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.b47407be36ac38e9.js`](./nordic.atlas-nodes.0149.b47407be36ac38e9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.39113a3f9213639d.js`](./nordic.atlas-nodes.0150.39113a3f9213639d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.580b107d4449e922.js`](./nordic.atlas-nodes.0151.580b107d4449e922.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.a63a0e3a6edce290.js`](./nordic.atlas-nodes.0152.a63a0e3a6edce290.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.96d15775c9ad95cb.js`](./nordic.atlas-nodes.0153.96d15775c9ad95cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.7e909841fe56c392.js`](./nordic.atlas-nodes.0154.7e909841fe56c392.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.efb37df7cb9a45be.js`](./nordic.atlas-nodes.0155.efb37df7cb9a45be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.8fe11779648dd621.js`](./nordic.atlas-nodes.0156.8fe11779648dd621.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.c8d6f5245426a6bc.js`](./nordic.atlas-nodes.0157.c8d6f5245426a6bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.5700a9da1a110b35.js`](./nordic.atlas-nodes.0158.5700a9da1a110b35.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.964a484af5139be9.js`](./nordic.atlas-nodes.0159.964a484af5139be9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.10120c98b28b1518.js`](./nordic.atlas-nodes.0160.10120c98b28b1518.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.373a64d01d8c72ca.js`](./nordic.atlas-nodes.0161.373a64d01d8c72ca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.7af34d0612ef5088.js`](./nordic.atlas-nodes.0162.7af34d0612ef5088.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.c8be95e26de03831.js`](./nordic.atlas-nodes.0163.c8be95e26de03831.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.177fcc02029eadfc.js`](./nordic.atlas-nodes.0164.177fcc02029eadfc.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.024298168a9afefe.js`](./nordic.atlas-details.0165.024298168a9afefe.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.7b0d31a891a17764.js`](./nordic.atlas-details.0166.7b0d31a891a17764.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.16dc4067bc0f53c2.js`](./nordic.atlas-details.0167.16dc4067bc0f53c2.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.57fc8e158f6781ae.js`](./nordic.atlas-details.0168.57fc8e158f6781ae.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.ade06d608871d71d.js`](./nordic.atlas-details.0169.ade06d608871d71d.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.70fe0d815c6f597f.js`](./nordic.atlas-details.0170.70fe0d815c6f597f.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.d524683035ac66a3.js`](./nordic.atlas-details.0171.d524683035ac66a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.7405d766e13f8295.js`](./nordic.atlas-details.0172.7405d766e13f8295.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.3e0933f67b2a6cb4.js`](./nordic.atlas-details.0173.3e0933f67b2a6cb4.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.8763032ff7090eaa.js`](./nordic.atlas-details.0174.8763032ff7090eaa.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.cce11c666ed03bd7.js`](./nordic.atlas-details.0175.cce11c666ed03bd7.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.88e9d7f658a89abd.js`](./nordic.atlas-details.0176.88e9d7f658a89abd.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.28c9307cdf9c4920.js`](./nordic.atlas-details.0177.28c9307cdf9c4920.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.7122ba3297a4902a.js`](./nordic.atlas-details.0178.7122ba3297a4902a.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.e1b7c7fb4ce84224.js`](./nordic.atlas-details.0179.e1b7c7fb4ce84224.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.e560b0b74fd8ada2.js`](./nordic.atlas-details.0180.e560b0b74fd8ada2.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.bc6be0c76f1b9325.js`](./nordic.atlas-details.0181.bc6be0c76f1b9325.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.08e5eaf5d42965f0.js`](./nordic.atlas-details.0182.08e5eaf5d42965f0.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.e8dae9532d5c3f45.js`](./nordic.atlas-details.0183.e8dae9532d5c3f45.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.1058b913ce70adf6.js`](./nordic.atlas-details.0184.1058b913ce70adf6.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.669bac87d8bf8ea8.js`](./nordic.atlas-details.0185.669bac87d8bf8ea8.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.2b3abc5aa5b6e4f3.js`](./nordic.atlas-details.0186.2b3abc5aa5b6e4f3.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.dd79c68df8625802.js`](./nordic.atlas-details.0187.dd79c68df8625802.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.49306009f014af31.js`](./nordic.atlas-details.0188.49306009f014af31.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.f88bb0c12a608f6c.js`](./nordic.atlas-details.0189.f88bb0c12a608f6c.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.1e4a453fd71eab33.js`](./nordic.atlas-details.0190.1e4a453fd71eab33.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.08ca530c1be56b67.js`](./nordic.atlas-details.0191.08ca530c1be56b67.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.6027693e11da42c9.js`](./nordic.atlas-details.0192.6027693e11da42c9.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.feedf6df591bf2a9.js`](./nordic.atlas-details.0193.feedf6df591bf2a9.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.83d3effbe4a1e976.js`](./nordic.atlas-details.0194.83d3effbe4a1e976.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.1a8e10ca833a11b3.js`](./nordic.atlas-details.0195.1a8e10ca833a11b3.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.787b8f626db0c3ac.js`](./nordic.atlas-details.0196.787b8f626db0c3ac.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.5e7c7def11611d9c.js`](./nordic.atlas-details.0197.5e7c7def11611d9c.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.80f02f4a00a2eed6.js`](./nordic.atlas-details.0198.80f02f4a00a2eed6.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.073282f3ec130a9d.js`](./nordic.atlas-details.0199.073282f3ec130a9d.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.07635d33def516b3.js`](./nordic.atlas-details.0200.07635d33def516b3.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.f5d4211e89f142ab.js`](./nordic.atlas-details.0201.f5d4211e89f142ab.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.7176cad5e5439444.js`](./nordic.atlas-details.0202.7176cad5e5439444.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.ae108f22f70a4cd1.js`](./nordic.atlas-details.0203.ae108f22f70a4cd1.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.127bff517b911ae0.js`](./nordic.atlas-details.0204.127bff517b911ae0.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.43f906bfd023b033.js`](./nordic.atlas-details.0205.43f906bfd023b033.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.8ae1ff0dbb637c74.js`](./nordic.atlas-details.0206.8ae1ff0dbb637c74.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.066fb4423a40f6c2.js`](./nordic.atlas-details.0207.066fb4423a40f6c2.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.9d16f448d8bc8540.js`](./nordic.atlas-details.0208.9d16f448d8bc8540.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.bb5f19beac76e441.js`](./nordic.atlas-details.0209.bb5f19beac76e441.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.a7df2cb8cf613467.js`](./nordic.atlas-details.0210.a7df2cb8cf613467.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.c9e49379b8b5615c.js`](./nordic.atlas-details.0211.c9e49379b8b5615c.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.d1716b92696d549f.js`](./nordic.atlas-details.0212.d1716b92696d549f.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.a9e02ff467fdebdb.js`](./nordic.atlas-details.0213.a9e02ff467fdebdb.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.8f13fc1044e5af2d.js`](./nordic.atlas-details.0214.8f13fc1044e5af2d.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.2cf8719eb4deff38.js`](./nordic.atlas-details.0215.2cf8719eb4deff38.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.0d84c2780669272b.js`](./nordic.atlas-details.0216.0d84c2780669272b.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.c85405bfdd0c2874.js`](./nordic.atlas-details.0217.c85405bfdd0c2874.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.fe131c6abd7cf9ca.js`](./nordic.atlas-details.0218.fe131c6abd7cf9ca.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.78e81797d72ee93f.js`](./nordic.atlas-details.0219.78e81797d72ee93f.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.457ce67212c0daa8.js`](./nordic.atlas-details.0220.457ce67212c0daa8.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.9bc89070727ad39f.js`](./nordic.atlas-details.0221.9bc89070727ad39f.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.0b47fc95df83f924.js`](./nordic.atlas-details.0222.0b47fc95df83f924.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.917ad996e3b5bdd6.js`](./nordic.atlas-details.0223.917ad996e3b5bdd6.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.86cb7a49722569b6.js`](./nordic.atlas-details.0224.86cb7a49722569b6.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.52185d0fc71f662a.js`](./nordic.atlas-details.0225.52185d0fc71f662a.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.f0d740b7cb665ed6.js`](./nordic.atlas-details.0226.f0d740b7cb665ed6.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.6b985cd7faa7b85f.js`](./nordic.atlas-details.0227.6b985cd7faa7b85f.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.200ad199198e43f4.js`](./nordic.atlas-details.0228.200ad199198e43f4.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.1716e8da8503b5c5.js`](./nordic.atlas-edges.0229.1716e8da8503b5c5.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.6e59b06f7a2c7f9a.js`](./nordic.atlas-sequences.0230.6e59b06f7a2c7f9a.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.2e7ecaf5cc0fec33.js`](./nordic.atlas-indexes.0231.2e7ecaf5cc0fec33.js)
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


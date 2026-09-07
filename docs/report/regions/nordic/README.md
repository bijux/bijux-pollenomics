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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.b8ebcb1231c18dcd.js`](./nordic.atlas-provenance.0000.b8ebcb1231c18dcd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.4ae4eb4e2afb7ae4.js`](./nordic.atlas-nodes.0001.4ae4eb4e2afb7ae4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.cbcc1812d90e29cf.js`](./nordic.atlas-nodes.0002.cbcc1812d90e29cf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.b41a4d6f79afd6fb.js`](./nordic.atlas-nodes.0003.b41a4d6f79afd6fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.b41bbb9379a4f354.js`](./nordic.atlas-nodes.0004.b41bbb9379a4f354.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.05d866d09e107ab1.js`](./nordic.atlas-nodes.0005.05d866d09e107ab1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.622284947f2cef56.js`](./nordic.atlas-nodes.0006.622284947f2cef56.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.a5a1af31f933217f.js`](./nordic.atlas-nodes.0007.a5a1af31f933217f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.6c2e25a89cc4cb15.js`](./nordic.atlas-nodes.0008.6c2e25a89cc4cb15.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.65cfaca335e2ba19.js`](./nordic.atlas-nodes.0009.65cfaca335e2ba19.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.c21758d17b69c4bc.js`](./nordic.atlas-nodes.0010.c21758d17b69c4bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.21fabebd05c90dcf.js`](./nordic.atlas-nodes.0011.21fabebd05c90dcf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.916ad418c1a0db38.js`](./nordic.atlas-nodes.0012.916ad418c1a0db38.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.0dd57eb07c37b766.js`](./nordic.atlas-nodes.0013.0dd57eb07c37b766.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.abd2e28fcf8c337b.js`](./nordic.atlas-nodes.0014.abd2e28fcf8c337b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.8c59880c0e192e4e.js`](./nordic.atlas-nodes.0015.8c59880c0e192e4e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.e2035424cbe5153c.js`](./nordic.atlas-nodes.0016.e2035424cbe5153c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.492816f4e9a300d5.js`](./nordic.atlas-nodes.0017.492816f4e9a300d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.83cd8d634b0406d7.js`](./nordic.atlas-nodes.0018.83cd8d634b0406d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.cefae8287e625d8f.js`](./nordic.atlas-nodes.0019.cefae8287e625d8f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.714c3cbb64bb628d.js`](./nordic.atlas-nodes.0020.714c3cbb64bb628d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.fe80a809d4e55b86.js`](./nordic.atlas-nodes.0021.fe80a809d4e55b86.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.7a5d29a84df8e117.js`](./nordic.atlas-nodes.0022.7a5d29a84df8e117.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.5f21398728a21e80.js`](./nordic.atlas-nodes.0023.5f21398728a21e80.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.268687932fa4b687.js`](./nordic.atlas-nodes.0024.268687932fa4b687.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.fec332d7f7b3fb0e.js`](./nordic.atlas-nodes.0025.fec332d7f7b3fb0e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.1be5e35f5508c788.js`](./nordic.atlas-nodes.0026.1be5e35f5508c788.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.82a77023a04b7a18.js`](./nordic.atlas-nodes.0027.82a77023a04b7a18.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.9ad8f352787c314e.js`](./nordic.atlas-nodes.0028.9ad8f352787c314e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.600da6790a22db43.js`](./nordic.atlas-nodes.0029.600da6790a22db43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.0fa3a88761cbd43d.js`](./nordic.atlas-nodes.0030.0fa3a88761cbd43d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.d488074774360d64.js`](./nordic.atlas-nodes.0031.d488074774360d64.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.1ee808f68cfb657e.js`](./nordic.atlas-nodes.0032.1ee808f68cfb657e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.10ae9b7526088766.js`](./nordic.atlas-nodes.0033.10ae9b7526088766.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.dfed135c495c9a42.js`](./nordic.atlas-nodes.0034.dfed135c495c9a42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.f6b149bf3b510685.js`](./nordic.atlas-nodes.0035.f6b149bf3b510685.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.459e15e51b57ea5f.js`](./nordic.atlas-nodes.0036.459e15e51b57ea5f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.d5b33f6f5d5982b4.js`](./nordic.atlas-nodes.0037.d5b33f6f5d5982b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.7bfb3a0b485bd9f0.js`](./nordic.atlas-nodes.0038.7bfb3a0b485bd9f0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.4710a4cf7f12cb39.js`](./nordic.atlas-nodes.0039.4710a4cf7f12cb39.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.780d5677e2cb05f5.js`](./nordic.atlas-nodes.0040.780d5677e2cb05f5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.9d491289df8700bf.js`](./nordic.atlas-nodes.0041.9d491289df8700bf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.ad329500754f0416.js`](./nordic.atlas-nodes.0042.ad329500754f0416.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.9c7f2b88add11d92.js`](./nordic.atlas-nodes.0043.9c7f2b88add11d92.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.c8ea18f701cd6d55.js`](./nordic.atlas-nodes.0044.c8ea18f701cd6d55.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.9ff953fe6a69535b.js`](./nordic.atlas-nodes.0045.9ff953fe6a69535b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.a443558dc7630459.js`](./nordic.atlas-nodes.0046.a443558dc7630459.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.f2430c15bee0c507.js`](./nordic.atlas-nodes.0047.f2430c15bee0c507.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.8a0ea2169985c4b4.js`](./nordic.atlas-nodes.0048.8a0ea2169985c4b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.a94fe32350c5e686.js`](./nordic.atlas-nodes.0049.a94fe32350c5e686.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.27a43d70e907feaa.js`](./nordic.atlas-nodes.0050.27a43d70e907feaa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.6d64133bd968100c.js`](./nordic.atlas-nodes.0051.6d64133bd968100c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.4e634b8ea3aa2a04.js`](./nordic.atlas-nodes.0052.4e634b8ea3aa2a04.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.bd0cd28061aa9913.js`](./nordic.atlas-nodes.0053.bd0cd28061aa9913.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.7ac5318d4e9244a8.js`](./nordic.atlas-nodes.0054.7ac5318d4e9244a8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.4977b5f219d49d77.js`](./nordic.atlas-nodes.0055.4977b5f219d49d77.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.76934461ca62142f.js`](./nordic.atlas-nodes.0056.76934461ca62142f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.50bce590154a0abd.js`](./nordic.atlas-nodes.0057.50bce590154a0abd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.f90d107e9fe6aa53.js`](./nordic.atlas-nodes.0058.f90d107e9fe6aa53.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.14fa29df11cd558d.js`](./nordic.atlas-nodes.0059.14fa29df11cd558d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.799e536146685b51.js`](./nordic.atlas-nodes.0060.799e536146685b51.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.ea513074f9df0aa6.js`](./nordic.atlas-nodes.0061.ea513074f9df0aa6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.23914aaae54d6438.js`](./nordic.atlas-nodes.0062.23914aaae54d6438.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.899e1791c69edd83.js`](./nordic.atlas-nodes.0063.899e1791c69edd83.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.85e06567b6d3e482.js`](./nordic.atlas-nodes.0064.85e06567b6d3e482.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.dcf98e469651e4e6.js`](./nordic.atlas-nodes.0065.dcf98e469651e4e6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.cd037e7ee0def726.js`](./nordic.atlas-nodes.0066.cd037e7ee0def726.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.c6ccf35a5e5f5dd2.js`](./nordic.atlas-nodes.0067.c6ccf35a5e5f5dd2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.71e3abe6965973b6.js`](./nordic.atlas-nodes.0068.71e3abe6965973b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.fda0d0f321cf61e9.js`](./nordic.atlas-nodes.0069.fda0d0f321cf61e9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.3e034f85b376c4be.js`](./nordic.atlas-nodes.0070.3e034f85b376c4be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.964d7ef3237ad52d.js`](./nordic.atlas-nodes.0071.964d7ef3237ad52d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.b3de3e4ac32c67b2.js`](./nordic.atlas-nodes.0072.b3de3e4ac32c67b2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.6976b0f1b3177e29.js`](./nordic.atlas-nodes.0073.6976b0f1b3177e29.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.d4d9174c3d4ebf30.js`](./nordic.atlas-nodes.0074.d4d9174c3d4ebf30.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.c70ef3bc9cd13e19.js`](./nordic.atlas-nodes.0075.c70ef3bc9cd13e19.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.084f1f18028637f3.js`](./nordic.atlas-nodes.0076.084f1f18028637f3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.1ed9c889f5e18b9c.js`](./nordic.atlas-nodes.0077.1ed9c889f5e18b9c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.dd92522516667099.js`](./nordic.atlas-nodes.0078.dd92522516667099.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.2136d0ccb47ae748.js`](./nordic.atlas-nodes.0079.2136d0ccb47ae748.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.b09cce7b0b95c9a5.js`](./nordic.atlas-nodes.0080.b09cce7b0b95c9a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.3d35af72f69d9784.js`](./nordic.atlas-nodes.0081.3d35af72f69d9784.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.a889876b9d8664cd.js`](./nordic.atlas-nodes.0082.a889876b9d8664cd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.e9b4c8ea92908b1e.js`](./nordic.atlas-nodes.0083.e9b4c8ea92908b1e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.06e3301b644d0d41.js`](./nordic.atlas-nodes.0084.06e3301b644d0d41.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.b99115e3d2f52b05.js`](./nordic.atlas-nodes.0085.b99115e3d2f52b05.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.3f8ea29bfc2c9b1c.js`](./nordic.atlas-nodes.0086.3f8ea29bfc2c9b1c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.d177fe91893c2a17.js`](./nordic.atlas-nodes.0087.d177fe91893c2a17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.903d6148c7dd18fe.js`](./nordic.atlas-nodes.0088.903d6148c7dd18fe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.e3200701e29c9eb2.js`](./nordic.atlas-nodes.0089.e3200701e29c9eb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.b263d4ce05c85800.js`](./nordic.atlas-nodes.0090.b263d4ce05c85800.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.e6286cc89c00ba99.js`](./nordic.atlas-nodes.0091.e6286cc89c00ba99.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.4099d66093c6d4ef.js`](./nordic.atlas-nodes.0092.4099d66093c6d4ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.e49b7f51a42123ef.js`](./nordic.atlas-nodes.0093.e49b7f51a42123ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.711d903da587b388.js`](./nordic.atlas-nodes.0094.711d903da587b388.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.185100e88a68eb4b.js`](./nordic.atlas-nodes.0095.185100e88a68eb4b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.3f19bcea2201d746.js`](./nordic.atlas-nodes.0096.3f19bcea2201d746.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.60cfc1dd8b8de42f.js`](./nordic.atlas-nodes.0097.60cfc1dd8b8de42f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.9e7919a43b5bce9d.js`](./nordic.atlas-nodes.0098.9e7919a43b5bce9d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.fc446522be78d81a.js`](./nordic.atlas-nodes.0099.fc446522be78d81a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.aad7ec5e713b2c84.js`](./nordic.atlas-nodes.0100.aad7ec5e713b2c84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.58a1cff50fe10a5b.js`](./nordic.atlas-nodes.0101.58a1cff50fe10a5b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.103827e59c247de5.js`](./nordic.atlas-nodes.0102.103827e59c247de5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.2514e463d4210c9e.js`](./nordic.atlas-nodes.0103.2514e463d4210c9e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.6207176660a881c0.js`](./nordic.atlas-nodes.0104.6207176660a881c0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.086eabb748b32093.js`](./nordic.atlas-nodes.0105.086eabb748b32093.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.ab3ca6836b86f33f.js`](./nordic.atlas-nodes.0106.ab3ca6836b86f33f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.3dd203cbf848a825.js`](./nordic.atlas-nodes.0107.3dd203cbf848a825.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.28a995afafb47fe3.js`](./nordic.atlas-nodes.0108.28a995afafb47fe3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.cad19b0bce06ae3c.js`](./nordic.atlas-nodes.0109.cad19b0bce06ae3c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.4c3967d97c12cd68.js`](./nordic.atlas-nodes.0110.4c3967d97c12cd68.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.700d73e4e51cca35.js`](./nordic.atlas-nodes.0111.700d73e4e51cca35.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.6ef7cdda4bd5844d.js`](./nordic.atlas-nodes.0112.6ef7cdda4bd5844d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.373ea2729845996a.js`](./nordic.atlas-nodes.0113.373ea2729845996a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.841e638d15f4a8d7.js`](./nordic.atlas-nodes.0114.841e638d15f4a8d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.59ec262311af8507.js`](./nordic.atlas-nodes.0115.59ec262311af8507.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.dab5be26a2cb3132.js`](./nordic.atlas-nodes.0116.dab5be26a2cb3132.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.77f193abe39094c2.js`](./nordic.atlas-nodes.0117.77f193abe39094c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.c4b7399576772148.js`](./nordic.atlas-nodes.0118.c4b7399576772148.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.0d26deee76f96dc2.js`](./nordic.atlas-nodes.0119.0d26deee76f96dc2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.51850376483add3a.js`](./nordic.atlas-nodes.0120.51850376483add3a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.465f67eaeadb43db.js`](./nordic.atlas-nodes.0121.465f67eaeadb43db.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.0dc2b31d1e3f5985.js`](./nordic.atlas-nodes.0122.0dc2b31d1e3f5985.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.6b12f9ccac3ab161.js`](./nordic.atlas-nodes.0123.6b12f9ccac3ab161.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.67351e1ee3b10892.js`](./nordic.atlas-nodes.0124.67351e1ee3b10892.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.2a403488dd0301d4.js`](./nordic.atlas-nodes.0125.2a403488dd0301d4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.38f1f0c046e31279.js`](./nordic.atlas-nodes.0126.38f1f0c046e31279.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.91aceb5e49372dba.js`](./nordic.atlas-nodes.0127.91aceb5e49372dba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.82fbd3977389a1af.js`](./nordic.atlas-nodes.0128.82fbd3977389a1af.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.b83607a343ca4fe9.js`](./nordic.atlas-nodes.0129.b83607a343ca4fe9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.d7c1cd0050c59fbe.js`](./nordic.atlas-nodes.0130.d7c1cd0050c59fbe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.740673664696d308.js`](./nordic.atlas-nodes.0131.740673664696d308.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.fa4ef4253683c802.js`](./nordic.atlas-nodes.0132.fa4ef4253683c802.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.a18dbaa018a8f234.js`](./nordic.atlas-nodes.0133.a18dbaa018a8f234.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.c3b368f942b48f2a.js`](./nordic.atlas-nodes.0134.c3b368f942b48f2a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.fe748725684ba7da.js`](./nordic.atlas-nodes.0135.fe748725684ba7da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.1e021b58504f75a0.js`](./nordic.atlas-nodes.0136.1e021b58504f75a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.ba687b5a10fd7593.js`](./nordic.atlas-nodes.0137.ba687b5a10fd7593.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.b1f1c1e3a61ebda0.js`](./nordic.atlas-nodes.0138.b1f1c1e3a61ebda0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.9edb0f5f17b21501.js`](./nordic.atlas-nodes.0139.9edb0f5f17b21501.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.ddc370fd9ab78ccb.js`](./nordic.atlas-nodes.0140.ddc370fd9ab78ccb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.b8fc6caab3f8b1e2.js`](./nordic.atlas-nodes.0141.b8fc6caab3f8b1e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.577d47147f65e025.js`](./nordic.atlas-nodes.0142.577d47147f65e025.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.209317f5f2f8f05f.js`](./nordic.atlas-nodes.0143.209317f5f2f8f05f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.ac606c1d48b43156.js`](./nordic.atlas-nodes.0144.ac606c1d48b43156.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.b60a5c9b4a61b09d.js`](./nordic.atlas-nodes.0145.b60a5c9b4a61b09d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.8b7f5ab42c1a6253.js`](./nordic.atlas-nodes.0146.8b7f5ab42c1a6253.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.a2aed84d9961423b.js`](./nordic.atlas-nodes.0147.a2aed84d9961423b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.bb8a745c35f8ae35.js`](./nordic.atlas-nodes.0148.bb8a745c35f8ae35.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.33d919b92173df82.js`](./nordic.atlas-nodes.0149.33d919b92173df82.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.ee0997c7ec53e695.js`](./nordic.atlas-nodes.0150.ee0997c7ec53e695.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.9f81a23e305702a0.js`](./nordic.atlas-nodes.0151.9f81a23e305702a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.7388f540fa7a61a8.js`](./nordic.atlas-nodes.0152.7388f540fa7a61a8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.f8c9b49f03ca78a0.js`](./nordic.atlas-nodes.0153.f8c9b49f03ca78a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.1214c917108e5444.js`](./nordic.atlas-nodes.0154.1214c917108e5444.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.00094cbf1b31754c.js`](./nordic.atlas-nodes.0155.00094cbf1b31754c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.ad8838fafeccd2de.js`](./nordic.atlas-nodes.0156.ad8838fafeccd2de.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.d90b829476950ea9.js`](./nordic.atlas-nodes.0157.d90b829476950ea9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.b32aef39f444ac4b.js`](./nordic.atlas-nodes.0158.b32aef39f444ac4b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.144afbeb1cf7cc47.js`](./nordic.atlas-nodes.0159.144afbeb1cf7cc47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.bbdb865094aa1bf8.js`](./nordic.atlas-nodes.0160.bbdb865094aa1bf8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.5558c5964aa79110.js`](./nordic.atlas-nodes.0161.5558c5964aa79110.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.dbebc7366c49beb7.js`](./nordic.atlas-nodes.0162.dbebc7366c49beb7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.31ce64807c14b8f7.js`](./nordic.atlas-nodes.0163.31ce64807c14b8f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.1b3e5354bbb97ab2.js`](./nordic.atlas-nodes.0164.1b3e5354bbb97ab2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.fb167407d7260df4.js`](./nordic.atlas-nodes.0165.fb167407d7260df4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.b4b991b06f009eec.js`](./nordic.atlas-nodes.0166.b4b991b06f009eec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.95204943a883419e.js`](./nordic.atlas-nodes.0167.95204943a883419e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.090f067cb45bb1e1.js`](./nordic.atlas-nodes.0168.090f067cb45bb1e1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.972bffb6e12cf9ab.js`](./nordic.atlas-nodes.0169.972bffb6e12cf9ab.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.0e94270bd89a1639.js`](./nordic.atlas-nodes.0170.0e94270bd89a1639.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0171.d350a0c6f73d7bc5.js`](./nordic.atlas-nodes.0171.d350a0c6f73d7bc5.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.1719643851239d3c.js`](./nordic.atlas-details.0172.1719643851239d3c.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.5cbac438a37a45a6.js`](./nordic.atlas-details.0173.5cbac438a37a45a6.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.1138a28ca4d1a69d.js`](./nordic.atlas-details.0174.1138a28ca4d1a69d.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.8c457f1d5156685b.js`](./nordic.atlas-details.0175.8c457f1d5156685b.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.eb9b9b2fc0916b72.js`](./nordic.atlas-details.0176.eb9b9b2fc0916b72.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.2f64e33e75a808e9.js`](./nordic.atlas-details.0177.2f64e33e75a808e9.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.ef4e7ec9234340f0.js`](./nordic.atlas-details.0178.ef4e7ec9234340f0.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.dcf46792455efa4d.js`](./nordic.atlas-details.0179.dcf46792455efa4d.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.c3e92d81def5deef.js`](./nordic.atlas-details.0180.c3e92d81def5deef.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.5f7e094de00cfc54.js`](./nordic.atlas-details.0181.5f7e094de00cfc54.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.e62d1cde505d35ff.js`](./nordic.atlas-details.0182.e62d1cde505d35ff.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.9bbb94b482b6f7eb.js`](./nordic.atlas-details.0183.9bbb94b482b6f7eb.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.7dcd5e25a887bcbb.js`](./nordic.atlas-details.0184.7dcd5e25a887bcbb.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.37efbcdb1711a041.js`](./nordic.atlas-details.0185.37efbcdb1711a041.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.6146e06abe94dc8c.js`](./nordic.atlas-details.0186.6146e06abe94dc8c.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.818afd9ee05dbbe3.js`](./nordic.atlas-details.0187.818afd9ee05dbbe3.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.dfba11fe5fa852ea.js`](./nordic.atlas-details.0188.dfba11fe5fa852ea.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.54266e49613937fd.js`](./nordic.atlas-details.0189.54266e49613937fd.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.0d0e660c7b99f4f6.js`](./nordic.atlas-details.0190.0d0e660c7b99f4f6.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.f2b6a6a6bb40ca83.js`](./nordic.atlas-details.0191.f2b6a6a6bb40ca83.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.1294671ffd8edcd0.js`](./nordic.atlas-details.0192.1294671ffd8edcd0.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.a299ee74e01a3aa0.js`](./nordic.atlas-details.0193.a299ee74e01a3aa0.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.2313b2fbc520a18b.js`](./nordic.atlas-details.0194.2313b2fbc520a18b.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.d135e8c130021632.js`](./nordic.atlas-details.0195.d135e8c130021632.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.61970adcb8da96f5.js`](./nordic.atlas-details.0196.61970adcb8da96f5.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.a27b51885c7588c6.js`](./nordic.atlas-details.0197.a27b51885c7588c6.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.40ee3c5f040fbea9.js`](./nordic.atlas-details.0198.40ee3c5f040fbea9.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.cc9c696884dd3397.js`](./nordic.atlas-details.0199.cc9c696884dd3397.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.40121e8c18622fd2.js`](./nordic.atlas-details.0200.40121e8c18622fd2.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.9058d2b33d0edc19.js`](./nordic.atlas-details.0201.9058d2b33d0edc19.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.476411569cee0975.js`](./nordic.atlas-details.0202.476411569cee0975.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.5cde9a30ff538862.js`](./nordic.atlas-details.0203.5cde9a30ff538862.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.4b4276d5a765263d.js`](./nordic.atlas-details.0204.4b4276d5a765263d.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.efe5f76961766fcd.js`](./nordic.atlas-details.0205.efe5f76961766fcd.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.687541e0e9e0e57a.js`](./nordic.atlas-details.0206.687541e0e9e0e57a.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.42fd96dd27b6204f.js`](./nordic.atlas-details.0207.42fd96dd27b6204f.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.9ee6adfa59ce0dc9.js`](./nordic.atlas-details.0208.9ee6adfa59ce0dc9.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.27dc49e10a07579a.js`](./nordic.atlas-details.0209.27dc49e10a07579a.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.5828840adf97e6a6.js`](./nordic.atlas-details.0210.5828840adf97e6a6.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.d1c539d1e28d8264.js`](./nordic.atlas-details.0211.d1c539d1e28d8264.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.2a607efc4c8b657d.js`](./nordic.atlas-details.0212.2a607efc4c8b657d.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.23c229a8125044bd.js`](./nordic.atlas-details.0213.23c229a8125044bd.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.ed5c88e50ed4249e.js`](./nordic.atlas-details.0214.ed5c88e50ed4249e.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.8b5f0b8fde5bb3e0.js`](./nordic.atlas-details.0215.8b5f0b8fde5bb3e0.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.b2fae38f216da9e6.js`](./nordic.atlas-details.0216.b2fae38f216da9e6.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.ed6442a3993f7322.js`](./nordic.atlas-details.0217.ed6442a3993f7322.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.bbbeb0dd8bb68c49.js`](./nordic.atlas-details.0218.bbbeb0dd8bb68c49.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.1b045c3075c60f7b.js`](./nordic.atlas-details.0219.1b045c3075c60f7b.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.cf9ef7e91608fd1c.js`](./nordic.atlas-details.0220.cf9ef7e91608fd1c.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.150beebed2da3b68.js`](./nordic.atlas-details.0221.150beebed2da3b68.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.692a10c422108802.js`](./nordic.atlas-details.0222.692a10c422108802.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.1a7b54ccc08ad76b.js`](./nordic.atlas-details.0223.1a7b54ccc08ad76b.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.bcec5232b524f562.js`](./nordic.atlas-details.0224.bcec5232b524f562.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.01b66482ef88e670.js`](./nordic.atlas-details.0225.01b66482ef88e670.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.f076f1001070bbdd.js`](./nordic.atlas-details.0226.f076f1001070bbdd.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.bdd0411f8f58325a.js`](./nordic.atlas-details.0227.bdd0411f8f58325a.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.848dab0722c03753.js`](./nordic.atlas-details.0228.848dab0722c03753.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.71792c818cb60532.js`](./nordic.atlas-details.0229.71792c818cb60532.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.74cf99b43599206f.js`](./nordic.atlas-details.0230.74cf99b43599206f.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.1575f96899b1a487.js`](./nordic.atlas-details.0231.1575f96899b1a487.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.fde17e0e02f3443b.js`](./nordic.atlas-details.0232.fde17e0e02f3443b.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.0200c11a61d9b5c7.js`](./nordic.atlas-details.0233.0200c11a61d9b5c7.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.9f509336ee39a4f5.js`](./nordic.atlas-details.0234.9f509336ee39a4f5.js)
- Static atlas data chunk: [`nordic.atlas-details.0235.4b1612ca38923235.js`](./nordic.atlas-details.0235.4b1612ca38923235.js)
- Static atlas data chunk: [`nordic.atlas-edges.0236.7bff90a3b29984e9.js`](./nordic.atlas-edges.0236.7bff90a3b29984e9.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0237.4bd3fe662962e801.js`](./nordic.atlas-sequences.0237.4bd3fe662962e801.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0238.e46126455e166c5c.js`](./nordic.atlas-indexes.0238.e46126455e166c5c.js)
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


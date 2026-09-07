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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.51ad04eba3e929f6.js`](./nordic.atlas-provenance.0000.51ad04eba3e929f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.a1fa93c6365d150c.js`](./nordic.atlas-nodes.0001.a1fa93c6365d150c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.99e07b13cdebd101.js`](./nordic.atlas-nodes.0002.99e07b13cdebd101.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.c2339f2c93ca07ee.js`](./nordic.atlas-nodes.0003.c2339f2c93ca07ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.05cb0958ccd2261b.js`](./nordic.atlas-nodes.0004.05cb0958ccd2261b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.1e43a569378b09ea.js`](./nordic.atlas-nodes.0005.1e43a569378b09ea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.f588b5f503384fde.js`](./nordic.atlas-nodes.0006.f588b5f503384fde.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.5802031054a6084f.js`](./nordic.atlas-nodes.0007.5802031054a6084f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.42a7eafda00326a2.js`](./nordic.atlas-nodes.0008.42a7eafda00326a2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.dfb0319f92fd2428.js`](./nordic.atlas-nodes.0009.dfb0319f92fd2428.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.c43bb9548bff551b.js`](./nordic.atlas-nodes.0010.c43bb9548bff551b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.1e49a975fc954a22.js`](./nordic.atlas-nodes.0011.1e49a975fc954a22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.7795cc2596c3a967.js`](./nordic.atlas-nodes.0012.7795cc2596c3a967.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.dcefb65bcb913684.js`](./nordic.atlas-nodes.0013.dcefb65bcb913684.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.873d597b042838e0.js`](./nordic.atlas-nodes.0014.873d597b042838e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.14a9d004fc96272d.js`](./nordic.atlas-nodes.0015.14a9d004fc96272d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.2df7f584698838cb.js`](./nordic.atlas-nodes.0016.2df7f584698838cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.cf70e08a59047330.js`](./nordic.atlas-nodes.0017.cf70e08a59047330.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.6922d0b2912c963c.js`](./nordic.atlas-nodes.0018.6922d0b2912c963c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.db046fd04c12dd47.js`](./nordic.atlas-nodes.0019.db046fd04c12dd47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.30e0c52c3ea10310.js`](./nordic.atlas-nodes.0020.30e0c52c3ea10310.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.b01741e6cadcde57.js`](./nordic.atlas-nodes.0021.b01741e6cadcde57.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.b960c204483585b0.js`](./nordic.atlas-nodes.0022.b960c204483585b0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.b8bab751ed78d55a.js`](./nordic.atlas-nodes.0023.b8bab751ed78d55a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.5b1db436d2638dfc.js`](./nordic.atlas-nodes.0024.5b1db436d2638dfc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.b495d1bb24e345fe.js`](./nordic.atlas-nodes.0025.b495d1bb24e345fe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.d652f7bcdd6e28da.js`](./nordic.atlas-nodes.0026.d652f7bcdd6e28da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.289855cdf004e6bf.js`](./nordic.atlas-nodes.0027.289855cdf004e6bf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.0f66813650a661ec.js`](./nordic.atlas-nodes.0028.0f66813650a661ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.2972a84cd1383e9c.js`](./nordic.atlas-nodes.0029.2972a84cd1383e9c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.5fd34fcd3d5a2049.js`](./nordic.atlas-nodes.0030.5fd34fcd3d5a2049.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.568a0a4e99fd7458.js`](./nordic.atlas-nodes.0031.568a0a4e99fd7458.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.f7eb17439ce15d1c.js`](./nordic.atlas-nodes.0032.f7eb17439ce15d1c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.e0e2a41ae604d8b8.js`](./nordic.atlas-nodes.0033.e0e2a41ae604d8b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.573721bfe3da494c.js`](./nordic.atlas-nodes.0034.573721bfe3da494c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.11d8d157887e2b93.js`](./nordic.atlas-nodes.0035.11d8d157887e2b93.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.c27b6e317ec4764e.js`](./nordic.atlas-nodes.0036.c27b6e317ec4764e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.15ea5695d1113b94.js`](./nordic.atlas-nodes.0037.15ea5695d1113b94.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.9a46524f87afcef3.js`](./nordic.atlas-nodes.0038.9a46524f87afcef3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.e43a8bd87f2f26ad.js`](./nordic.atlas-nodes.0039.e43a8bd87f2f26ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.4b26a8d4971b324d.js`](./nordic.atlas-nodes.0040.4b26a8d4971b324d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.77d397e7ca392108.js`](./nordic.atlas-nodes.0041.77d397e7ca392108.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.08c533c4e100341d.js`](./nordic.atlas-nodes.0042.08c533c4e100341d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.740950170db065b7.js`](./nordic.atlas-nodes.0043.740950170db065b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.bfa03a4b9602b5b8.js`](./nordic.atlas-nodes.0044.bfa03a4b9602b5b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.47536786055d9998.js`](./nordic.atlas-nodes.0045.47536786055d9998.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.ee68583648285c34.js`](./nordic.atlas-nodes.0046.ee68583648285c34.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.53d6f036fa5c9117.js`](./nordic.atlas-nodes.0047.53d6f036fa5c9117.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.6342651ff05613cc.js`](./nordic.atlas-nodes.0048.6342651ff05613cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.51f26bda2711e422.js`](./nordic.atlas-nodes.0049.51f26bda2711e422.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.d9d7606189465ffb.js`](./nordic.atlas-nodes.0050.d9d7606189465ffb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.6634a3b4ff87c662.js`](./nordic.atlas-nodes.0051.6634a3b4ff87c662.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.b9bf7716fc7ac910.js`](./nordic.atlas-nodes.0052.b9bf7716fc7ac910.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.fbbfe3b89f7118f5.js`](./nordic.atlas-nodes.0053.fbbfe3b89f7118f5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.89e7539d7fc9d8c8.js`](./nordic.atlas-nodes.0054.89e7539d7fc9d8c8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.c2f2d072b0d033b2.js`](./nordic.atlas-nodes.0055.c2f2d072b0d033b2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.00f6d2c92211157e.js`](./nordic.atlas-nodes.0056.00f6d2c92211157e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.2615dcfa26704e64.js`](./nordic.atlas-nodes.0057.2615dcfa26704e64.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.3511a4ead111b8ff.js`](./nordic.atlas-nodes.0058.3511a4ead111b8ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.0604fff0284cbdd1.js`](./nordic.atlas-nodes.0059.0604fff0284cbdd1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.e22e8ed6528be00b.js`](./nordic.atlas-nodes.0060.e22e8ed6528be00b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.1aa39bc6f8439cde.js`](./nordic.atlas-nodes.0061.1aa39bc6f8439cde.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.36da377b206ee645.js`](./nordic.atlas-nodes.0062.36da377b206ee645.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.8d4231285c5896aa.js`](./nordic.atlas-nodes.0063.8d4231285c5896aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.921c93d9068261f7.js`](./nordic.atlas-nodes.0064.921c93d9068261f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.93167f84b538ae22.js`](./nordic.atlas-nodes.0065.93167f84b538ae22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.af9b1e8843e31cc0.js`](./nordic.atlas-nodes.0066.af9b1e8843e31cc0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.0b28b5f32ffb37c9.js`](./nordic.atlas-nodes.0067.0b28b5f32ffb37c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.4408cbac978ab769.js`](./nordic.atlas-nodes.0068.4408cbac978ab769.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.de8482c9b2d55373.js`](./nordic.atlas-nodes.0069.de8482c9b2d55373.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.ee57667c27191a5f.js`](./nordic.atlas-nodes.0070.ee57667c27191a5f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.8e1bb336e1eb6683.js`](./nordic.atlas-nodes.0071.8e1bb336e1eb6683.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.0235ce1c45a33cfc.js`](./nordic.atlas-nodes.0072.0235ce1c45a33cfc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.5e9bd66f28400c2d.js`](./nordic.atlas-nodes.0073.5e9bd66f28400c2d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.7ee39a910e9252d5.js`](./nordic.atlas-nodes.0074.7ee39a910e9252d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.d81fb575b7ad5162.js`](./nordic.atlas-nodes.0075.d81fb575b7ad5162.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.1f1d257b91290d4f.js`](./nordic.atlas-nodes.0076.1f1d257b91290d4f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.598c68bdde1c631a.js`](./nordic.atlas-nodes.0077.598c68bdde1c631a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.7ffc9d90e5090f7b.js`](./nordic.atlas-nodes.0078.7ffc9d90e5090f7b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.ef3ad66e46cbc0ce.js`](./nordic.atlas-nodes.0079.ef3ad66e46cbc0ce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.f88b220a534495ce.js`](./nordic.atlas-nodes.0080.f88b220a534495ce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.b18addc662884944.js`](./nordic.atlas-nodes.0081.b18addc662884944.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.a64e903a02dc3b2b.js`](./nordic.atlas-nodes.0082.a64e903a02dc3b2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.61f32b7ff8892873.js`](./nordic.atlas-nodes.0083.61f32b7ff8892873.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.64f55b1e0435fc07.js`](./nordic.atlas-nodes.0084.64f55b1e0435fc07.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.19c456c645f92135.js`](./nordic.atlas-nodes.0085.19c456c645f92135.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.b2a6d075ace78bb2.js`](./nordic.atlas-nodes.0086.b2a6d075ace78bb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.d8fc66a32b8b03bc.js`](./nordic.atlas-nodes.0087.d8fc66a32b8b03bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.1366cd30de59faba.js`](./nordic.atlas-nodes.0088.1366cd30de59faba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.acdb4b83bad3c5fb.js`](./nordic.atlas-nodes.0089.acdb4b83bad3c5fb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.a9d5d1a375efb8ad.js`](./nordic.atlas-nodes.0090.a9d5d1a375efb8ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.5399a9907203c585.js`](./nordic.atlas-nodes.0091.5399a9907203c585.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.6e3d17c2861494d2.js`](./nordic.atlas-nodes.0092.6e3d17c2861494d2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.a33b43e2079e2bbe.js`](./nordic.atlas-nodes.0093.a33b43e2079e2bbe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.aee051740caa4a69.js`](./nordic.atlas-nodes.0094.aee051740caa4a69.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.d87f88e4acad8171.js`](./nordic.atlas-nodes.0095.d87f88e4acad8171.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.16d20c37eb5396a4.js`](./nordic.atlas-nodes.0096.16d20c37eb5396a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.3d81bb532c885b48.js`](./nordic.atlas-nodes.0097.3d81bb532c885b48.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.d5097f6833a3506e.js`](./nordic.atlas-nodes.0098.d5097f6833a3506e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.46cb5278e1a77880.js`](./nordic.atlas-nodes.0099.46cb5278e1a77880.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.7d4d64787fb65295.js`](./nordic.atlas-nodes.0100.7d4d64787fb65295.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.22052ce6525c8501.js`](./nordic.atlas-nodes.0101.22052ce6525c8501.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.ede8422004161d79.js`](./nordic.atlas-nodes.0102.ede8422004161d79.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.f0632ded38043a3b.js`](./nordic.atlas-nodes.0103.f0632ded38043a3b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.31b878ddee6eca92.js`](./nordic.atlas-nodes.0104.31b878ddee6eca92.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.307c9b290bdfd9b6.js`](./nordic.atlas-nodes.0105.307c9b290bdfd9b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.2083fa2536b94574.js`](./nordic.atlas-nodes.0106.2083fa2536b94574.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.98c4a89b93d69288.js`](./nordic.atlas-nodes.0107.98c4a89b93d69288.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.adde896f66cb5e9e.js`](./nordic.atlas-nodes.0108.adde896f66cb5e9e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.ad169ba55c9afd78.js`](./nordic.atlas-nodes.0109.ad169ba55c9afd78.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.f382b14324265538.js`](./nordic.atlas-nodes.0110.f382b14324265538.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.e39af04851242506.js`](./nordic.atlas-nodes.0111.e39af04851242506.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.51ca4368c0424ac3.js`](./nordic.atlas-nodes.0112.51ca4368c0424ac3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.b57e45f1529d6da0.js`](./nordic.atlas-nodes.0113.b57e45f1529d6da0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.fe55f6103bfe4574.js`](./nordic.atlas-nodes.0114.fe55f6103bfe4574.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.69e2f7728e2cea37.js`](./nordic.atlas-nodes.0115.69e2f7728e2cea37.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.755f936f1a65fbed.js`](./nordic.atlas-nodes.0116.755f936f1a65fbed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.8c239a849c0cbab3.js`](./nordic.atlas-nodes.0117.8c239a849c0cbab3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.17943b29fff3dfb2.js`](./nordic.atlas-nodes.0118.17943b29fff3dfb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.62670132634a8aa4.js`](./nordic.atlas-nodes.0119.62670132634a8aa4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.79bfd0051ead3252.js`](./nordic.atlas-nodes.0120.79bfd0051ead3252.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.a5d02978c167fc44.js`](./nordic.atlas-nodes.0121.a5d02978c167fc44.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.e8de513f2620b364.js`](./nordic.atlas-nodes.0122.e8de513f2620b364.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.99dd6ba4be576df1.js`](./nordic.atlas-nodes.0123.99dd6ba4be576df1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.93789e49b0c4b7ff.js`](./nordic.atlas-nodes.0124.93789e49b0c4b7ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.60932ac2ddd3315d.js`](./nordic.atlas-nodes.0125.60932ac2ddd3315d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.ad79a3311c11ece7.js`](./nordic.atlas-nodes.0126.ad79a3311c11ece7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.e30acd0ad8fdcb7d.js`](./nordic.atlas-nodes.0127.e30acd0ad8fdcb7d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.20c354f5ceacaff0.js`](./nordic.atlas-nodes.0128.20c354f5ceacaff0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.001f6a87f72ea2f8.js`](./nordic.atlas-nodes.0129.001f6a87f72ea2f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.9fb44d4444e4db32.js`](./nordic.atlas-nodes.0130.9fb44d4444e4db32.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.103cd46fc8d8628c.js`](./nordic.atlas-nodes.0131.103cd46fc8d8628c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.3d5b2c0c7313e59d.js`](./nordic.atlas-nodes.0132.3d5b2c0c7313e59d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.1100c78fa8e9137d.js`](./nordic.atlas-nodes.0133.1100c78fa8e9137d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.51bc1504b6177b27.js`](./nordic.atlas-nodes.0134.51bc1504b6177b27.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.5caa881c6e3d0cb4.js`](./nordic.atlas-nodes.0135.5caa881c6e3d0cb4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.f4ffa8e8bdf5f56b.js`](./nordic.atlas-nodes.0136.f4ffa8e8bdf5f56b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.d7e0d2462f61b444.js`](./nordic.atlas-nodes.0137.d7e0d2462f61b444.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.1998dee9ca53fe91.js`](./nordic.atlas-nodes.0138.1998dee9ca53fe91.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.f2db2258bc10b65c.js`](./nordic.atlas-nodes.0139.f2db2258bc10b65c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.e0041dee46ec8695.js`](./nordic.atlas-nodes.0140.e0041dee46ec8695.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.62d8b8822b33bb5f.js`](./nordic.atlas-nodes.0141.62d8b8822b33bb5f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.db0f6b8b51d885d1.js`](./nordic.atlas-nodes.0142.db0f6b8b51d885d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.d15769bdcf6c4fc1.js`](./nordic.atlas-nodes.0143.d15769bdcf6c4fc1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.3702150f55fd2030.js`](./nordic.atlas-nodes.0144.3702150f55fd2030.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.36d4a0437e310ae1.js`](./nordic.atlas-nodes.0145.36d4a0437e310ae1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.3baeb627a02eed91.js`](./nordic.atlas-nodes.0146.3baeb627a02eed91.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.7a08532018c9c551.js`](./nordic.atlas-nodes.0147.7a08532018c9c551.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.9428565fec45f1b4.js`](./nordic.atlas-nodes.0148.9428565fec45f1b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.f814c598e7023ab9.js`](./nordic.atlas-nodes.0149.f814c598e7023ab9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.2e17874483e9fec0.js`](./nordic.atlas-nodes.0150.2e17874483e9fec0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.abd20df3162b413b.js`](./nordic.atlas-nodes.0151.abd20df3162b413b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.b87439006a325def.js`](./nordic.atlas-nodes.0152.b87439006a325def.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.be8411fd0175ed9d.js`](./nordic.atlas-nodes.0153.be8411fd0175ed9d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.b3a3b42baa385fb0.js`](./nordic.atlas-nodes.0154.b3a3b42baa385fb0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.458138e709e16e56.js`](./nordic.atlas-nodes.0155.458138e709e16e56.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.4ba78ecc938f743f.js`](./nordic.atlas-nodes.0156.4ba78ecc938f743f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.01ab5a4551ae41b5.js`](./nordic.atlas-nodes.0157.01ab5a4551ae41b5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.bc80a9807b772de0.js`](./nordic.atlas-nodes.0158.bc80a9807b772de0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.00ffd68aea544b79.js`](./nordic.atlas-nodes.0159.00ffd68aea544b79.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.013c570dea89cccd.js`](./nordic.atlas-nodes.0160.013c570dea89cccd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.1e7a89a7c02cddc5.js`](./nordic.atlas-nodes.0161.1e7a89a7c02cddc5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.bf06a2867741c320.js`](./nordic.atlas-nodes.0162.bf06a2867741c320.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.6429d671a0a3b1b3.js`](./nordic.atlas-nodes.0163.6429d671a0a3b1b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.3a41acbba181b03c.js`](./nordic.atlas-nodes.0164.3a41acbba181b03c.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.92952c8f7ce778a4.js`](./nordic.atlas-details.0165.92952c8f7ce778a4.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.0beba5cf922d2e1e.js`](./nordic.atlas-details.0166.0beba5cf922d2e1e.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.a23d47b1d1dbc53c.js`](./nordic.atlas-details.0167.a23d47b1d1dbc53c.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.7526f7721406dc81.js`](./nordic.atlas-details.0168.7526f7721406dc81.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.e5e82a6b808767d6.js`](./nordic.atlas-details.0169.e5e82a6b808767d6.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.5fc76310b203c9cc.js`](./nordic.atlas-details.0170.5fc76310b203c9cc.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.28e5fa9e881f78bd.js`](./nordic.atlas-details.0171.28e5fa9e881f78bd.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.bc697195000132ea.js`](./nordic.atlas-details.0172.bc697195000132ea.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.f9ada7ccd2844647.js`](./nordic.atlas-details.0173.f9ada7ccd2844647.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.5a57cc52f1644f14.js`](./nordic.atlas-details.0174.5a57cc52f1644f14.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.84b43d11a2b375b3.js`](./nordic.atlas-details.0175.84b43d11a2b375b3.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.1feef16d754a01cb.js`](./nordic.atlas-details.0176.1feef16d754a01cb.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.1235b362e4825ce4.js`](./nordic.atlas-details.0177.1235b362e4825ce4.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.3a889656e4f91f77.js`](./nordic.atlas-details.0178.3a889656e4f91f77.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.3e91550f46949cdc.js`](./nordic.atlas-details.0179.3e91550f46949cdc.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.da2ccd998d768961.js`](./nordic.atlas-details.0180.da2ccd998d768961.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.c855db452f43f0e4.js`](./nordic.atlas-details.0181.c855db452f43f0e4.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.4ce5ed3edf61b009.js`](./nordic.atlas-details.0182.4ce5ed3edf61b009.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.c771b45286badd00.js`](./nordic.atlas-details.0183.c771b45286badd00.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.a53eef0adb3b1e12.js`](./nordic.atlas-details.0184.a53eef0adb3b1e12.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.07c59590983c53ec.js`](./nordic.atlas-details.0185.07c59590983c53ec.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.0d40d813a6ffae6f.js`](./nordic.atlas-details.0186.0d40d813a6ffae6f.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.202300704b38c471.js`](./nordic.atlas-details.0187.202300704b38c471.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.6a5dc716e45576a8.js`](./nordic.atlas-details.0188.6a5dc716e45576a8.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.2f45a0a3259f8282.js`](./nordic.atlas-details.0189.2f45a0a3259f8282.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.b6492652f5a8e954.js`](./nordic.atlas-details.0190.b6492652f5a8e954.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.1bc38b8e65d07091.js`](./nordic.atlas-details.0191.1bc38b8e65d07091.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.27a7b8757307c3a0.js`](./nordic.atlas-details.0192.27a7b8757307c3a0.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.441693358db1bace.js`](./nordic.atlas-details.0193.441693358db1bace.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.a428a792391bfbd2.js`](./nordic.atlas-details.0194.a428a792391bfbd2.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.04a1383eeac620ab.js`](./nordic.atlas-details.0195.04a1383eeac620ab.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.d554f8449f2220c6.js`](./nordic.atlas-details.0196.d554f8449f2220c6.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.0a8cf5c8fc787c8b.js`](./nordic.atlas-details.0197.0a8cf5c8fc787c8b.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.d2c8353af17c685c.js`](./nordic.atlas-details.0198.d2c8353af17c685c.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.20cede75209bfefb.js`](./nordic.atlas-details.0199.20cede75209bfefb.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.55b3a0905f5bc76a.js`](./nordic.atlas-details.0200.55b3a0905f5bc76a.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.7e4d4ae8642b5cf7.js`](./nordic.atlas-details.0201.7e4d4ae8642b5cf7.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.c5caaeeca992b5ea.js`](./nordic.atlas-details.0202.c5caaeeca992b5ea.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.6057930a4cb2f3e5.js`](./nordic.atlas-details.0203.6057930a4cb2f3e5.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.73203c4bea8824ef.js`](./nordic.atlas-details.0204.73203c4bea8824ef.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.31ba17c38dbac87b.js`](./nordic.atlas-details.0205.31ba17c38dbac87b.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.4b54329fc1af116b.js`](./nordic.atlas-details.0206.4b54329fc1af116b.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.72d2b6c3b9e640be.js`](./nordic.atlas-details.0207.72d2b6c3b9e640be.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.b0db4af9406562be.js`](./nordic.atlas-details.0208.b0db4af9406562be.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.bc2c157475065a6e.js`](./nordic.atlas-details.0209.bc2c157475065a6e.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.c526e3b38b92cc8f.js`](./nordic.atlas-details.0210.c526e3b38b92cc8f.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.9563570e2729608f.js`](./nordic.atlas-details.0211.9563570e2729608f.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.7b78af08dea7088a.js`](./nordic.atlas-details.0212.7b78af08dea7088a.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.9690ebbda35e6ab4.js`](./nordic.atlas-details.0213.9690ebbda35e6ab4.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.dfe85fca7ecf9615.js`](./nordic.atlas-details.0214.dfe85fca7ecf9615.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.6d4c960c1b93af1e.js`](./nordic.atlas-details.0215.6d4c960c1b93af1e.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.1601e3d0cb660ea0.js`](./nordic.atlas-details.0216.1601e3d0cb660ea0.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.bda795698580d8dd.js`](./nordic.atlas-details.0217.bda795698580d8dd.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.497885c570aff320.js`](./nordic.atlas-details.0218.497885c570aff320.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.076c30f3acd440e0.js`](./nordic.atlas-details.0219.076c30f3acd440e0.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.f2b6885e0a8c661b.js`](./nordic.atlas-details.0220.f2b6885e0a8c661b.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.6b48db561ea2271a.js`](./nordic.atlas-details.0221.6b48db561ea2271a.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.a1831acede6283e6.js`](./nordic.atlas-details.0222.a1831acede6283e6.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.f16ccd1f628dd675.js`](./nordic.atlas-details.0223.f16ccd1f628dd675.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.a4972f899e26938e.js`](./nordic.atlas-details.0224.a4972f899e26938e.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.ef8523d701e85a97.js`](./nordic.atlas-details.0225.ef8523d701e85a97.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.9205b14a0030b401.js`](./nordic.atlas-details.0226.9205b14a0030b401.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.5345d4affbe22738.js`](./nordic.atlas-details.0227.5345d4affbe22738.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.452b4a63145b13e4.js`](./nordic.atlas-details.0228.452b4a63145b13e4.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.f3b38b54a980f082.js`](./nordic.atlas-edges.0229.f3b38b54a980f082.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.f7584a77cd6ef2ac.js`](./nordic.atlas-sequences.0230.f7584a77cd6ef2ac.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.5c8ce6f9c1d0a360.js`](./nordic.atlas-indexes.0231.5c8ce6f9c1d0a360.js)
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


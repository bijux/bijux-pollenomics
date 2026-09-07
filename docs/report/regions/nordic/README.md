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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.4eb6012c3f82f04a.js`](./nordic.atlas-provenance.0000.4eb6012c3f82f04a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.e6a19eff75a4060e.js`](./nordic.atlas-nodes.0001.e6a19eff75a4060e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.d06f4270ea65b442.js`](./nordic.atlas-nodes.0002.d06f4270ea65b442.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.1ef6b76f7f75acc0.js`](./nordic.atlas-nodes.0003.1ef6b76f7f75acc0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.c1546166287683eb.js`](./nordic.atlas-nodes.0004.c1546166287683eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.a6045c79453b0a2b.js`](./nordic.atlas-nodes.0005.a6045c79453b0a2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.1ebf4b07a816916e.js`](./nordic.atlas-nodes.0006.1ebf4b07a816916e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.e9aa66816cdb523a.js`](./nordic.atlas-nodes.0007.e9aa66816cdb523a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.2330fd298dd1fd32.js`](./nordic.atlas-nodes.0008.2330fd298dd1fd32.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.d9ea18418b73ef66.js`](./nordic.atlas-nodes.0009.d9ea18418b73ef66.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.69c6b1b29a6b23a1.js`](./nordic.atlas-nodes.0010.69c6b1b29a6b23a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.06f621c69f2666f9.js`](./nordic.atlas-nodes.0011.06f621c69f2666f9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.e3da7d79661cba1f.js`](./nordic.atlas-nodes.0012.e3da7d79661cba1f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.76ccd1a5201eaa58.js`](./nordic.atlas-nodes.0013.76ccd1a5201eaa58.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.4f55e68d2afcb47c.js`](./nordic.atlas-nodes.0014.4f55e68d2afcb47c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.fc7ebacf04b7ed2d.js`](./nordic.atlas-nodes.0015.fc7ebacf04b7ed2d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.12e3a4936c6f1fa7.js`](./nordic.atlas-nodes.0016.12e3a4936c6f1fa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.74ab1de48cf1c007.js`](./nordic.atlas-nodes.0017.74ab1de48cf1c007.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.7a3b52c07f77ace0.js`](./nordic.atlas-nodes.0018.7a3b52c07f77ace0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.9887cf69b47032b5.js`](./nordic.atlas-nodes.0019.9887cf69b47032b5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.043c8a8eed87fb1c.js`](./nordic.atlas-nodes.0020.043c8a8eed87fb1c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.be52a17b1b89f6e7.js`](./nordic.atlas-nodes.0021.be52a17b1b89f6e7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.e1d80cce9f08e52d.js`](./nordic.atlas-nodes.0022.e1d80cce9f08e52d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.fd85eb577052db54.js`](./nordic.atlas-nodes.0023.fd85eb577052db54.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.1f38af77fad9fd94.js`](./nordic.atlas-nodes.0024.1f38af77fad9fd94.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.0dc6364bddf6cdd3.js`](./nordic.atlas-nodes.0025.0dc6364bddf6cdd3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.122e9dfba834ba69.js`](./nordic.atlas-nodes.0026.122e9dfba834ba69.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.60479632cf3475ba.js`](./nordic.atlas-nodes.0027.60479632cf3475ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.9851661d0f69418c.js`](./nordic.atlas-nodes.0028.9851661d0f69418c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.9c436b6ace08d21e.js`](./nordic.atlas-nodes.0029.9c436b6ace08d21e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.1ffb0f82a0d8e0b9.js`](./nordic.atlas-nodes.0030.1ffb0f82a0d8e0b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.1d1893b2bb09d8f6.js`](./nordic.atlas-nodes.0031.1d1893b2bb09d8f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.562470fa58c72942.js`](./nordic.atlas-nodes.0032.562470fa58c72942.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.fe0e3b898715adb9.js`](./nordic.atlas-nodes.0033.fe0e3b898715adb9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.fc338fcd43345dd6.js`](./nordic.atlas-nodes.0034.fc338fcd43345dd6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.a492bd1bbbae0682.js`](./nordic.atlas-nodes.0035.a492bd1bbbae0682.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.daf7d30f098d1285.js`](./nordic.atlas-nodes.0036.daf7d30f098d1285.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.df6eaf9eb86ad954.js`](./nordic.atlas-nodes.0037.df6eaf9eb86ad954.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.df729cc06475a08c.js`](./nordic.atlas-nodes.0038.df729cc06475a08c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.0589313cc461d93a.js`](./nordic.atlas-nodes.0039.0589313cc461d93a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.083469caeb8c15c1.js`](./nordic.atlas-nodes.0040.083469caeb8c15c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.45c9a1023fd8df14.js`](./nordic.atlas-nodes.0041.45c9a1023fd8df14.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.61797540df782869.js`](./nordic.atlas-nodes.0042.61797540df782869.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.3cd8f28a6b815ff6.js`](./nordic.atlas-nodes.0043.3cd8f28a6b815ff6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.a5d82c2d2c54cc28.js`](./nordic.atlas-nodes.0044.a5d82c2d2c54cc28.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.b6b1c39086f6c16f.js`](./nordic.atlas-nodes.0045.b6b1c39086f6c16f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.9f34ecbd7cd2bf60.js`](./nordic.atlas-nodes.0046.9f34ecbd7cd2bf60.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.338474b3879b61bd.js`](./nordic.atlas-nodes.0047.338474b3879b61bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.1d83bc36467c2845.js`](./nordic.atlas-nodes.0048.1d83bc36467c2845.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.8822ff2d1da09eb2.js`](./nordic.atlas-nodes.0049.8822ff2d1da09eb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.0c412d32dbfabef8.js`](./nordic.atlas-nodes.0050.0c412d32dbfabef8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.66cc9665756389a1.js`](./nordic.atlas-nodes.0051.66cc9665756389a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.5ca873ccddcb39a1.js`](./nordic.atlas-nodes.0052.5ca873ccddcb39a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.fb89de28b573354c.js`](./nordic.atlas-nodes.0053.fb89de28b573354c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.6bc4a9d9a8e21dc3.js`](./nordic.atlas-nodes.0054.6bc4a9d9a8e21dc3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.727631ff9e71634f.js`](./nordic.atlas-nodes.0055.727631ff9e71634f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.822a1a1eebfa12fc.js`](./nordic.atlas-nodes.0056.822a1a1eebfa12fc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.3fac9f2aa80a5d89.js`](./nordic.atlas-nodes.0057.3fac9f2aa80a5d89.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.e164375c79e48185.js`](./nordic.atlas-nodes.0058.e164375c79e48185.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.1899c080ccd6754d.js`](./nordic.atlas-nodes.0059.1899c080ccd6754d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.5345ce3e20ed127b.js`](./nordic.atlas-nodes.0060.5345ce3e20ed127b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.291438229d9d0e49.js`](./nordic.atlas-nodes.0061.291438229d9d0e49.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.e267d8432854b855.js`](./nordic.atlas-nodes.0062.e267d8432854b855.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.bd5a8cccfd34390c.js`](./nordic.atlas-nodes.0063.bd5a8cccfd34390c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.f7787135ab4812f3.js`](./nordic.atlas-nodes.0064.f7787135ab4812f3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.8a2e94abea32b269.js`](./nordic.atlas-nodes.0065.8a2e94abea32b269.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.bcdd6f6e05a4e8f5.js`](./nordic.atlas-nodes.0066.bcdd6f6e05a4e8f5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.6b342266cc56dec7.js`](./nordic.atlas-nodes.0067.6b342266cc56dec7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.194797926eeced1d.js`](./nordic.atlas-nodes.0068.194797926eeced1d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.3432a8b8a18b216e.js`](./nordic.atlas-nodes.0069.3432a8b8a18b216e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.2aeb4272fcb4878f.js`](./nordic.atlas-nodes.0070.2aeb4272fcb4878f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.c5e260c9099ebcde.js`](./nordic.atlas-nodes.0071.c5e260c9099ebcde.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.1b29ae53f780979d.js`](./nordic.atlas-nodes.0072.1b29ae53f780979d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.6a90e0b1f539268d.js`](./nordic.atlas-nodes.0073.6a90e0b1f539268d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.88f52aae6e9b0a0f.js`](./nordic.atlas-nodes.0074.88f52aae6e9b0a0f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.e1fd78c75e268712.js`](./nordic.atlas-nodes.0075.e1fd78c75e268712.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.31a3a20def75a6e0.js`](./nordic.atlas-nodes.0076.31a3a20def75a6e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.fd2fc32acdfbd896.js`](./nordic.atlas-nodes.0077.fd2fc32acdfbd896.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.d778925a486f1768.js`](./nordic.atlas-nodes.0078.d778925a486f1768.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.507442aa54154b8e.js`](./nordic.atlas-nodes.0079.507442aa54154b8e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.0623349fda7b32ec.js`](./nordic.atlas-nodes.0080.0623349fda7b32ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.be92da5745b70424.js`](./nordic.atlas-nodes.0081.be92da5745b70424.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.35737b802751f64b.js`](./nordic.atlas-nodes.0082.35737b802751f64b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.943d15cecc145ff9.js`](./nordic.atlas-nodes.0083.943d15cecc145ff9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.adc762471642641c.js`](./nordic.atlas-nodes.0084.adc762471642641c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.7ba4bb4ca16eb0f1.js`](./nordic.atlas-nodes.0085.7ba4bb4ca16eb0f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.585189d508f0e327.js`](./nordic.atlas-nodes.0086.585189d508f0e327.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.b5896cce9f39bcc8.js`](./nordic.atlas-nodes.0087.b5896cce9f39bcc8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.0cee140e5793da6b.js`](./nordic.atlas-nodes.0088.0cee140e5793da6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.b45103d1d34303a5.js`](./nordic.atlas-nodes.0089.b45103d1d34303a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.b489aa09257ef2bc.js`](./nordic.atlas-nodes.0090.b489aa09257ef2bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.32e299011aab9549.js`](./nordic.atlas-nodes.0091.32e299011aab9549.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.a2d734ff972e98eb.js`](./nordic.atlas-nodes.0092.a2d734ff972e98eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.afa011be40443155.js`](./nordic.atlas-nodes.0093.afa011be40443155.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.b5d62e50385cde1b.js`](./nordic.atlas-nodes.0094.b5d62e50385cde1b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.5b8252a5fb989bcd.js`](./nordic.atlas-nodes.0095.5b8252a5fb989bcd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.d2d72cea076eb908.js`](./nordic.atlas-nodes.0096.d2d72cea076eb908.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.6003260de451b17c.js`](./nordic.atlas-nodes.0097.6003260de451b17c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.b512ac3061d86cf8.js`](./nordic.atlas-nodes.0098.b512ac3061d86cf8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.aa27ab87df815b6e.js`](./nordic.atlas-nodes.0099.aa27ab87df815b6e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.5735e623098bf720.js`](./nordic.atlas-nodes.0100.5735e623098bf720.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.28cb0d9e21f04138.js`](./nordic.atlas-nodes.0101.28cb0d9e21f04138.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.081d876e2e6b7a83.js`](./nordic.atlas-nodes.0102.081d876e2e6b7a83.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.cb55e2f6210d0c95.js`](./nordic.atlas-nodes.0103.cb55e2f6210d0c95.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.24bed05646f567e3.js`](./nordic.atlas-nodes.0104.24bed05646f567e3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.03b40f5cca532e9f.js`](./nordic.atlas-nodes.0105.03b40f5cca532e9f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.e2cd659658c2b3be.js`](./nordic.atlas-nodes.0106.e2cd659658c2b3be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.1a29ed15a7f28b5a.js`](./nordic.atlas-nodes.0107.1a29ed15a7f28b5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.52c84fcc4f9ca455.js`](./nordic.atlas-nodes.0108.52c84fcc4f9ca455.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.bf273176b5f43bd8.js`](./nordic.atlas-nodes.0109.bf273176b5f43bd8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.65e105d7621d5031.js`](./nordic.atlas-nodes.0110.65e105d7621d5031.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.7dba760e46cd517d.js`](./nordic.atlas-nodes.0111.7dba760e46cd517d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.c8d123de59033062.js`](./nordic.atlas-nodes.0112.c8d123de59033062.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.97a52cd4ce297164.js`](./nordic.atlas-nodes.0113.97a52cd4ce297164.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.2df662eef8053655.js`](./nordic.atlas-nodes.0114.2df662eef8053655.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.272d593e09672ce6.js`](./nordic.atlas-nodes.0115.272d593e09672ce6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.a209a5e95aea0597.js`](./nordic.atlas-nodes.0116.a209a5e95aea0597.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.39f885fc5ee6cadc.js`](./nordic.atlas-nodes.0117.39f885fc5ee6cadc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.283af01a922b6959.js`](./nordic.atlas-nodes.0118.283af01a922b6959.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.670ebef5b21f7105.js`](./nordic.atlas-nodes.0119.670ebef5b21f7105.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.8381441cedb7ddff.js`](./nordic.atlas-nodes.0120.8381441cedb7ddff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.0addcd13d65542fe.js`](./nordic.atlas-nodes.0121.0addcd13d65542fe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.4aa13b778ccfe5fa.js`](./nordic.atlas-nodes.0122.4aa13b778ccfe5fa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.4201f9df3353a5db.js`](./nordic.atlas-nodes.0123.4201f9df3353a5db.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.11a93a38360a1f52.js`](./nordic.atlas-nodes.0124.11a93a38360a1f52.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.d05390efc39e9c2b.js`](./nordic.atlas-nodes.0125.d05390efc39e9c2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.d3a91a5f6bbbd49e.js`](./nordic.atlas-nodes.0126.d3a91a5f6bbbd49e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.40f9ec4ca9bb16c2.js`](./nordic.atlas-nodes.0127.40f9ec4ca9bb16c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.18fc22b5e5a7249a.js`](./nordic.atlas-nodes.0128.18fc22b5e5a7249a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.dfbf9de2126743e5.js`](./nordic.atlas-nodes.0129.dfbf9de2126743e5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.5b67104072fd779d.js`](./nordic.atlas-nodes.0130.5b67104072fd779d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.f51e0f96d33a6936.js`](./nordic.atlas-nodes.0131.f51e0f96d33a6936.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.e0ce049fc55d66c6.js`](./nordic.atlas-nodes.0132.e0ce049fc55d66c6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.fe72f4d1f45c8d85.js`](./nordic.atlas-nodes.0133.fe72f4d1f45c8d85.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.0f6e75ccb0f90467.js`](./nordic.atlas-nodes.0134.0f6e75ccb0f90467.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.be7ee5f4dc714ca2.js`](./nordic.atlas-nodes.0135.be7ee5f4dc714ca2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.92fc737a2e99d006.js`](./nordic.atlas-nodes.0136.92fc737a2e99d006.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.d323b1b61b12103d.js`](./nordic.atlas-nodes.0137.d323b1b61b12103d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.c3181506f427a7d7.js`](./nordic.atlas-nodes.0138.c3181506f427a7d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.6e5789f3a80e0ab9.js`](./nordic.atlas-nodes.0139.6e5789f3a80e0ab9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.3ff0370aa178b532.js`](./nordic.atlas-nodes.0140.3ff0370aa178b532.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.d7deae2fac0eec48.js`](./nordic.atlas-nodes.0141.d7deae2fac0eec48.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.f26075195a3b3e9a.js`](./nordic.atlas-nodes.0142.f26075195a3b3e9a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.dd49644ce9c24608.js`](./nordic.atlas-nodes.0143.dd49644ce9c24608.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.ed19334d1037b3d0.js`](./nordic.atlas-nodes.0144.ed19334d1037b3d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.75cb9eb9cf52e4e3.js`](./nordic.atlas-nodes.0145.75cb9eb9cf52e4e3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.7fff720678e9b4b2.js`](./nordic.atlas-nodes.0146.7fff720678e9b4b2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.dc6326a02107964b.js`](./nordic.atlas-nodes.0147.dc6326a02107964b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.f90cfaec2ed6439d.js`](./nordic.atlas-nodes.0148.f90cfaec2ed6439d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.79453ff91ff693cc.js`](./nordic.atlas-nodes.0149.79453ff91ff693cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.b4f9ebd172b05351.js`](./nordic.atlas-nodes.0150.b4f9ebd172b05351.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.ee948116d570425c.js`](./nordic.atlas-nodes.0151.ee948116d570425c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.4aae95018dc494ac.js`](./nordic.atlas-nodes.0152.4aae95018dc494ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.2f1dca36dbfa8202.js`](./nordic.atlas-nodes.0153.2f1dca36dbfa8202.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.4cf770af75b2973b.js`](./nordic.atlas-nodes.0154.4cf770af75b2973b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.b90e2aa7016e7e78.js`](./nordic.atlas-nodes.0155.b90e2aa7016e7e78.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.bf442e2af1326ba5.js`](./nordic.atlas-nodes.0156.bf442e2af1326ba5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.a50eb738484393e4.js`](./nordic.atlas-nodes.0157.a50eb738484393e4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.c2262b1279727c8f.js`](./nordic.atlas-nodes.0158.c2262b1279727c8f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.670f3e18e1b56550.js`](./nordic.atlas-nodes.0159.670f3e18e1b56550.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.17dcd8b2c0f6070d.js`](./nordic.atlas-nodes.0160.17dcd8b2c0f6070d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.208f2bc5267e7d45.js`](./nordic.atlas-nodes.0161.208f2bc5267e7d45.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.df093265fe745108.js`](./nordic.atlas-nodes.0162.df093265fe745108.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.0eec406ac159276f.js`](./nordic.atlas-nodes.0163.0eec406ac159276f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.bb3a1edd947ee9d7.js`](./nordic.atlas-nodes.0164.bb3a1edd947ee9d7.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.4d70e40853b39496.js`](./nordic.atlas-details.0165.4d70e40853b39496.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.2d293bbe38a44ddd.js`](./nordic.atlas-details.0166.2d293bbe38a44ddd.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.e3e35e2dbb870caa.js`](./nordic.atlas-details.0167.e3e35e2dbb870caa.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.44c1405a57d7d8d1.js`](./nordic.atlas-details.0168.44c1405a57d7d8d1.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.5581e765315065bf.js`](./nordic.atlas-details.0169.5581e765315065bf.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.723007942a5fb02d.js`](./nordic.atlas-details.0170.723007942a5fb02d.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.374b36c361c65f26.js`](./nordic.atlas-details.0171.374b36c361c65f26.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.5f17e082fff18d07.js`](./nordic.atlas-details.0172.5f17e082fff18d07.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.0ac2e63ebc430842.js`](./nordic.atlas-details.0173.0ac2e63ebc430842.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.ec4537cb0ff45f34.js`](./nordic.atlas-details.0174.ec4537cb0ff45f34.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.44e70bacbb593091.js`](./nordic.atlas-details.0175.44e70bacbb593091.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.041ce2dbdf113aa3.js`](./nordic.atlas-details.0176.041ce2dbdf113aa3.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.73509ef7e3f98e00.js`](./nordic.atlas-details.0177.73509ef7e3f98e00.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.7c83daef25c1e5ae.js`](./nordic.atlas-details.0178.7c83daef25c1e5ae.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.98b8db011a2d0522.js`](./nordic.atlas-details.0179.98b8db011a2d0522.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.aab33b686642c08e.js`](./nordic.atlas-details.0180.aab33b686642c08e.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.32f7b8ad6a41bcbd.js`](./nordic.atlas-details.0181.32f7b8ad6a41bcbd.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.04cc4c6057983de8.js`](./nordic.atlas-details.0182.04cc4c6057983de8.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.25fae68978461fe0.js`](./nordic.atlas-details.0183.25fae68978461fe0.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.56e63fdef61b2379.js`](./nordic.atlas-details.0184.56e63fdef61b2379.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.46dc686d5fde0bc8.js`](./nordic.atlas-details.0185.46dc686d5fde0bc8.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.dc62a297028f01f9.js`](./nordic.atlas-details.0186.dc62a297028f01f9.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.a938633cd309daa7.js`](./nordic.atlas-details.0187.a938633cd309daa7.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.d0ae525972e19110.js`](./nordic.atlas-details.0188.d0ae525972e19110.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.6ccda747a4b20f73.js`](./nordic.atlas-details.0189.6ccda747a4b20f73.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.b671c08ebc94289a.js`](./nordic.atlas-details.0190.b671c08ebc94289a.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.ead212a474be6717.js`](./nordic.atlas-details.0191.ead212a474be6717.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.d9dbef79d5e64d37.js`](./nordic.atlas-details.0192.d9dbef79d5e64d37.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.51a0c5399e4dec90.js`](./nordic.atlas-details.0193.51a0c5399e4dec90.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.16e51ef4c29a6b48.js`](./nordic.atlas-details.0194.16e51ef4c29a6b48.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.7dc64221c76aa295.js`](./nordic.atlas-details.0195.7dc64221c76aa295.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.a8f8266a9e97f92f.js`](./nordic.atlas-details.0196.a8f8266a9e97f92f.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.d698420bdfddd801.js`](./nordic.atlas-details.0197.d698420bdfddd801.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.feda03ff8c432567.js`](./nordic.atlas-details.0198.feda03ff8c432567.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.88db4cfaa999594b.js`](./nordic.atlas-details.0199.88db4cfaa999594b.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.86b9e78aabfb14d7.js`](./nordic.atlas-details.0200.86b9e78aabfb14d7.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.6ca912eccb8b0c52.js`](./nordic.atlas-details.0201.6ca912eccb8b0c52.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.f2fb9d742e850a4d.js`](./nordic.atlas-details.0202.f2fb9d742e850a4d.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.7e4ad7f3b9fa7daf.js`](./nordic.atlas-details.0203.7e4ad7f3b9fa7daf.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.ba1bc653c29cae58.js`](./nordic.atlas-details.0204.ba1bc653c29cae58.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.198113064ec35ddd.js`](./nordic.atlas-details.0205.198113064ec35ddd.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.ca026daaa4238e6d.js`](./nordic.atlas-details.0206.ca026daaa4238e6d.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.52fcfdfa0078e434.js`](./nordic.atlas-details.0207.52fcfdfa0078e434.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.b75e7ed5bfade915.js`](./nordic.atlas-details.0208.b75e7ed5bfade915.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.edad5149d8ce0862.js`](./nordic.atlas-details.0209.edad5149d8ce0862.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.12e84859e8503e2f.js`](./nordic.atlas-details.0210.12e84859e8503e2f.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.4fa5e27211d24dda.js`](./nordic.atlas-details.0211.4fa5e27211d24dda.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.70dab759125bc94f.js`](./nordic.atlas-details.0212.70dab759125bc94f.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.1c0a23e5dd229178.js`](./nordic.atlas-details.0213.1c0a23e5dd229178.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.6d437f52f6c23c7e.js`](./nordic.atlas-details.0214.6d437f52f6c23c7e.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.00e6614b70cadd23.js`](./nordic.atlas-details.0215.00e6614b70cadd23.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.b6dd66a7f239e184.js`](./nordic.atlas-details.0216.b6dd66a7f239e184.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.21af239d59f44ec7.js`](./nordic.atlas-details.0217.21af239d59f44ec7.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.cadc04540617a288.js`](./nordic.atlas-details.0218.cadc04540617a288.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.8c2aa911f555da0a.js`](./nordic.atlas-details.0219.8c2aa911f555da0a.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.0fa36841e82b2bf9.js`](./nordic.atlas-details.0220.0fa36841e82b2bf9.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.da612d470cbc5b89.js`](./nordic.atlas-details.0221.da612d470cbc5b89.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.d6e624c9c7e49e7e.js`](./nordic.atlas-details.0222.d6e624c9c7e49e7e.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.ab920528c6b39529.js`](./nordic.atlas-details.0223.ab920528c6b39529.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.2de27d640085c0c1.js`](./nordic.atlas-details.0224.2de27d640085c0c1.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.1d9f71743fd56a38.js`](./nordic.atlas-details.0225.1d9f71743fd56a38.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.2013ea2e63459b98.js`](./nordic.atlas-details.0226.2013ea2e63459b98.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.5dbd3e3c7a3986b2.js`](./nordic.atlas-details.0227.5dbd3e3c7a3986b2.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.8cca820ae351ae88.js`](./nordic.atlas-details.0228.8cca820ae351ae88.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.dae922ae18aef569.js`](./nordic.atlas-edges.0229.dae922ae18aef569.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.8e63efcbceb337c9.js`](./nordic.atlas-sequences.0230.8e63efcbceb337c9.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.c7ac88e72a6f6d20.js`](./nordic.atlas-indexes.0231.c7ac88e72a6f6d20.js)
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


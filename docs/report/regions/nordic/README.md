# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-08` from Homo
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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.db6d3ec8209ffc78.js`](./nordic.atlas-provenance.0000.db6d3ec8209ffc78.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.7287a185de9d0947.js`](./nordic.atlas-nodes.0001.7287a185de9d0947.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.84a277a9a8afd190.js`](./nordic.atlas-nodes.0002.84a277a9a8afd190.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.d57bb9c8faf548cc.js`](./nordic.atlas-nodes.0003.d57bb9c8faf548cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.db573fbb002bbe14.js`](./nordic.atlas-nodes.0004.db573fbb002bbe14.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.e073952b1de245aa.js`](./nordic.atlas-nodes.0005.e073952b1de245aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.a3aec9543f44b228.js`](./nordic.atlas-nodes.0006.a3aec9543f44b228.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.5bbcf47883932680.js`](./nordic.atlas-nodes.0007.5bbcf47883932680.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.3e1720b339145090.js`](./nordic.atlas-nodes.0008.3e1720b339145090.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.0ea06fb0c9e826d7.js`](./nordic.atlas-nodes.0009.0ea06fb0c9e826d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.70a9890bc2edb50e.js`](./nordic.atlas-nodes.0010.70a9890bc2edb50e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.f11f40df9d08f036.js`](./nordic.atlas-nodes.0011.f11f40df9d08f036.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.371effc053d6b690.js`](./nordic.atlas-nodes.0012.371effc053d6b690.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.f3d3f2a321c60d22.js`](./nordic.atlas-nodes.0013.f3d3f2a321c60d22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.ede1f0d61ded07b6.js`](./nordic.atlas-nodes.0014.ede1f0d61ded07b6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.8691f721f25ebfa2.js`](./nordic.atlas-nodes.0015.8691f721f25ebfa2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.5aafb84a7488d362.js`](./nordic.atlas-nodes.0016.5aafb84a7488d362.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.a15f487909cb8afd.js`](./nordic.atlas-nodes.0017.a15f487909cb8afd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.dcfdafbaced9f184.js`](./nordic.atlas-nodes.0018.dcfdafbaced9f184.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.3cd0058c93176621.js`](./nordic.atlas-nodes.0019.3cd0058c93176621.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.a75d2edaaeaaa93d.js`](./nordic.atlas-nodes.0020.a75d2edaaeaaa93d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.e14c5bf1dc28b89c.js`](./nordic.atlas-nodes.0021.e14c5bf1dc28b89c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.db17fdfe8022594b.js`](./nordic.atlas-nodes.0022.db17fdfe8022594b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.435641fb47e95d4c.js`](./nordic.atlas-nodes.0023.435641fb47e95d4c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.eb0cbfa1a5507c51.js`](./nordic.atlas-nodes.0024.eb0cbfa1a5507c51.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.fae36fa4bf7795e8.js`](./nordic.atlas-nodes.0025.fae36fa4bf7795e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.90d5d61b2049bda9.js`](./nordic.atlas-nodes.0026.90d5d61b2049bda9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.86e92732688de653.js`](./nordic.atlas-nodes.0027.86e92732688de653.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.c1fef3e1ab56ce85.js`](./nordic.atlas-nodes.0028.c1fef3e1ab56ce85.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.72dd3234efc39ec0.js`](./nordic.atlas-nodes.0029.72dd3234efc39ec0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.f8d6f5d240c3e5e3.js`](./nordic.atlas-nodes.0030.f8d6f5d240c3e5e3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.a46d3fe7c4467bb8.js`](./nordic.atlas-nodes.0031.a46d3fe7c4467bb8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.b5a1f9e9f23c95ae.js`](./nordic.atlas-nodes.0032.b5a1f9e9f23c95ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.680e2519da255354.js`](./nordic.atlas-nodes.0033.680e2519da255354.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.dcf4e3c8f652e25e.js`](./nordic.atlas-nodes.0034.dcf4e3c8f652e25e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.979b2113b72d98a7.js`](./nordic.atlas-nodes.0035.979b2113b72d98a7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.0691f8abd68112ed.js`](./nordic.atlas-nodes.0036.0691f8abd68112ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.487fd6e8aa9935c2.js`](./nordic.atlas-nodes.0037.487fd6e8aa9935c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.507458d147b852ed.js`](./nordic.atlas-nodes.0038.507458d147b852ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.2a2b86b66cb57117.js`](./nordic.atlas-nodes.0039.2a2b86b66cb57117.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.24cfb4036f6a8acb.js`](./nordic.atlas-nodes.0040.24cfb4036f6a8acb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.1236c48171ddb4d1.js`](./nordic.atlas-nodes.0041.1236c48171ddb4d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.640ebdf559a80479.js`](./nordic.atlas-nodes.0042.640ebdf559a80479.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.d5b20c2c02e08711.js`](./nordic.atlas-nodes.0043.d5b20c2c02e08711.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.9aa9153a2a6801dc.js`](./nordic.atlas-nodes.0044.9aa9153a2a6801dc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.acd8867869d0d59a.js`](./nordic.atlas-nodes.0045.acd8867869d0d59a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.f58aea929ca47056.js`](./nordic.atlas-nodes.0046.f58aea929ca47056.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.601033c9a7a797f1.js`](./nordic.atlas-nodes.0047.601033c9a7a797f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.363ad2282c9121ef.js`](./nordic.atlas-nodes.0048.363ad2282c9121ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.8518dd70a2963c01.js`](./nordic.atlas-nodes.0049.8518dd70a2963c01.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.87109f60dfd30dc8.js`](./nordic.atlas-nodes.0050.87109f60dfd30dc8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.22907455b841809b.js`](./nordic.atlas-nodes.0051.22907455b841809b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.f61ec8e88ea57d4d.js`](./nordic.atlas-nodes.0052.f61ec8e88ea57d4d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.77aef5291acdbe80.js`](./nordic.atlas-nodes.0053.77aef5291acdbe80.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.8374a6436687800a.js`](./nordic.atlas-nodes.0054.8374a6436687800a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.dfa624fb138e2c67.js`](./nordic.atlas-nodes.0055.dfa624fb138e2c67.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.5c45a3a5a7326d36.js`](./nordic.atlas-nodes.0056.5c45a3a5a7326d36.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.b9213289398ee87c.js`](./nordic.atlas-nodes.0057.b9213289398ee87c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.702852d28b25008f.js`](./nordic.atlas-nodes.0058.702852d28b25008f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.bab44021775ed8d5.js`](./nordic.atlas-nodes.0059.bab44021775ed8d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.89a4f011af3d6e70.js`](./nordic.atlas-nodes.0060.89a4f011af3d6e70.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.71358276b20ed028.js`](./nordic.atlas-nodes.0061.71358276b20ed028.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.28ee691d7905cf03.js`](./nordic.atlas-nodes.0062.28ee691d7905cf03.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.7c305e3a1f13ee43.js`](./nordic.atlas-nodes.0063.7c305e3a1f13ee43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.1643c9e83702b5b4.js`](./nordic.atlas-nodes.0064.1643c9e83702b5b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.0e6758d66436b42a.js`](./nordic.atlas-nodes.0065.0e6758d66436b42a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.243fd9862936c432.js`](./nordic.atlas-nodes.0066.243fd9862936c432.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.1271d4d301847cc4.js`](./nordic.atlas-nodes.0067.1271d4d301847cc4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.ced3b87c1ef7148b.js`](./nordic.atlas-nodes.0068.ced3b87c1ef7148b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.d0151dbecdfcc246.js`](./nordic.atlas-nodes.0069.d0151dbecdfcc246.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.7cf56453df25410a.js`](./nordic.atlas-nodes.0070.7cf56453df25410a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.dd7c2cd2f1092d61.js`](./nordic.atlas-nodes.0071.dd7c2cd2f1092d61.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.6e7e24d75bc33aca.js`](./nordic.atlas-nodes.0072.6e7e24d75bc33aca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.2faa823fefa6acd0.js`](./nordic.atlas-nodes.0073.2faa823fefa6acd0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.2e95b4e6276a55b4.js`](./nordic.atlas-nodes.0074.2e95b4e6276a55b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.a7ffb539e4e17869.js`](./nordic.atlas-nodes.0075.a7ffb539e4e17869.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.b766d4395bc05969.js`](./nordic.atlas-nodes.0076.b766d4395bc05969.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.a8c4a8a8d701e832.js`](./nordic.atlas-nodes.0077.a8c4a8a8d701e832.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.9c155dc3260c6bf9.js`](./nordic.atlas-nodes.0078.9c155dc3260c6bf9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.1856e6c05780427f.js`](./nordic.atlas-nodes.0079.1856e6c05780427f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.5bd6896921707e8d.js`](./nordic.atlas-nodes.0080.5bd6896921707e8d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.2f79623579a316cb.js`](./nordic.atlas-nodes.0081.2f79623579a316cb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.6fdd75f1dd1b5b51.js`](./nordic.atlas-nodes.0082.6fdd75f1dd1b5b51.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.42feb8de5eec6b21.js`](./nordic.atlas-nodes.0083.42feb8de5eec6b21.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.f267ee11000512b3.js`](./nordic.atlas-nodes.0084.f267ee11000512b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.9d38122b70931eda.js`](./nordic.atlas-nodes.0085.9d38122b70931eda.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.ec3a8265c4e162c9.js`](./nordic.atlas-nodes.0086.ec3a8265c4e162c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.622bc7eb816bcee1.js`](./nordic.atlas-nodes.0087.622bc7eb816bcee1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.0e54b55aed6b89f8.js`](./nordic.atlas-nodes.0088.0e54b55aed6b89f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.98d354f4cdb58179.js`](./nordic.atlas-nodes.0089.98d354f4cdb58179.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.ecfb1bd7d1498463.js`](./nordic.atlas-nodes.0090.ecfb1bd7d1498463.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.56001b57d8f1a2b8.js`](./nordic.atlas-nodes.0091.56001b57d8f1a2b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.2ecf3871fe9ea167.js`](./nordic.atlas-nodes.0092.2ecf3871fe9ea167.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.2c7d3f29a3bf9881.js`](./nordic.atlas-nodes.0093.2c7d3f29a3bf9881.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.acf0141d97f5ce68.js`](./nordic.atlas-nodes.0094.acf0141d97f5ce68.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.5642e83df4ea6b97.js`](./nordic.atlas-nodes.0095.5642e83df4ea6b97.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.903882844801f28f.js`](./nordic.atlas-nodes.0096.903882844801f28f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.a8d2f1a85d263abf.js`](./nordic.atlas-nodes.0097.a8d2f1a85d263abf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.c282ec0253a62a45.js`](./nordic.atlas-nodes.0098.c282ec0253a62a45.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.5ac22a9141054e58.js`](./nordic.atlas-nodes.0099.5ac22a9141054e58.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.7bb725cd9b9823aa.js`](./nordic.atlas-nodes.0100.7bb725cd9b9823aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.da13556820fb2a25.js`](./nordic.atlas-nodes.0101.da13556820fb2a25.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.5e1801e36680b2f6.js`](./nordic.atlas-nodes.0102.5e1801e36680b2f6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.ced667021773ce89.js`](./nordic.atlas-nodes.0103.ced667021773ce89.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.b5320c7f01ae1ce9.js`](./nordic.atlas-nodes.0104.b5320c7f01ae1ce9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.093c895c0c7d5ed5.js`](./nordic.atlas-nodes.0105.093c895c0c7d5ed5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.d7af91ab3de89b08.js`](./nordic.atlas-nodes.0106.d7af91ab3de89b08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.3aac5c2e5cb46df9.js`](./nordic.atlas-nodes.0107.3aac5c2e5cb46df9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.cf3766bcc0f19e4f.js`](./nordic.atlas-nodes.0108.cf3766bcc0f19e4f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.8304938691b969c1.js`](./nordic.atlas-nodes.0109.8304938691b969c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.bf3c1291034674ae.js`](./nordic.atlas-nodes.0110.bf3c1291034674ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.c54345ddff5548a3.js`](./nordic.atlas-nodes.0111.c54345ddff5548a3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.33e8e41c2ee3e1c5.js`](./nordic.atlas-nodes.0112.33e8e41c2ee3e1c5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.eaa54e845b787f52.js`](./nordic.atlas-nodes.0113.eaa54e845b787f52.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.a33d817fdbadaa34.js`](./nordic.atlas-nodes.0114.a33d817fdbadaa34.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.2eade86cee69714f.js`](./nordic.atlas-nodes.0115.2eade86cee69714f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.6bde1c8e9fa34e39.js`](./nordic.atlas-nodes.0116.6bde1c8e9fa34e39.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.2e0a1c8d5bd806d3.js`](./nordic.atlas-nodes.0117.2e0a1c8d5bd806d3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.8a0b2592d4b22a31.js`](./nordic.atlas-nodes.0118.8a0b2592d4b22a31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.8e080ecdf2da6cff.js`](./nordic.atlas-nodes.0119.8e080ecdf2da6cff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.5b988971924dc53d.js`](./nordic.atlas-nodes.0120.5b988971924dc53d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.9cfe0b0d625746dd.js`](./nordic.atlas-nodes.0121.9cfe0b0d625746dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.4abee0a023207843.js`](./nordic.atlas-nodes.0122.4abee0a023207843.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.0184f3c95de9aa15.js`](./nordic.atlas-nodes.0123.0184f3c95de9aa15.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.e69fe809a8a4e4df.js`](./nordic.atlas-nodes.0124.e69fe809a8a4e4df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.ecbcf3fed2601eaa.js`](./nordic.atlas-nodes.0125.ecbcf3fed2601eaa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.9067cc910f7e64dc.js`](./nordic.atlas-nodes.0126.9067cc910f7e64dc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.bb5d2b0e441b9238.js`](./nordic.atlas-nodes.0127.bb5d2b0e441b9238.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.c891c5b2253a7485.js`](./nordic.atlas-nodes.0128.c891c5b2253a7485.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.a7a24093578bc239.js`](./nordic.atlas-nodes.0129.a7a24093578bc239.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.a4acb27773b4cb5e.js`](./nordic.atlas-nodes.0130.a4acb27773b4cb5e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.6012821a3a858c83.js`](./nordic.atlas-nodes.0131.6012821a3a858c83.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.4a2eed3ff583a8bf.js`](./nordic.atlas-nodes.0132.4a2eed3ff583a8bf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.14cd29a36ece73d7.js`](./nordic.atlas-nodes.0133.14cd29a36ece73d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.5ab3ef392b777709.js`](./nordic.atlas-nodes.0134.5ab3ef392b777709.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.10559066b2f843b4.js`](./nordic.atlas-nodes.0135.10559066b2f843b4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.d83d45434cb41a2f.js`](./nordic.atlas-nodes.0136.d83d45434cb41a2f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.dc30557efd9464d1.js`](./nordic.atlas-nodes.0137.dc30557efd9464d1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.895362d27d5b0afd.js`](./nordic.atlas-nodes.0138.895362d27d5b0afd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.1970bd09ea1b67d0.js`](./nordic.atlas-nodes.0139.1970bd09ea1b67d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.c26fa96de36b65c9.js`](./nordic.atlas-nodes.0140.c26fa96de36b65c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.aaa3e73d66e2c930.js`](./nordic.atlas-nodes.0141.aaa3e73d66e2c930.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.951ceb6f940460a4.js`](./nordic.atlas-nodes.0142.951ceb6f940460a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.0c13b7dfe46eebc8.js`](./nordic.atlas-nodes.0143.0c13b7dfe46eebc8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.7562a766499d4550.js`](./nordic.atlas-nodes.0144.7562a766499d4550.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.17a6a2335eb26c27.js`](./nordic.atlas-nodes.0145.17a6a2335eb26c27.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.49b950040557a4be.js`](./nordic.atlas-nodes.0146.49b950040557a4be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.7c547a4c1039642f.js`](./nordic.atlas-nodes.0147.7c547a4c1039642f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.10e1326d92b75695.js`](./nordic.atlas-nodes.0148.10e1326d92b75695.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.3fd7810be1372718.js`](./nordic.atlas-nodes.0149.3fd7810be1372718.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.8221ad9a0f3cb43b.js`](./nordic.atlas-nodes.0150.8221ad9a0f3cb43b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.238653307ff6d065.js`](./nordic.atlas-nodes.0151.238653307ff6d065.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.ef8ed4727f041f9a.js`](./nordic.atlas-nodes.0152.ef8ed4727f041f9a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.ed8996bdde5828b9.js`](./nordic.atlas-nodes.0153.ed8996bdde5828b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.68f51a133d4e1238.js`](./nordic.atlas-nodes.0154.68f51a133d4e1238.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.d41e2e174c6ff3d9.js`](./nordic.atlas-nodes.0155.d41e2e174c6ff3d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.6b9609cfb48ded65.js`](./nordic.atlas-nodes.0156.6b9609cfb48ded65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.f07faa180853e421.js`](./nordic.atlas-nodes.0157.f07faa180853e421.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.116c0ba4f3632f18.js`](./nordic.atlas-nodes.0158.116c0ba4f3632f18.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.ac1c1736d1671137.js`](./nordic.atlas-nodes.0159.ac1c1736d1671137.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.2a42c46890bba410.js`](./nordic.atlas-nodes.0160.2a42c46890bba410.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.661215bf4cb662f8.js`](./nordic.atlas-nodes.0161.661215bf4cb662f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.1a66f030d7bdc81b.js`](./nordic.atlas-nodes.0162.1a66f030d7bdc81b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.767c3780c5a2d7e7.js`](./nordic.atlas-nodes.0163.767c3780c5a2d7e7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.ba9493c1b725f375.js`](./nordic.atlas-nodes.0164.ba9493c1b725f375.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.096f0838451d285c.js`](./nordic.atlas-nodes.0165.096f0838451d285c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.6fd6ef0f220d0a8f.js`](./nordic.atlas-nodes.0166.6fd6ef0f220d0a8f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.5e75fb192ed62311.js`](./nordic.atlas-nodes.0167.5e75fb192ed62311.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.9d6fbb05b8ec83a9.js`](./nordic.atlas-nodes.0168.9d6fbb05b8ec83a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.37ec1bcecc8dfcf6.js`](./nordic.atlas-nodes.0169.37ec1bcecc8dfcf6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.fc1eb7645b9b36f1.js`](./nordic.atlas-nodes.0170.fc1eb7645b9b36f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0171.6945b35ec640d74e.js`](./nordic.atlas-nodes.0171.6945b35ec640d74e.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.dfdd733803b8aeef.js`](./nordic.atlas-details.0172.dfdd733803b8aeef.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.7030c5b4ae360d9a.js`](./nordic.atlas-details.0173.7030c5b4ae360d9a.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.5df2940d9d54be3f.js`](./nordic.atlas-details.0174.5df2940d9d54be3f.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.a5e96fe62b2a09b7.js`](./nordic.atlas-details.0175.a5e96fe62b2a09b7.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.b772fa0b989dabbe.js`](./nordic.atlas-details.0176.b772fa0b989dabbe.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.b7c81397e212cb50.js`](./nordic.atlas-details.0177.b7c81397e212cb50.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.826960cfc8aca6ec.js`](./nordic.atlas-details.0178.826960cfc8aca6ec.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.e2e3ef0157e0272d.js`](./nordic.atlas-details.0179.e2e3ef0157e0272d.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.1e40d1c9fc733a57.js`](./nordic.atlas-details.0180.1e40d1c9fc733a57.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.f86883aade1f2ed8.js`](./nordic.atlas-details.0181.f86883aade1f2ed8.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.737d25607cd2818f.js`](./nordic.atlas-details.0182.737d25607cd2818f.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.28bc5274051fbf59.js`](./nordic.atlas-details.0183.28bc5274051fbf59.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.7719dc5c3cc0436e.js`](./nordic.atlas-details.0184.7719dc5c3cc0436e.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.48d87bd8a55f1691.js`](./nordic.atlas-details.0185.48d87bd8a55f1691.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.36f5b760f3f8ef61.js`](./nordic.atlas-details.0186.36f5b760f3f8ef61.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.0bf0f5688fbf4c3e.js`](./nordic.atlas-details.0187.0bf0f5688fbf4c3e.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.eec9a49a6b8d2162.js`](./nordic.atlas-details.0188.eec9a49a6b8d2162.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.bd11b186632a9290.js`](./nordic.atlas-details.0189.bd11b186632a9290.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.c9cb3441e2daad88.js`](./nordic.atlas-details.0190.c9cb3441e2daad88.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.2fde3fddcd79ae34.js`](./nordic.atlas-details.0191.2fde3fddcd79ae34.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.6256935dcc34d2f9.js`](./nordic.atlas-details.0192.6256935dcc34d2f9.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.c17113a1bec55681.js`](./nordic.atlas-details.0193.c17113a1bec55681.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.6a37392817e5da82.js`](./nordic.atlas-details.0194.6a37392817e5da82.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.94b7d6b8eba557a3.js`](./nordic.atlas-details.0195.94b7d6b8eba557a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.f22903eda3654dd7.js`](./nordic.atlas-details.0196.f22903eda3654dd7.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.b876688d5b530b3c.js`](./nordic.atlas-details.0197.b876688d5b530b3c.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.258a624ff1b58bea.js`](./nordic.atlas-details.0198.258a624ff1b58bea.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.75d28ed4efe27018.js`](./nordic.atlas-details.0199.75d28ed4efe27018.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.384e6970292edc04.js`](./nordic.atlas-details.0200.384e6970292edc04.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.e4e233b7a02d0c3c.js`](./nordic.atlas-details.0201.e4e233b7a02d0c3c.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.90bd1e256df8831e.js`](./nordic.atlas-details.0202.90bd1e256df8831e.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.33cd3f39f0372371.js`](./nordic.atlas-details.0203.33cd3f39f0372371.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.a7eabfc9ff128390.js`](./nordic.atlas-details.0204.a7eabfc9ff128390.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.048cd3287b57250e.js`](./nordic.atlas-details.0205.048cd3287b57250e.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.b1af6c98489c28e5.js`](./nordic.atlas-details.0206.b1af6c98489c28e5.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.904c806449e2d5e1.js`](./nordic.atlas-details.0207.904c806449e2d5e1.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.85cf4ec13647fd56.js`](./nordic.atlas-details.0208.85cf4ec13647fd56.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.37fbc28a78633c0b.js`](./nordic.atlas-details.0209.37fbc28a78633c0b.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.dcb52b857d93ed50.js`](./nordic.atlas-details.0210.dcb52b857d93ed50.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.b3861776b2d6cb86.js`](./nordic.atlas-details.0211.b3861776b2d6cb86.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.9cd56968edbea2f2.js`](./nordic.atlas-details.0212.9cd56968edbea2f2.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.3e4b41a19f4b259b.js`](./nordic.atlas-details.0213.3e4b41a19f4b259b.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.29d3963cd1e881de.js`](./nordic.atlas-details.0214.29d3963cd1e881de.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.dae22835171a7698.js`](./nordic.atlas-details.0215.dae22835171a7698.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.66ea1d6ef201627f.js`](./nordic.atlas-details.0216.66ea1d6ef201627f.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.3ce02bf0ea2c10af.js`](./nordic.atlas-details.0217.3ce02bf0ea2c10af.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.e4ff61169c01e316.js`](./nordic.atlas-details.0218.e4ff61169c01e316.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.49b15b9afbafb845.js`](./nordic.atlas-details.0219.49b15b9afbafb845.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.3ccd7c73ad078368.js`](./nordic.atlas-details.0220.3ccd7c73ad078368.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.2a3a7ec967ba40e9.js`](./nordic.atlas-details.0221.2a3a7ec967ba40e9.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.e561e62d72e83855.js`](./nordic.atlas-details.0222.e561e62d72e83855.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.e971cfd243dc34a5.js`](./nordic.atlas-details.0223.e971cfd243dc34a5.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.1fae968f2496174d.js`](./nordic.atlas-details.0224.1fae968f2496174d.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.beae22a4d9b33627.js`](./nordic.atlas-details.0225.beae22a4d9b33627.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.7e7d9a722efa6e33.js`](./nordic.atlas-details.0226.7e7d9a722efa6e33.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.a10ebfd98d9cc669.js`](./nordic.atlas-details.0227.a10ebfd98d9cc669.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.f769824e178b4641.js`](./nordic.atlas-details.0228.f769824e178b4641.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.eb77c971c2a223c4.js`](./nordic.atlas-details.0229.eb77c971c2a223c4.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.e092811f982b6d23.js`](./nordic.atlas-details.0230.e092811f982b6d23.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.e0c9d26c1d9a258e.js`](./nordic.atlas-details.0231.e0c9d26c1d9a258e.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.f812cc8ff4ce8cdc.js`](./nordic.atlas-details.0232.f812cc8ff4ce8cdc.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.df1bce105bd37b9e.js`](./nordic.atlas-details.0233.df1bce105bd37b9e.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.8c0eb0ae2d2c159e.js`](./nordic.atlas-details.0234.8c0eb0ae2d2c159e.js)
- Static atlas data chunk: [`nordic.atlas-details.0235.047f4d19cd44fb5a.js`](./nordic.atlas-details.0235.047f4d19cd44fb5a.js)
- Static atlas data chunk: [`nordic.atlas-edges.0236.e079479108f5a6d7.js`](./nordic.atlas-edges.0236.e079479108f5a6d7.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0237.40f3b75631eccbe2.js`](./nordic.atlas-sequences.0237.40f3b75631eccbe2.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0238.63e41b13fa0640c1.js`](./nordic.atlas-indexes.0238.63e41b13fa0640c1.js)
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


# World Evidence Surface

This shared interactive map bundle was generated on `2026-09-29` from Homo
sapiens AADR `v66` plus any governed contextual and animal surfaces that
the active scope contract allows.

World is the governing publication surface. It keeps every published country inside one shared map and excludes Nordic-only context overlays that would look more complete than they really are at broader scale.

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
- The opening extent keeps a broad trans-Atlantic and Eurasian frame so the root publication surface reads as a parent scope rather than a Nordic detail page with a bigger title.

## Output Files

- Interactive map: [`world_map.html`](./world_map.html)
- Combined GeoJSON: [`world_samples.geojson`](./world_samples.geojson)
- Machine-readable summary: [`world_summary.json`](./world_summary.json)
- Map publication contract JSON: [`world_map_publication_contract.json`](./world_map_publication_contract.json)
- Map publication contract markdown: [`world_map_publication_contract.md`](./world_map_publication_contract.md)
- Point traceability JSON: [`world_point_traceability.json`](./world_point_traceability.json)
- Point traceability markdown: [`world_point_traceability.md`](./world_point_traceability.md)
- Nordic country boundaries: [`nordic_country_boundaries.geojson`](./nordic_country_boundaries.geojson)
- Animal locality GeoJSON: [`world_animal_localities.geojson`](./world_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`world_domesticated_animal_localities.geojson`](./world_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`world_comparator_animal_localities.geojson`](./world_comparator_animal_localities.geojson)
- Wild and progenitor animal locality GeoJSON: [`world_progenitor_animal_localities.geojson`](./world_progenitor_animal_localities.geojson)
- Animal atlas evidence CSV: [`world_animal_atlas_evidence.csv`](./world_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`world_animal_atlas_evidence.json`](./world_animal_atlas_evidence.json)
- Animal point traceability JSON: [`world_animal_point_traceability.json`](./world_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`world_map_assets.json`](./world_map_assets.json)
- Static atlas data chunk: [`world.atlas-provenance.0000.3b81217e41447e3d.js`](./world.atlas-provenance.0000.3b81217e41447e3d.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.57abb306371fe17c.js`](./world.atlas-nodes.0001.57abb306371fe17c.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.09e160b446554116.js`](./world.atlas-nodes.0002.09e160b446554116.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.a4ca2719608f9068.js`](./world.atlas-nodes.0003.a4ca2719608f9068.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.0f6c0d479590738c.js`](./world.atlas-nodes.0004.0f6c0d479590738c.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.b44c036820f3fcd3.js`](./world.atlas-nodes.0005.b44c036820f3fcd3.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.ed3f285102b45119.js`](./world.atlas-nodes.0006.ed3f285102b45119.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.6ac7065673986345.js`](./world.atlas-nodes.0007.6ac7065673986345.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.d1ab130893bc1731.js`](./world.atlas-nodes.0008.d1ab130893bc1731.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.0e2d77097696d39a.js`](./world.atlas-nodes.0009.0e2d77097696d39a.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.57404b1f154fbdeb.js`](./world.atlas-nodes.0010.57404b1f154fbdeb.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.357e029a5b553fa6.js`](./world.atlas-nodes.0011.357e029a5b553fa6.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.a994ff4ba7982cee.js`](./world.atlas-nodes.0012.a994ff4ba7982cee.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.388a74fbf545d215.js`](./world.atlas-nodes.0013.388a74fbf545d215.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.b8e8172b9318d7be.js`](./world.atlas-nodes.0014.b8e8172b9318d7be.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.c638f1a4c15feb52.js`](./world.atlas-nodes.0015.c638f1a4c15feb52.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.56555cf841e3ab4e.js`](./world.atlas-nodes.0016.56555cf841e3ab4e.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.460b4739e0d3e7bc.js`](./world.atlas-nodes.0017.460b4739e0d3e7bc.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.47768347e083a8d7.js`](./world.atlas-nodes.0018.47768347e083a8d7.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.d1715912453545da.js`](./world.atlas-nodes.0019.d1715912453545da.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.ce21596b9e298856.js`](./world.atlas-nodes.0020.ce21596b9e298856.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.5c3d20555b96d351.js`](./world.atlas-nodes.0021.5c3d20555b96d351.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.47599284e5fee109.js`](./world.atlas-nodes.0022.47599284e5fee109.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.e8dc6f5322f8250d.js`](./world.atlas-nodes.0023.e8dc6f5322f8250d.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.b75e7f73efcfdada.js`](./world.atlas-nodes.0024.b75e7f73efcfdada.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.b49f5d76f44970bf.js`](./world.atlas-nodes.0025.b49f5d76f44970bf.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.182d912f3c6cc4a1.js`](./world.atlas-nodes.0026.182d912f3c6cc4a1.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.7e40db2bad430b1b.js`](./world.atlas-nodes.0027.7e40db2bad430b1b.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.ee4a52f776ee529f.js`](./world.atlas-nodes.0028.ee4a52f776ee529f.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.8872b3d9bd9f99f4.js`](./world.atlas-nodes.0029.8872b3d9bd9f99f4.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.17e9ddc14b9bb6be.js`](./world.atlas-nodes.0030.17e9ddc14b9bb6be.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.acb0328c9d85c890.js`](./world.atlas-nodes.0031.acb0328c9d85c890.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.ef0f6752566a0fd5.js`](./world.atlas-nodes.0032.ef0f6752566a0fd5.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.7be99a785ee4d2e8.js`](./world.atlas-nodes.0033.7be99a785ee4d2e8.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.93d57843ea6b3a0b.js`](./world.atlas-nodes.0034.93d57843ea6b3a0b.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.ca0bbb4064165f9d.js`](./world.atlas-nodes.0035.ca0bbb4064165f9d.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.347304a63a0ce22a.js`](./world.atlas-nodes.0036.347304a63a0ce22a.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.9d6c965e13be20ee.js`](./world.atlas-nodes.0037.9d6c965e13be20ee.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.f92d1bc3a463b580.js`](./world.atlas-nodes.0038.f92d1bc3a463b580.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.4b4ea56dd372945a.js`](./world.atlas-nodes.0039.4b4ea56dd372945a.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.d563950dc94bc62b.js`](./world.atlas-nodes.0040.d563950dc94bc62b.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.4b2bce54cd9a1c75.js`](./world.atlas-nodes.0041.4b2bce54cd9a1c75.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.980847a91cc05a60.js`](./world.atlas-nodes.0042.980847a91cc05a60.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.03b8853d6ea2470c.js`](./world.atlas-nodes.0043.03b8853d6ea2470c.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.a4d73a4f2c8850fc.js`](./world.atlas-nodes.0044.a4d73a4f2c8850fc.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.51208bd20591ebae.js`](./world.atlas-nodes.0045.51208bd20591ebae.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.3d8e4a9fd6e7de77.js`](./world.atlas-nodes.0046.3d8e4a9fd6e7de77.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.0264bb767758c7e1.js`](./world.atlas-nodes.0047.0264bb767758c7e1.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.f9e80745ee118e58.js`](./world.atlas-nodes.0048.f9e80745ee118e58.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.dd44bd9d1beb1698.js`](./world.atlas-nodes.0049.dd44bd9d1beb1698.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.6d7633cc8339eee6.js`](./world.atlas-nodes.0050.6d7633cc8339eee6.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.2b642104ed2a9504.js`](./world.atlas-nodes.0051.2b642104ed2a9504.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.a17bcfb145132252.js`](./world.atlas-nodes.0052.a17bcfb145132252.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.8845e6304693d253.js`](./world.atlas-nodes.0053.8845e6304693d253.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.dcb750935bb6c282.js`](./world.atlas-nodes.0054.dcb750935bb6c282.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.f834a62cfc79d83e.js`](./world.atlas-nodes.0055.f834a62cfc79d83e.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.076e781e235b83ee.js`](./world.atlas-nodes.0056.076e781e235b83ee.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.137b85bc17d4165f.js`](./world.atlas-nodes.0057.137b85bc17d4165f.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.ae2614b8c856f66c.js`](./world.atlas-nodes.0058.ae2614b8c856f66c.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.0f995c3e1e391dea.js`](./world.atlas-nodes.0059.0f995c3e1e391dea.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.fde77ec077163f1c.js`](./world.atlas-nodes.0060.fde77ec077163f1c.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.4c005b44546c756d.js`](./world.atlas-nodes.0061.4c005b44546c756d.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.8e1f479f106e6aed.js`](./world.atlas-nodes.0062.8e1f479f106e6aed.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.03e597ecdb22d1bd.js`](./world.atlas-nodes.0063.03e597ecdb22d1bd.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.7c1bd8e94cc38ae9.js`](./world.atlas-nodes.0064.7c1bd8e94cc38ae9.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.51272e60f8a1efbb.js`](./world.atlas-nodes.0065.51272e60f8a1efbb.js)
- Static atlas data chunk: [`world.atlas-nodes.0066.565ca0cdcbccf3a4.js`](./world.atlas-nodes.0066.565ca0cdcbccf3a4.js)
- Static atlas data chunk: [`world.atlas-nodes.0067.cce498fd6cbf6975.js`](./world.atlas-nodes.0067.cce498fd6cbf6975.js)
- Static atlas data chunk: [`world.atlas-nodes.0068.128893544495a86a.js`](./world.atlas-nodes.0068.128893544495a86a.js)
- Static atlas data chunk: [`world.atlas-nodes.0069.76acfd337ecc1b16.js`](./world.atlas-nodes.0069.76acfd337ecc1b16.js)
- Static atlas data chunk: [`world.atlas-nodes.0070.a43cbb3a9815e176.js`](./world.atlas-nodes.0070.a43cbb3a9815e176.js)
- Static atlas data chunk: [`world.atlas-nodes.0071.db6eb18a25515d43.js`](./world.atlas-nodes.0071.db6eb18a25515d43.js)
- Static atlas data chunk: [`world.atlas-nodes.0072.e8262d339d1fc808.js`](./world.atlas-nodes.0072.e8262d339d1fc808.js)
- Static atlas data chunk: [`world.atlas-nodes.0073.dcba781920afa66b.js`](./world.atlas-nodes.0073.dcba781920afa66b.js)
- Static atlas data chunk: [`world.atlas-nodes.0074.40627c2739927336.js`](./world.atlas-nodes.0074.40627c2739927336.js)
- Static atlas data chunk: [`world.atlas-nodes.0075.aa6fa35ff1c56499.js`](./world.atlas-nodes.0075.aa6fa35ff1c56499.js)
- Static atlas data chunk: [`world.atlas-nodes.0076.716776424d546730.js`](./world.atlas-nodes.0076.716776424d546730.js)
- Static atlas data chunk: [`world.atlas-nodes.0077.a3b774b3bbcd01c6.js`](./world.atlas-nodes.0077.a3b774b3bbcd01c6.js)
- Static atlas data chunk: [`world.atlas-nodes.0078.25a553510542dd08.js`](./world.atlas-nodes.0078.25a553510542dd08.js)
- Static atlas data chunk: [`world.atlas-nodes.0079.72c0da1fb5a5e575.js`](./world.atlas-nodes.0079.72c0da1fb5a5e575.js)
- Static atlas data chunk: [`world.atlas-nodes.0080.1fdc079123e2886c.js`](./world.atlas-nodes.0080.1fdc079123e2886c.js)
- Static atlas data chunk: [`world.atlas-nodes.0081.42d0027d6eaf9a68.js`](./world.atlas-nodes.0081.42d0027d6eaf9a68.js)
- Static atlas data chunk: [`world.atlas-nodes.0082.00cb1706f1c82a9c.js`](./world.atlas-nodes.0082.00cb1706f1c82a9c.js)
- Static atlas data chunk: [`world.atlas-nodes.0083.ff8c448018105f61.js`](./world.atlas-nodes.0083.ff8c448018105f61.js)
- Static atlas data chunk: [`world.atlas-nodes.0084.440a4a41225c28e7.js`](./world.atlas-nodes.0084.440a4a41225c28e7.js)
- Static atlas data chunk: [`world.atlas-nodes.0085.2e4df068e13e29c9.js`](./world.atlas-nodes.0085.2e4df068e13e29c9.js)
- Static atlas data chunk: [`world.atlas-nodes.0086.30f2f924cc16febc.js`](./world.atlas-nodes.0086.30f2f924cc16febc.js)
- Static atlas data chunk: [`world.atlas-nodes.0087.ea208e47425e5dd0.js`](./world.atlas-nodes.0087.ea208e47425e5dd0.js)
- Static atlas data chunk: [`world.atlas-nodes.0088.1b4c43db848fc334.js`](./world.atlas-nodes.0088.1b4c43db848fc334.js)
- Static atlas data chunk: [`world.atlas-nodes.0089.1d15a90ac1befb46.js`](./world.atlas-nodes.0089.1d15a90ac1befb46.js)
- Static atlas data chunk: [`world.atlas-nodes.0090.26ad4350b53633b0.js`](./world.atlas-nodes.0090.26ad4350b53633b0.js)
- Static atlas data chunk: [`world.atlas-nodes.0091.a6c5da6647f0ca84.js`](./world.atlas-nodes.0091.a6c5da6647f0ca84.js)
- Static atlas data chunk: [`world.atlas-nodes.0092.58eaa01e1c987204.js`](./world.atlas-nodes.0092.58eaa01e1c987204.js)
- Static atlas data chunk: [`world.atlas-nodes.0093.9175c380271aa8eb.js`](./world.atlas-nodes.0093.9175c380271aa8eb.js)
- Static atlas data chunk: [`world.atlas-nodes.0094.c6c5d46803729ce4.js`](./world.atlas-nodes.0094.c6c5d46803729ce4.js)
- Static atlas data chunk: [`world.atlas-nodes.0095.d7ed57c9cb9f32f7.js`](./world.atlas-nodes.0095.d7ed57c9cb9f32f7.js)
- Static atlas data chunk: [`world.atlas-nodes.0096.d48ad12824a86b33.js`](./world.atlas-nodes.0096.d48ad12824a86b33.js)
- Static atlas data chunk: [`world.atlas-nodes.0097.b9169475430131a1.js`](./world.atlas-nodes.0097.b9169475430131a1.js)
- Static atlas data chunk: [`world.atlas-nodes.0098.20d8d546da39cd8a.js`](./world.atlas-nodes.0098.20d8d546da39cd8a.js)
- Static atlas data chunk: [`world.atlas-nodes.0099.20f6010bd907c1a7.js`](./world.atlas-nodes.0099.20f6010bd907c1a7.js)
- Static atlas data chunk: [`world.atlas-nodes.0100.c6dd681f0caa483b.js`](./world.atlas-nodes.0100.c6dd681f0caa483b.js)
- Static atlas data chunk: [`world.atlas-nodes.0101.001fc758f96be559.js`](./world.atlas-nodes.0101.001fc758f96be559.js)
- Static atlas data chunk: [`world.atlas-nodes.0102.24751ce78f03f12b.js`](./world.atlas-nodes.0102.24751ce78f03f12b.js)
- Static atlas data chunk: [`world.atlas-nodes.0103.0b7f7b762bc1d8ab.js`](./world.atlas-nodes.0103.0b7f7b762bc1d8ab.js)
- Static atlas data chunk: [`world.atlas-nodes.0104.f51feb9a34074304.js`](./world.atlas-nodes.0104.f51feb9a34074304.js)
- Static atlas data chunk: [`world.atlas-nodes.0105.2bbe1cba1c53cd70.js`](./world.atlas-nodes.0105.2bbe1cba1c53cd70.js)
- Static atlas data chunk: [`world.atlas-nodes.0106.7279a232d6248e8e.js`](./world.atlas-nodes.0106.7279a232d6248e8e.js)
- Static atlas data chunk: [`world.atlas-nodes.0107.ebcff7573be5b905.js`](./world.atlas-nodes.0107.ebcff7573be5b905.js)
- Static atlas data chunk: [`world.atlas-nodes.0108.1bb7f764496e9737.js`](./world.atlas-nodes.0108.1bb7f764496e9737.js)
- Static atlas data chunk: [`world.atlas-nodes.0109.f73a5b61a0062179.js`](./world.atlas-nodes.0109.f73a5b61a0062179.js)
- Static atlas data chunk: [`world.atlas-nodes.0110.1147074eaa8c86d4.js`](./world.atlas-nodes.0110.1147074eaa8c86d4.js)
- Static atlas data chunk: [`world.atlas-nodes.0111.947b4e72b6fb4b69.js`](./world.atlas-nodes.0111.947b4e72b6fb4b69.js)
- Static atlas data chunk: [`world.atlas-nodes.0112.12e393e80c83ce19.js`](./world.atlas-nodes.0112.12e393e80c83ce19.js)
- Static atlas data chunk: [`world.atlas-nodes.0113.e00dccea097f1b8d.js`](./world.atlas-nodes.0113.e00dccea097f1b8d.js)
- Static atlas data chunk: [`world.atlas-nodes.0114.781f3ac30766b0c2.js`](./world.atlas-nodes.0114.781f3ac30766b0c2.js)
- Static atlas data chunk: [`world.atlas-nodes.0115.1f61f54eda77d839.js`](./world.atlas-nodes.0115.1f61f54eda77d839.js)
- Static atlas data chunk: [`world.atlas-nodes.0116.8a214041fc120719.js`](./world.atlas-nodes.0116.8a214041fc120719.js)
- Static atlas data chunk: [`world.atlas-nodes.0117.cec68875667e1427.js`](./world.atlas-nodes.0117.cec68875667e1427.js)
- Static atlas data chunk: [`world.atlas-edges.0118.cbf18e861d1bd51c.js`](./world.atlas-edges.0118.cbf18e861d1bd51c.js)
- Static atlas data chunk: [`world.atlas-sequences.0119.b4959c360b48e02c.js`](./world.atlas-sequences.0119.b4959c360b48e02c.js)
- Static atlas data chunk: [`world.atlas-indexes.0120.a2f5f02b6bea834e.js`](./world.atlas-indexes.0120.a2f5f02b6bea834e.js)
- Animal source-sample chronology accountability: [`world_animal_sample_chronology_context.json`](./world_animal_sample_chronology_context.json)
- Candidate site ranking CSV: [`world_candidate_sites.csv`](./world_candidate_sites.csv)
- Candidate site ranking JSON: [`world_candidate_sites.json`](./world_candidate_sites.json)
- Candidate site ranking markdown: [`world_candidate_sites.md`](./world_candidate_sites.md)
- Candidate site sensitivity JSON: [`world_candidate_site_sensitivity.json`](./world_candidate_site_sensitivity.json)
- Candidate site sensitivity markdown: [`world_candidate_site_sensitivity.md`](./world_candidate_site_sensitivity.md)
- Candidate ranking engine manifest: [`world_candidate_ranking_engine_manifest.json`](./world_candidate_ranking_engine_manifest.json)
- Atlas evidence surface JSON: [`world_evidence_surface.json`](./world_evidence_surface.json)
- Atlas evidence surface markdown: [`world_evidence_surface.md`](./world_evidence_surface.md)
- Atlas scientific review JSON: [`world_scientific_review.json`](./world_scientific_review.json)
- Atlas scientific review markdown: [`world_scientific_review.md`](./world_scientific_review.md)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `22` |
| Goat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `26` |
| Goat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `1` |
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `63` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `10` |
| Cat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `24` |
| Cat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `31` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `9` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `242` |
| Cat source-sample chronology | `shared_world_scale_layer` |  | `35` |
| Sheep source-sample chronology | `shared_world_scale_layer` |  | `4` |
| Pig source-sample chronology | `shared_world_scale_layer` |  | `2` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |

## Governed Filters

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch

## Scope Caveats

- World is the parent publication scope, not a claim that worldwide contextual coverage is already complete.
- Nordic environmental and archaeology overlays are withheld here until broader equivalents exist.
- Country counts still describe Homo sapiens AADR rows even when animal layers are also visible.


## Animal aDNA Layers

- Total animal locality points: `165`
- Shipped animal species: `6`
- Domesticated-core species layers: `5`
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
| approximate | 24 |
| exact | 139 |
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
| cattle | Bos taurus | wild_or_progenitor_context | 22 |
| goat | Capra hircus | domesticated_core | 26 |
| goat | Capra hircus | wild_or_progenitor_context | 1 |
| horse | Equus caballus | domesticated_core | 63 |
| horse | Equus caballus | wild_or_progenitor_context | 10 |
| cat | Felis catus | domesticated_core | 24 |
| cat | Felis catus | wild_or_progenitor_context | 15 |
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

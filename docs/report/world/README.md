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
- Static atlas data chunk: [`world.atlas-provenance.0000.7cc824892bebbe87.js`](./world.atlas-provenance.0000.7cc824892bebbe87.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.38098c9b43f4660f.js`](./world.atlas-nodes.0001.38098c9b43f4660f.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.dd37086b452f146a.js`](./world.atlas-nodes.0002.dd37086b452f146a.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.6e70da35a22a402b.js`](./world.atlas-nodes.0003.6e70da35a22a402b.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.b2778a35d881f6fd.js`](./world.atlas-nodes.0004.b2778a35d881f6fd.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.3dd21781108ed3a5.js`](./world.atlas-nodes.0005.3dd21781108ed3a5.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.1bc389d5c1bbbaba.js`](./world.atlas-nodes.0006.1bc389d5c1bbbaba.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.0983ae807c663237.js`](./world.atlas-nodes.0007.0983ae807c663237.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.7cd6d40b4a491545.js`](./world.atlas-nodes.0008.7cd6d40b4a491545.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.1c7b501d1a0f429e.js`](./world.atlas-nodes.0009.1c7b501d1a0f429e.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.f94571a2c4070e5a.js`](./world.atlas-nodes.0010.f94571a2c4070e5a.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.f7754195856dba08.js`](./world.atlas-nodes.0011.f7754195856dba08.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.1e5bfaea0468fa28.js`](./world.atlas-nodes.0012.1e5bfaea0468fa28.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.a86a2ae22f30de1b.js`](./world.atlas-nodes.0013.a86a2ae22f30de1b.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.7bc30b42c57f859f.js`](./world.atlas-nodes.0014.7bc30b42c57f859f.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.3ac4dd0844bdefa9.js`](./world.atlas-nodes.0015.3ac4dd0844bdefa9.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.1a44820e057e5c32.js`](./world.atlas-nodes.0016.1a44820e057e5c32.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.03c66baec13c64aa.js`](./world.atlas-nodes.0017.03c66baec13c64aa.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.35066746e77e6875.js`](./world.atlas-nodes.0018.35066746e77e6875.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.4769f98a8919ceb1.js`](./world.atlas-nodes.0019.4769f98a8919ceb1.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.4ac59de199f82a5b.js`](./world.atlas-nodes.0020.4ac59de199f82a5b.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.6a206053702ceb0e.js`](./world.atlas-nodes.0021.6a206053702ceb0e.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.6b92555c0934c9c9.js`](./world.atlas-nodes.0022.6b92555c0934c9c9.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.e4a06ed074c0ec25.js`](./world.atlas-nodes.0023.e4a06ed074c0ec25.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.f98c2eb42c9881ee.js`](./world.atlas-nodes.0024.f98c2eb42c9881ee.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.cafbe0c9526e885b.js`](./world.atlas-nodes.0025.cafbe0c9526e885b.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.d1a6d9cec246ddb2.js`](./world.atlas-nodes.0026.d1a6d9cec246ddb2.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.28bbb3a50b889537.js`](./world.atlas-nodes.0027.28bbb3a50b889537.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.f8d52b42982457c7.js`](./world.atlas-nodes.0028.f8d52b42982457c7.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.2957c30925b1a338.js`](./world.atlas-nodes.0029.2957c30925b1a338.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.55319251c1c15a4f.js`](./world.atlas-nodes.0030.55319251c1c15a4f.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.6d8ad32fb8b74f3a.js`](./world.atlas-nodes.0031.6d8ad32fb8b74f3a.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.3957f3b0ed161e23.js`](./world.atlas-nodes.0032.3957f3b0ed161e23.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.9771268def6f17fa.js`](./world.atlas-nodes.0033.9771268def6f17fa.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.843b962515f5512a.js`](./world.atlas-nodes.0034.843b962515f5512a.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.f86f2e63d53e1f21.js`](./world.atlas-nodes.0035.f86f2e63d53e1f21.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.068c5de5dd103d5e.js`](./world.atlas-nodes.0036.068c5de5dd103d5e.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.ec61f33b9655b1b1.js`](./world.atlas-nodes.0037.ec61f33b9655b1b1.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.d04cee2eaefaabdf.js`](./world.atlas-nodes.0038.d04cee2eaefaabdf.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.35086cce45250b49.js`](./world.atlas-nodes.0039.35086cce45250b49.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.c58e56dd3ca0cdc6.js`](./world.atlas-nodes.0040.c58e56dd3ca0cdc6.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.2c29ef44ca56d3af.js`](./world.atlas-nodes.0041.2c29ef44ca56d3af.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.2c4378c6b7cd3060.js`](./world.atlas-nodes.0042.2c4378c6b7cd3060.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.6c350f14600500e6.js`](./world.atlas-nodes.0043.6c350f14600500e6.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.b170ea94d61a955e.js`](./world.atlas-nodes.0044.b170ea94d61a955e.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.d1b45eecd0745c21.js`](./world.atlas-nodes.0045.d1b45eecd0745c21.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.7dda3d5147edddc9.js`](./world.atlas-nodes.0046.7dda3d5147edddc9.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.f657e652d61e1686.js`](./world.atlas-nodes.0047.f657e652d61e1686.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.f44e7d4ca776fa84.js`](./world.atlas-nodes.0048.f44e7d4ca776fa84.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.a5d189b303244505.js`](./world.atlas-nodes.0049.a5d189b303244505.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.87ef874987c8ef64.js`](./world.atlas-nodes.0050.87ef874987c8ef64.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.34c58dc6f9fd3103.js`](./world.atlas-nodes.0051.34c58dc6f9fd3103.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.6ee354bdcabeb00b.js`](./world.atlas-nodes.0052.6ee354bdcabeb00b.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.8ca8b7154b86b64a.js`](./world.atlas-nodes.0053.8ca8b7154b86b64a.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.758af338e0999875.js`](./world.atlas-nodes.0054.758af338e0999875.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.64a2bf6642ac0028.js`](./world.atlas-nodes.0055.64a2bf6642ac0028.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.f48197df1f1214f7.js`](./world.atlas-nodes.0056.f48197df1f1214f7.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.481cddf9400a6f17.js`](./world.atlas-nodes.0057.481cddf9400a6f17.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.1446b2de4a807760.js`](./world.atlas-nodes.0058.1446b2de4a807760.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.53e072afcd114f24.js`](./world.atlas-nodes.0059.53e072afcd114f24.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.bfe0d5f13f99b594.js`](./world.atlas-nodes.0060.bfe0d5f13f99b594.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.a22a6412753ab642.js`](./world.atlas-nodes.0061.a22a6412753ab642.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.4b118047b13668f1.js`](./world.atlas-nodes.0062.4b118047b13668f1.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.373e3c45ec716285.js`](./world.atlas-nodes.0063.373e3c45ec716285.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.4215e0fc17aabf4e.js`](./world.atlas-nodes.0064.4215e0fc17aabf4e.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.785ec8bd6ed58e7f.js`](./world.atlas-nodes.0065.785ec8bd6ed58e7f.js)
- Static atlas data chunk: [`world.atlas-nodes.0066.ea7261e25202bcce.js`](./world.atlas-nodes.0066.ea7261e25202bcce.js)
- Static atlas data chunk: [`world.atlas-nodes.0067.64efb314dfb9faa8.js`](./world.atlas-nodes.0067.64efb314dfb9faa8.js)
- Static atlas data chunk: [`world.atlas-nodes.0068.bb093d72bd77bc60.js`](./world.atlas-nodes.0068.bb093d72bd77bc60.js)
- Static atlas data chunk: [`world.atlas-nodes.0069.0dd673c1f32d7d38.js`](./world.atlas-nodes.0069.0dd673c1f32d7d38.js)
- Static atlas data chunk: [`world.atlas-nodes.0070.714dc9a1b11285f1.js`](./world.atlas-nodes.0070.714dc9a1b11285f1.js)
- Static atlas data chunk: [`world.atlas-nodes.0071.e3727f43f1f82242.js`](./world.atlas-nodes.0071.e3727f43f1f82242.js)
- Static atlas data chunk: [`world.atlas-nodes.0072.09d43d14896c39c4.js`](./world.atlas-nodes.0072.09d43d14896c39c4.js)
- Static atlas data chunk: [`world.atlas-nodes.0073.bd5897f4b04c717e.js`](./world.atlas-nodes.0073.bd5897f4b04c717e.js)
- Static atlas data chunk: [`world.atlas-nodes.0074.e9b3782c023389da.js`](./world.atlas-nodes.0074.e9b3782c023389da.js)
- Static atlas data chunk: [`world.atlas-nodes.0075.c9dc78f4e830ecfb.js`](./world.atlas-nodes.0075.c9dc78f4e830ecfb.js)
- Static atlas data chunk: [`world.atlas-nodes.0076.9582666bb2a50bf5.js`](./world.atlas-nodes.0076.9582666bb2a50bf5.js)
- Static atlas data chunk: [`world.atlas-nodes.0077.c8c63177010b4146.js`](./world.atlas-nodes.0077.c8c63177010b4146.js)
- Static atlas data chunk: [`world.atlas-nodes.0078.32777e4b92acf92e.js`](./world.atlas-nodes.0078.32777e4b92acf92e.js)
- Static atlas data chunk: [`world.atlas-nodes.0079.72edfaa03d0efbaf.js`](./world.atlas-nodes.0079.72edfaa03d0efbaf.js)
- Static atlas data chunk: [`world.atlas-nodes.0080.d21df136189272cf.js`](./world.atlas-nodes.0080.d21df136189272cf.js)
- Static atlas data chunk: [`world.atlas-nodes.0081.dc22657a78a1598e.js`](./world.atlas-nodes.0081.dc22657a78a1598e.js)
- Static atlas data chunk: [`world.atlas-nodes.0082.5c4d27973ef04b2c.js`](./world.atlas-nodes.0082.5c4d27973ef04b2c.js)
- Static atlas data chunk: [`world.atlas-nodes.0083.82c5e03cc6c931bb.js`](./world.atlas-nodes.0083.82c5e03cc6c931bb.js)
- Static atlas data chunk: [`world.atlas-nodes.0084.df954a5859239879.js`](./world.atlas-nodes.0084.df954a5859239879.js)
- Static atlas data chunk: [`world.atlas-nodes.0085.ca529f70dd3ba410.js`](./world.atlas-nodes.0085.ca529f70dd3ba410.js)
- Static atlas data chunk: [`world.atlas-nodes.0086.341505d7eda19117.js`](./world.atlas-nodes.0086.341505d7eda19117.js)
- Static atlas data chunk: [`world.atlas-nodes.0087.749c4521e9a7b463.js`](./world.atlas-nodes.0087.749c4521e9a7b463.js)
- Static atlas data chunk: [`world.atlas-nodes.0088.5e8655071567f74b.js`](./world.atlas-nodes.0088.5e8655071567f74b.js)
- Static atlas data chunk: [`world.atlas-nodes.0089.b980d996cd3762f5.js`](./world.atlas-nodes.0089.b980d996cd3762f5.js)
- Static atlas data chunk: [`world.atlas-nodes.0090.5ad726a023cd5437.js`](./world.atlas-nodes.0090.5ad726a023cd5437.js)
- Static atlas data chunk: [`world.atlas-nodes.0091.4f8daa04d4b8e0b0.js`](./world.atlas-nodes.0091.4f8daa04d4b8e0b0.js)
- Static atlas data chunk: [`world.atlas-nodes.0092.db7e7eabfe916e81.js`](./world.atlas-nodes.0092.db7e7eabfe916e81.js)
- Static atlas data chunk: [`world.atlas-nodes.0093.92dd18831ef168f0.js`](./world.atlas-nodes.0093.92dd18831ef168f0.js)
- Static atlas data chunk: [`world.atlas-nodes.0094.c5a307ecaca01a64.js`](./world.atlas-nodes.0094.c5a307ecaca01a64.js)
- Static atlas data chunk: [`world.atlas-nodes.0095.456d3271d6b739c6.js`](./world.atlas-nodes.0095.456d3271d6b739c6.js)
- Static atlas data chunk: [`world.atlas-nodes.0096.f3863fa77544ce9b.js`](./world.atlas-nodes.0096.f3863fa77544ce9b.js)
- Static atlas data chunk: [`world.atlas-nodes.0097.e4557c84f5e9be37.js`](./world.atlas-nodes.0097.e4557c84f5e9be37.js)
- Static atlas data chunk: [`world.atlas-nodes.0098.407bdb32964288e7.js`](./world.atlas-nodes.0098.407bdb32964288e7.js)
- Static atlas data chunk: [`world.atlas-nodes.0099.34f4da8e8bf168de.js`](./world.atlas-nodes.0099.34f4da8e8bf168de.js)
- Static atlas data chunk: [`world.atlas-nodes.0100.79e9dec872af0900.js`](./world.atlas-nodes.0100.79e9dec872af0900.js)
- Static atlas data chunk: [`world.atlas-nodes.0101.78bbc9550b841dc2.js`](./world.atlas-nodes.0101.78bbc9550b841dc2.js)
- Static atlas data chunk: [`world.atlas-nodes.0102.5a4aac8d11cdce68.js`](./world.atlas-nodes.0102.5a4aac8d11cdce68.js)
- Static atlas data chunk: [`world.atlas-nodes.0103.a203c99de4f23e2c.js`](./world.atlas-nodes.0103.a203c99de4f23e2c.js)
- Static atlas data chunk: [`world.atlas-nodes.0104.663631fdd4c3ccaf.js`](./world.atlas-nodes.0104.663631fdd4c3ccaf.js)
- Static atlas data chunk: [`world.atlas-nodes.0105.c5e39f0fd9626279.js`](./world.atlas-nodes.0105.c5e39f0fd9626279.js)
- Static atlas data chunk: [`world.atlas-nodes.0106.66e35cdfd514329d.js`](./world.atlas-nodes.0106.66e35cdfd514329d.js)
- Static atlas data chunk: [`world.atlas-nodes.0107.7e3ea477cb9205d3.js`](./world.atlas-nodes.0107.7e3ea477cb9205d3.js)
- Static atlas data chunk: [`world.atlas-nodes.0108.d98afad0e795dec9.js`](./world.atlas-nodes.0108.d98afad0e795dec9.js)
- Static atlas data chunk: [`world.atlas-nodes.0109.ec70ce31de49acbc.js`](./world.atlas-nodes.0109.ec70ce31de49acbc.js)
- Static atlas data chunk: [`world.atlas-nodes.0110.5125bbe5f9746253.js`](./world.atlas-nodes.0110.5125bbe5f9746253.js)
- Static atlas data chunk: [`world.atlas-nodes.0111.23e6becdeb5e3839.js`](./world.atlas-nodes.0111.23e6becdeb5e3839.js)
- Static atlas data chunk: [`world.atlas-nodes.0112.e205b1e5c3c6bc00.js`](./world.atlas-nodes.0112.e205b1e5c3c6bc00.js)
- Static atlas data chunk: [`world.atlas-edges.0113.9ece9bb545994e20.js`](./world.atlas-edges.0113.9ece9bb545994e20.js)
- Static atlas data chunk: [`world.atlas-sequences.0114.59d0aa1174363a6b.js`](./world.atlas-sequences.0114.59d0aa1174363a6b.js)
- Static atlas data chunk: [`world.atlas-indexes.0115.3eb7d584923725d6.js`](./world.atlas-indexes.0115.3eb7d584923725d6.js)
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
- Static atlas runtime: [`world_map.atlas-runtime.f2519cfb77824d9e.js`](./world_map.atlas-runtime.f2519cfb77824d9e.js)
- Interactive evidence tools: [`world_map.atlas-evidence-tools.bac3f9295a5c95bb.js`](./world_map.atlas-evidence-tools.bac3f9295a5c95bb.js)
- Static atlas index transport: [`world_map.atlas-index-transport.2168d29af8354bcb.js`](./world_map.atlas-index-transport.2168d29af8354bcb.js)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `22` |
| Goat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `23` |
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `63` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `10` |
| Cat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `24` |
| Cat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `31` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `5` |
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

- Total animal locality points: `161`
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
| exact | 135 |
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
| goat | Capra hircus | domesticated_core | 23 |
| horse | Equus caballus | domesticated_core | 63 |
| horse | Equus caballus | wild_or_progenitor_context | 10 |
| cat | Felis catus | domesticated_core | 24 |
| cat | Felis catus | wild_or_progenitor_context | 15 |
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The world bundle is a governing publication scope with 1231AADR metadata samples from four Nordic country products and 161 governed animal locality features.

**Unsupported claim.** World is a scope name, not worldwide source completeness, genotype analysis, scientific country/chronology admission or validated fieldwork advice.

**Actual verification performed.** The actual three-scope producer at 04f1c4857 passed source-value, temporal, layer, point-traceability, static-budget and playback guards in 266.419 s. World retains 16 layer rows, including 15 point layers with 1711 record uses. No full browser or query-latency acceptance is claimed.

**Remaining input or review.** Broader context-source coverage, qualified sample chronology/geography/rights and scientific admission remain incomplete; current browser/network behavior requires its own retained execution.

**Cause category.** Publication scope and heterogeneous metadata layers with incomplete scientific/global coverage.

**Consequence.** Withheld Nordic environmental/context overlays do not become globally available by widening the map frame; source-sample chronology overlays are not additional biological samples.

**Precise next acceptance route.** Reproduce exact current bundle/assets and native browser contract, then qualify broader source coverage and each family role before asserting worldwide science or historical inference.

**Negative or refused result.** Nordic-onlycontext overlays remain withheld; animal comparator layer count 0 is not absence of all wild/progenitor context; historical 170 features/331 memberships are superseded by 161/318.

**Matched denominator.** Human 1231=SE 416+NO 130+FI 32+DK 653 at 447 localities; animal 161 features represent 318 samples across 6 mapped species. Source-chronology overlays 319 record uses overlap these memberships and must not be added as independent evidence.

- [Retained qualification evidence: docs/report/world/world_summary.json](world_summary.json) (SHA-256 `72145bd208a3dfd9b890bdb08ce1fd868685e55d9ac9ef155facb6da3ec4529b`).

- [Retained qualification evidence: docs/report/world/world_map_publication_contract.json](world_map_publication_contract.json) (SHA-256 `25d3be6f3671d90b333cf09b98c0278a6b8bd71560a88a2ed64e2bdcc0745548`).

- [Retained qualification evidence: reports/science/animal-entity-capability/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/report.json) (SHA-256 `713396181e44cfe23c2be59e8cac78db120ef33888245adcc01a7c2e18a6784b`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

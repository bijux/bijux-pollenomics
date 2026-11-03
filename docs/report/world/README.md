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
- Static atlas data chunk: [`world.atlas-provenance.0000.24ed5a4b40830b5c.js`](./world.atlas-provenance.0000.24ed5a4b40830b5c.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.49c0de7e6a1ec79c.js`](./world.atlas-nodes.0001.49c0de7e6a1ec79c.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.d0ecb48d88fec713.js`](./world.atlas-nodes.0002.d0ecb48d88fec713.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.c7105325f3e26409.js`](./world.atlas-nodes.0003.c7105325f3e26409.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.c7e81be673a43d76.js`](./world.atlas-nodes.0004.c7e81be673a43d76.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.6479308972c3c76f.js`](./world.atlas-nodes.0005.6479308972c3c76f.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.5e7ef70cbe820f94.js`](./world.atlas-nodes.0006.5e7ef70cbe820f94.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.4748f6d146aa01cc.js`](./world.atlas-nodes.0007.4748f6d146aa01cc.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.7b8da99a4aa8d9c1.js`](./world.atlas-nodes.0008.7b8da99a4aa8d9c1.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.3c3dc2d0e74aed85.js`](./world.atlas-nodes.0009.3c3dc2d0e74aed85.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.cc0ef829f5cab82b.js`](./world.atlas-nodes.0010.cc0ef829f5cab82b.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.b56a34b45128867c.js`](./world.atlas-nodes.0011.b56a34b45128867c.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.5c12e5e05791d25c.js`](./world.atlas-nodes.0012.5c12e5e05791d25c.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.37981c27724a7f27.js`](./world.atlas-nodes.0013.37981c27724a7f27.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.38a15767de0675cb.js`](./world.atlas-nodes.0014.38a15767de0675cb.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.e906b459c6954613.js`](./world.atlas-nodes.0015.e906b459c6954613.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.de02c3337c36da6c.js`](./world.atlas-nodes.0016.de02c3337c36da6c.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.0b5a6c73fdd9081f.js`](./world.atlas-nodes.0017.0b5a6c73fdd9081f.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.2d74e64d9c33d893.js`](./world.atlas-nodes.0018.2d74e64d9c33d893.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.449c8a1883e73143.js`](./world.atlas-nodes.0019.449c8a1883e73143.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.68393325570ab8b2.js`](./world.atlas-nodes.0020.68393325570ab8b2.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.afd3aec4c421fd83.js`](./world.atlas-nodes.0021.afd3aec4c421fd83.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.b3d640aaa0c4e77c.js`](./world.atlas-nodes.0022.b3d640aaa0c4e77c.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.7d5088928b9eccfc.js`](./world.atlas-nodes.0023.7d5088928b9eccfc.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.692dd8336a65f034.js`](./world.atlas-nodes.0024.692dd8336a65f034.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.a95b388016f4ea62.js`](./world.atlas-nodes.0025.a95b388016f4ea62.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.be30bdb78305a749.js`](./world.atlas-nodes.0026.be30bdb78305a749.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.f7cc644b83b1619d.js`](./world.atlas-nodes.0027.f7cc644b83b1619d.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.d11933db6e97ce8e.js`](./world.atlas-nodes.0028.d11933db6e97ce8e.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.6ca760785021e5e9.js`](./world.atlas-nodes.0029.6ca760785021e5e9.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.e7996ae421cccc3b.js`](./world.atlas-nodes.0030.e7996ae421cccc3b.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.35be527b70daf692.js`](./world.atlas-nodes.0031.35be527b70daf692.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.a18949cd65da69bf.js`](./world.atlas-nodes.0032.a18949cd65da69bf.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.fa5b6bd4924f0634.js`](./world.atlas-nodes.0033.fa5b6bd4924f0634.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.2423d5e49b811f78.js`](./world.atlas-nodes.0034.2423d5e49b811f78.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.2ab2028a2c567411.js`](./world.atlas-nodes.0035.2ab2028a2c567411.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.adca3a719826236d.js`](./world.atlas-nodes.0036.adca3a719826236d.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.6f07defdc0b80119.js`](./world.atlas-nodes.0037.6f07defdc0b80119.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.a965fde86a5fbdb6.js`](./world.atlas-nodes.0038.a965fde86a5fbdb6.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.c0ac3c6be987552a.js`](./world.atlas-nodes.0039.c0ac3c6be987552a.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.7cdeaded70863bb4.js`](./world.atlas-nodes.0040.7cdeaded70863bb4.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.e45981cb9a163379.js`](./world.atlas-nodes.0041.e45981cb9a163379.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.8805b24d12fe2939.js`](./world.atlas-nodes.0042.8805b24d12fe2939.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.0df383e45b565158.js`](./world.atlas-nodes.0043.0df383e45b565158.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.135e0d94858f8e3d.js`](./world.atlas-nodes.0044.135e0d94858f8e3d.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.fe1fc93c5092c65d.js`](./world.atlas-nodes.0045.fe1fc93c5092c65d.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.3b9767da4ed5771d.js`](./world.atlas-nodes.0046.3b9767da4ed5771d.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.b297dfcd4dbabaed.js`](./world.atlas-nodes.0047.b297dfcd4dbabaed.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.a8e0425d4c46b36e.js`](./world.atlas-nodes.0048.a8e0425d4c46b36e.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.cf03574f795fa22e.js`](./world.atlas-nodes.0049.cf03574f795fa22e.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.a64ebce53a7100a2.js`](./world.atlas-nodes.0050.a64ebce53a7100a2.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.0c6a4ee9a9493761.js`](./world.atlas-nodes.0051.0c6a4ee9a9493761.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.bdf202c3ab40e59f.js`](./world.atlas-nodes.0052.bdf202c3ab40e59f.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.18680337a067f044.js`](./world.atlas-nodes.0053.18680337a067f044.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.311754707cbfce82.js`](./world.atlas-nodes.0054.311754707cbfce82.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.f55bd10b9a33f035.js`](./world.atlas-nodes.0055.f55bd10b9a33f035.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.9a808070191b1e92.js`](./world.atlas-nodes.0056.9a808070191b1e92.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.bcb9d804bcad1dea.js`](./world.atlas-nodes.0057.bcb9d804bcad1dea.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.1599da82b177624a.js`](./world.atlas-nodes.0058.1599da82b177624a.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.7055af8f849e5e07.js`](./world.atlas-nodes.0059.7055af8f849e5e07.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.2af5194fda7df799.js`](./world.atlas-nodes.0060.2af5194fda7df799.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.8c9efa7283854469.js`](./world.atlas-nodes.0061.8c9efa7283854469.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.58807ecfb498cef4.js`](./world.atlas-nodes.0062.58807ecfb498cef4.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.aae754ac239ef316.js`](./world.atlas-nodes.0063.aae754ac239ef316.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.2cbf15d320592792.js`](./world.atlas-nodes.0064.2cbf15d320592792.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.12a6bb7fbe29de1a.js`](./world.atlas-nodes.0065.12a6bb7fbe29de1a.js)
- Static atlas data chunk: [`world.atlas-nodes.0066.f8f98bc6a69a3142.js`](./world.atlas-nodes.0066.f8f98bc6a69a3142.js)
- Static atlas data chunk: [`world.atlas-nodes.0067.9ca9b047e49f01a6.js`](./world.atlas-nodes.0067.9ca9b047e49f01a6.js)
- Static atlas data chunk: [`world.atlas-nodes.0068.8ce945aa90f1fd5b.js`](./world.atlas-nodes.0068.8ce945aa90f1fd5b.js)
- Static atlas data chunk: [`world.atlas-nodes.0069.080a19cf57cb0d76.js`](./world.atlas-nodes.0069.080a19cf57cb0d76.js)
- Static atlas data chunk: [`world.atlas-nodes.0070.b8f84a13a365f445.js`](./world.atlas-nodes.0070.b8f84a13a365f445.js)
- Static atlas data chunk: [`world.atlas-nodes.0071.6c2254f26ef326d7.js`](./world.atlas-nodes.0071.6c2254f26ef326d7.js)
- Static atlas data chunk: [`world.atlas-nodes.0072.bc5c77af0dcd87e7.js`](./world.atlas-nodes.0072.bc5c77af0dcd87e7.js)
- Static atlas data chunk: [`world.atlas-nodes.0073.1301ca1cb1c533ba.js`](./world.atlas-nodes.0073.1301ca1cb1c533ba.js)
- Static atlas data chunk: [`world.atlas-nodes.0074.f56973f08c114f0d.js`](./world.atlas-nodes.0074.f56973f08c114f0d.js)
- Static atlas data chunk: [`world.atlas-nodes.0075.6437183dfba93973.js`](./world.atlas-nodes.0075.6437183dfba93973.js)
- Static atlas data chunk: [`world.atlas-nodes.0076.63e3cb9e25b945a2.js`](./world.atlas-nodes.0076.63e3cb9e25b945a2.js)
- Static atlas data chunk: [`world.atlas-nodes.0077.d556c4e9accd9b94.js`](./world.atlas-nodes.0077.d556c4e9accd9b94.js)
- Static atlas data chunk: [`world.atlas-nodes.0078.dcdd0879d9b15ab0.js`](./world.atlas-nodes.0078.dcdd0879d9b15ab0.js)
- Static atlas data chunk: [`world.atlas-nodes.0079.16a4dbb6275bb4b9.js`](./world.atlas-nodes.0079.16a4dbb6275bb4b9.js)
- Static atlas data chunk: [`world.atlas-nodes.0080.b4273d5455f9f032.js`](./world.atlas-nodes.0080.b4273d5455f9f032.js)
- Static atlas data chunk: [`world.atlas-nodes.0081.2d6dbb4621eca696.js`](./world.atlas-nodes.0081.2d6dbb4621eca696.js)
- Static atlas data chunk: [`world.atlas-nodes.0082.fcd0a534f417ec0d.js`](./world.atlas-nodes.0082.fcd0a534f417ec0d.js)
- Static atlas data chunk: [`world.atlas-nodes.0083.3a013e427ad84ab7.js`](./world.atlas-nodes.0083.3a013e427ad84ab7.js)
- Static atlas data chunk: [`world.atlas-nodes.0084.991a2f0aa4809233.js`](./world.atlas-nodes.0084.991a2f0aa4809233.js)
- Static atlas data chunk: [`world.atlas-nodes.0085.444231e78e0a4d74.js`](./world.atlas-nodes.0085.444231e78e0a4d74.js)
- Static atlas data chunk: [`world.atlas-nodes.0086.f13d401f4074910b.js`](./world.atlas-nodes.0086.f13d401f4074910b.js)
- Static atlas data chunk: [`world.atlas-nodes.0087.b03beb2ff928a041.js`](./world.atlas-nodes.0087.b03beb2ff928a041.js)
- Static atlas data chunk: [`world.atlas-nodes.0088.13140423ee23e479.js`](./world.atlas-nodes.0088.13140423ee23e479.js)
- Static atlas data chunk: [`world.atlas-nodes.0089.975e06718e1cd6df.js`](./world.atlas-nodes.0089.975e06718e1cd6df.js)
- Static atlas data chunk: [`world.atlas-nodes.0090.ad8fd578c66f380f.js`](./world.atlas-nodes.0090.ad8fd578c66f380f.js)
- Static atlas data chunk: [`world.atlas-nodes.0091.73fe6de822e36219.js`](./world.atlas-nodes.0091.73fe6de822e36219.js)
- Static atlas data chunk: [`world.atlas-nodes.0092.bc000bd55d9c59d4.js`](./world.atlas-nodes.0092.bc000bd55d9c59d4.js)
- Static atlas data chunk: [`world.atlas-nodes.0093.6f2e09c5ab5bc6f1.js`](./world.atlas-nodes.0093.6f2e09c5ab5bc6f1.js)
- Static atlas data chunk: [`world.atlas-nodes.0094.b988dc73227bef68.js`](./world.atlas-nodes.0094.b988dc73227bef68.js)
- Static atlas data chunk: [`world.atlas-nodes.0095.a91bddf06b2dac60.js`](./world.atlas-nodes.0095.a91bddf06b2dac60.js)
- Static atlas data chunk: [`world.atlas-nodes.0096.7bdd801c32fd37f0.js`](./world.atlas-nodes.0096.7bdd801c32fd37f0.js)
- Static atlas data chunk: [`world.atlas-nodes.0097.d0f8bc15fe25b8ef.js`](./world.atlas-nodes.0097.d0f8bc15fe25b8ef.js)
- Static atlas data chunk: [`world.atlas-nodes.0098.651ffad02fccf21b.js`](./world.atlas-nodes.0098.651ffad02fccf21b.js)
- Static atlas data chunk: [`world.atlas-nodes.0099.16e263170d10ea4c.js`](./world.atlas-nodes.0099.16e263170d10ea4c.js)
- Static atlas data chunk: [`world.atlas-nodes.0100.43834973ec35d4d1.js`](./world.atlas-nodes.0100.43834973ec35d4d1.js)
- Static atlas data chunk: [`world.atlas-nodes.0101.c82c74d7e86a85ab.js`](./world.atlas-nodes.0101.c82c74d7e86a85ab.js)
- Static atlas data chunk: [`world.atlas-nodes.0102.fc23e55ab19d3837.js`](./world.atlas-nodes.0102.fc23e55ab19d3837.js)
- Static atlas data chunk: [`world.atlas-nodes.0103.5a337c3a2baa99db.js`](./world.atlas-nodes.0103.5a337c3a2baa99db.js)
- Static atlas data chunk: [`world.atlas-nodes.0104.e325a19e8541bb45.js`](./world.atlas-nodes.0104.e325a19e8541bb45.js)
- Static atlas data chunk: [`world.atlas-nodes.0105.3de633b2dde58565.js`](./world.atlas-nodes.0105.3de633b2dde58565.js)
- Static atlas data chunk: [`world.atlas-nodes.0106.910cf26f6a35e1b7.js`](./world.atlas-nodes.0106.910cf26f6a35e1b7.js)
- Static atlas data chunk: [`world.atlas-nodes.0107.78422ccb946c32ca.js`](./world.atlas-nodes.0107.78422ccb946c32ca.js)
- Static atlas data chunk: [`world.atlas-nodes.0108.d5cfa9118f125e55.js`](./world.atlas-nodes.0108.d5cfa9118f125e55.js)
- Static atlas data chunk: [`world.atlas-nodes.0109.f038cd68fda35658.js`](./world.atlas-nodes.0109.f038cd68fda35658.js)
- Static atlas data chunk: [`world.atlas-nodes.0110.298986aea18e4034.js`](./world.atlas-nodes.0110.298986aea18e4034.js)
- Static atlas data chunk: [`world.atlas-nodes.0111.87ad7eb5ebfa9e85.js`](./world.atlas-nodes.0111.87ad7eb5ebfa9e85.js)
- Static atlas data chunk: [`world.atlas-nodes.0112.38ad24906e2d4962.js`](./world.atlas-nodes.0112.38ad24906e2d4962.js)
- Static atlas data chunk: [`world.atlas-edges.0113.e04f7602846ad276.js`](./world.atlas-edges.0113.e04f7602846ad276.js)
- Static atlas data chunk: [`world.atlas-sequences.0114.2193bdbf873c6c5b.js`](./world.atlas-sequences.0114.2193bdbf873c6c5b.js)
- Static atlas data chunk: [`world.atlas-indexes.0115.ee8815b992f80684.js`](./world.atlas-indexes.0115.ee8815b992f80684.js)
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
- Static atlas runtime: [`world_map.atlas-runtime.a333c0c242dd81a3.js`](./world_map.atlas-runtime.a333c0c242dd81a3.js)
- Interactive evidence tools: [`world_map.atlas-evidence-tools.bac3f9295a5c95bb.js`](./world_map.atlas-evidence-tools.bac3f9295a5c95bb.js)
- Static atlas index transport: [`world_map.atlas-index-transport.2168d29af8354bcb.js`](./world_map.atlas-index-transport.2168d29af8354bcb.js)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `22` |
| Goat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `23` |
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `63` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `12` |
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

- Total animal locality points: `163`
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
| exact | 137 |
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
| horse | Equus caballus | wild_or_progenitor_context | 12 |
| cat | Felis catus | domesticated_core | 24 |
| cat | Felis catus | wild_or_progenitor_context | 15 |
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The current world bundle is a governing publication scope with 1231 AADR metadata samples from four Nordic country products and 163 governed animal locality features.

**Unsupported claim.** World is a scope name, not worldwide source completeness, genotype analysis, scientific country/chronology admission or validated fieldwork advice.

**Actual verification performed.** The source-bound three-scope producer at a18530b54 completed in 326.099 s. Independent decoded preservation and all three actual JavaScript index-factory checks passed in 65.517 s aggregate, preserving unrelated science and retained chronology context. Freshly served World Chromium passed 22 source-backed and labelled synthetic temporal cases; this does not qualify general browser behavior, external providers or query latency. World now has 1713 point uses across 15 point layers within 16 layer rows.

**Remaining input or review.** Broader source coverage, sample chronology/geography/rights and scientific admission remain incomplete. The narrow served World temporal cases do not qualify all browser/network behavior or query latency.

**Cause category.** Publication scope and heterogeneous metadata layers with incomplete scientific/global coverage.

**Consequence.** Withheld Nordic environmental/context overlays do not become globally available by widening the map frame; source-sample chronology overlays are not additional biological samples.

**Precise next acceptance route.** Use the qualified current bundle/assets and source-bound temporal/index evidence; qualify broader source coverage and each family role before worldwide scientific or historical inference.

**Negative or refused result.** Nordic-only context overlays remain withheld; zero comparator layers do not imply absence of wild/progenitor context. Earlier 161/318, 165/322 and 170/331 animal populations remain historical.

**Matched denominator.** Human 1231=SE416+NO130+FI32+DK653 at 447 localities; animal 163 locality features represent 324 mapped samples across 6 mapped species. The 319 retained source-chronology record uses overlap those memberships and are not additional independent evidence.

- [Retained qualification evidence: docs/report/world/world_summary.json](world_summary.json) (SHA-256 `4024f52d6f032e139771a9727902f4a06f362a0be526f659409dbc34910812cd`).

- [Retained qualification evidence: docs/report/world/world_map_publication_contract.json](world_map_publication_contract.json) (SHA-256 `9fda0df60f16a49b954d846fc3e933c1ad1f43ba734fe6fb58147080e0f30431`).

- [Retained qualification evidence: reports/science/animal-entity-capability/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/report.json) (SHA-256 `7e3e55e28c1582ce388493290b1272709f3d85f8439e1dbbda67f7d5dcf531e9`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

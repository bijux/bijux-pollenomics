# World Evidence Surface

This shared interactive map bundle was generated on `2026-09-07` from Homo
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
- Static atlas data chunk: [`world.atlas-provenance.0000.222b692c44924b19.js`](./world.atlas-provenance.0000.222b692c44924b19.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.883f3d653bfba29d.js`](./world.atlas-nodes.0001.883f3d653bfba29d.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.bad93cbe6e8a3a9c.js`](./world.atlas-nodes.0002.bad93cbe6e8a3a9c.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.fdacce709e5c5e4d.js`](./world.atlas-nodes.0003.fdacce709e5c5e4d.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.81bb50084a887357.js`](./world.atlas-nodes.0004.81bb50084a887357.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.8546890641eae819.js`](./world.atlas-nodes.0005.8546890641eae819.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.b355f4862852b3ca.js`](./world.atlas-nodes.0006.b355f4862852b3ca.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.77bb415644034955.js`](./world.atlas-nodes.0007.77bb415644034955.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.c42d039ced55ff04.js`](./world.atlas-nodes.0008.c42d039ced55ff04.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.a2ad62f5ae2a8e10.js`](./world.atlas-nodes.0009.a2ad62f5ae2a8e10.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.613d070f485db762.js`](./world.atlas-nodes.0010.613d070f485db762.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.f23ebe3c142f915e.js`](./world.atlas-nodes.0011.f23ebe3c142f915e.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.171fb66095c4b791.js`](./world.atlas-nodes.0012.171fb66095c4b791.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.15460e5639062792.js`](./world.atlas-nodes.0013.15460e5639062792.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.c4668ca0cb51689b.js`](./world.atlas-nodes.0014.c4668ca0cb51689b.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.6c1f5f19ddb1f6f9.js`](./world.atlas-nodes.0015.6c1f5f19ddb1f6f9.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.8dfbfba0641f3197.js`](./world.atlas-nodes.0016.8dfbfba0641f3197.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.7057ae6e6a24d850.js`](./world.atlas-nodes.0017.7057ae6e6a24d850.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.0e85d2af72df3cf2.js`](./world.atlas-nodes.0018.0e85d2af72df3cf2.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.23b2b6092ee4f193.js`](./world.atlas-nodes.0019.23b2b6092ee4f193.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.49451decdca056b5.js`](./world.atlas-nodes.0020.49451decdca056b5.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.e56c1b1b715aa6ee.js`](./world.atlas-nodes.0021.e56c1b1b715aa6ee.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.1179df99a0fc30ce.js`](./world.atlas-nodes.0022.1179df99a0fc30ce.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.222e971c735771a4.js`](./world.atlas-nodes.0023.222e971c735771a4.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.718d7024a50e5457.js`](./world.atlas-nodes.0024.718d7024a50e5457.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.88c441ba3234f848.js`](./world.atlas-nodes.0025.88c441ba3234f848.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.dd3397b036e7ef4e.js`](./world.atlas-nodes.0026.dd3397b036e7ef4e.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.4f3de6e2d355f137.js`](./world.atlas-nodes.0027.4f3de6e2d355f137.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.5bce11ba862786ec.js`](./world.atlas-nodes.0028.5bce11ba862786ec.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.e0ee536f55cd885f.js`](./world.atlas-nodes.0029.e0ee536f55cd885f.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.e727d748a9f9ccee.js`](./world.atlas-nodes.0030.e727d748a9f9ccee.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.a36c727d92eb7b24.js`](./world.atlas-nodes.0031.a36c727d92eb7b24.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.944c9e45924a5a20.js`](./world.atlas-nodes.0032.944c9e45924a5a20.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.15f25ce6b947ff5e.js`](./world.atlas-nodes.0033.15f25ce6b947ff5e.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.8fd5ba7a6017f108.js`](./world.atlas-nodes.0034.8fd5ba7a6017f108.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.64ec0d99c4ef793a.js`](./world.atlas-nodes.0035.64ec0d99c4ef793a.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.d5ef683cdf63983b.js`](./world.atlas-nodes.0036.d5ef683cdf63983b.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.c70b3b9ed5ab3ccf.js`](./world.atlas-nodes.0037.c70b3b9ed5ab3ccf.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.55c8b9e5dbfb9633.js`](./world.atlas-nodes.0038.55c8b9e5dbfb9633.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.9e05fddf35d18ecc.js`](./world.atlas-nodes.0039.9e05fddf35d18ecc.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.d00cb56e7e44af2f.js`](./world.atlas-nodes.0040.d00cb56e7e44af2f.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.515d4ee3c3fb390a.js`](./world.atlas-nodes.0041.515d4ee3c3fb390a.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.c64cb53b11f7715c.js`](./world.atlas-nodes.0042.c64cb53b11f7715c.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.4a5e29c052b13f3d.js`](./world.atlas-nodes.0043.4a5e29c052b13f3d.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.e1ac192ded4a11e0.js`](./world.atlas-nodes.0044.e1ac192ded4a11e0.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.6ebdfdee9b3294b9.js`](./world.atlas-nodes.0045.6ebdfdee9b3294b9.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.6ce95e08e92985b0.js`](./world.atlas-nodes.0046.6ce95e08e92985b0.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.8c635b156e638340.js`](./world.atlas-nodes.0047.8c635b156e638340.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.23a00cf6834e8098.js`](./world.atlas-nodes.0048.23a00cf6834e8098.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.c47b83d4532ccd75.js`](./world.atlas-nodes.0049.c47b83d4532ccd75.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.a17b89ec32439e7d.js`](./world.atlas-nodes.0050.a17b89ec32439e7d.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.04dda6fb1451cc4f.js`](./world.atlas-nodes.0051.04dda6fb1451cc4f.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.601f5c870bf10f40.js`](./world.atlas-nodes.0052.601f5c870bf10f40.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.9c42473b13d7933a.js`](./world.atlas-nodes.0053.9c42473b13d7933a.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.845b8b3369b8a3e3.js`](./world.atlas-nodes.0054.845b8b3369b8a3e3.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.f6e2e6d1d6808cae.js`](./world.atlas-nodes.0055.f6e2e6d1d6808cae.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.6802316f118c5560.js`](./world.atlas-nodes.0056.6802316f118c5560.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.cd03475a4b80ebb3.js`](./world.atlas-nodes.0057.cd03475a4b80ebb3.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.3e6f9ced0c2fc578.js`](./world.atlas-nodes.0058.3e6f9ced0c2fc578.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.9d52adc3e5200331.js`](./world.atlas-nodes.0059.9d52adc3e5200331.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.5546f3425e161ffd.js`](./world.atlas-nodes.0060.5546f3425e161ffd.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.ac9bf2141c009fbc.js`](./world.atlas-nodes.0061.ac9bf2141c009fbc.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.e9220be153293930.js`](./world.atlas-nodes.0062.e9220be153293930.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.15ff55cfbef9a211.js`](./world.atlas-nodes.0063.15ff55cfbef9a211.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.79560366768c293e.js`](./world.atlas-nodes.0064.79560366768c293e.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.eb6602a39f440d92.js`](./world.atlas-nodes.0065.eb6602a39f440d92.js)
- Static atlas data chunk: [`world.atlas-nodes.0066.eb4617df6117a753.js`](./world.atlas-nodes.0066.eb4617df6117a753.js)
- Static atlas data chunk: [`world.atlas-nodes.0067.08fc154b76a14bee.js`](./world.atlas-nodes.0067.08fc154b76a14bee.js)
- Static atlas data chunk: [`world.atlas-nodes.0068.564e79dec3a01734.js`](./world.atlas-nodes.0068.564e79dec3a01734.js)
- Static atlas data chunk: [`world.atlas-nodes.0069.7fefd3a9671358f5.js`](./world.atlas-nodes.0069.7fefd3a9671358f5.js)
- Static atlas data chunk: [`world.atlas-nodes.0070.b33e8a46c002d2a5.js`](./world.atlas-nodes.0070.b33e8a46c002d2a5.js)
- Static atlas data chunk: [`world.atlas-nodes.0071.214f4a67f4a4f2d8.js`](./world.atlas-nodes.0071.214f4a67f4a4f2d8.js)
- Static atlas data chunk: [`world.atlas-nodes.0072.1a77a689eba402bb.js`](./world.atlas-nodes.0072.1a77a689eba402bb.js)
- Static atlas data chunk: [`world.atlas-nodes.0073.54d8d54bed9c04ca.js`](./world.atlas-nodes.0073.54d8d54bed9c04ca.js)
- Static atlas data chunk: [`world.atlas-nodes.0074.0861976c0d0ff045.js`](./world.atlas-nodes.0074.0861976c0d0ff045.js)
- Static atlas data chunk: [`world.atlas-nodes.0075.ac0b809f58522915.js`](./world.atlas-nodes.0075.ac0b809f58522915.js)
- Static atlas data chunk: [`world.atlas-nodes.0076.b8d6417c1d5514c4.js`](./world.atlas-nodes.0076.b8d6417c1d5514c4.js)
- Static atlas data chunk: [`world.atlas-nodes.0077.391434e153d8b48c.js`](./world.atlas-nodes.0077.391434e153d8b48c.js)
- Static atlas data chunk: [`world.atlas-nodes.0078.b99d1285c155837a.js`](./world.atlas-nodes.0078.b99d1285c155837a.js)
- Static atlas data chunk: [`world.atlas-nodes.0079.1fde26ddb0a1df2a.js`](./world.atlas-nodes.0079.1fde26ddb0a1df2a.js)
- Static atlas data chunk: [`world.atlas-nodes.0080.b1b509f43365b248.js`](./world.atlas-nodes.0080.b1b509f43365b248.js)
- Static atlas data chunk: [`world.atlas-nodes.0081.bb9fd96393c94ab6.js`](./world.atlas-nodes.0081.bb9fd96393c94ab6.js)
- Static atlas data chunk: [`world.atlas-nodes.0082.42fbd6c0d19f8d23.js`](./world.atlas-nodes.0082.42fbd6c0d19f8d23.js)
- Static atlas data chunk: [`world.atlas-nodes.0083.2bfc3d26e63168f7.js`](./world.atlas-nodes.0083.2bfc3d26e63168f7.js)
- Static atlas data chunk: [`world.atlas-nodes.0084.0954990c2fa59c35.js`](./world.atlas-nodes.0084.0954990c2fa59c35.js)
- Static atlas data chunk: [`world.atlas-nodes.0085.ef64a9835ee59b3d.js`](./world.atlas-nodes.0085.ef64a9835ee59b3d.js)
- Static atlas data chunk: [`world.atlas-nodes.0086.0b2b27c05b7ac0f8.js`](./world.atlas-nodes.0086.0b2b27c05b7ac0f8.js)
- Static atlas data chunk: [`world.atlas-nodes.0087.0d276d5a4ce6af18.js`](./world.atlas-nodes.0087.0d276d5a4ce6af18.js)
- Static atlas data chunk: [`world.atlas-nodes.0088.e664d66932c1e250.js`](./world.atlas-nodes.0088.e664d66932c1e250.js)
- Static atlas data chunk: [`world.atlas-nodes.0089.2b2feeef6a4cc0ec.js`](./world.atlas-nodes.0089.2b2feeef6a4cc0ec.js)
- Static atlas data chunk: [`world.atlas-nodes.0090.9b46c7a9c5d02415.js`](./world.atlas-nodes.0090.9b46c7a9c5d02415.js)
- Static atlas data chunk: [`world.atlas-nodes.0091.cf8cc8d47d8fbe43.js`](./world.atlas-nodes.0091.cf8cc8d47d8fbe43.js)
- Static atlas data chunk: [`world.atlas-nodes.0092.611e9811aa35c6f9.js`](./world.atlas-nodes.0092.611e9811aa35c6f9.js)
- Static atlas data chunk: [`world.atlas-nodes.0093.01f7cfed2805a1b4.js`](./world.atlas-nodes.0093.01f7cfed2805a1b4.js)
- Static atlas data chunk: [`world.atlas-nodes.0094.b232e3cdf96881eb.js`](./world.atlas-nodes.0094.b232e3cdf96881eb.js)
- Static atlas data chunk: [`world.atlas-nodes.0095.8c8623646fbe2098.js`](./world.atlas-nodes.0095.8c8623646fbe2098.js)
- Static atlas data chunk: [`world.atlas-nodes.0096.291f9e7ab92df552.js`](./world.atlas-nodes.0096.291f9e7ab92df552.js)
- Static atlas data chunk: [`world.atlas-nodes.0097.5a0657d9de07c1ca.js`](./world.atlas-nodes.0097.5a0657d9de07c1ca.js)
- Static atlas data chunk: [`world.atlas-nodes.0098.93c3e77502e49fa3.js`](./world.atlas-nodes.0098.93c3e77502e49fa3.js)
- Static atlas data chunk: [`world.atlas-nodes.0099.3669b2f8e927a0ec.js`](./world.atlas-nodes.0099.3669b2f8e927a0ec.js)
- Static atlas data chunk: [`world.atlas-nodes.0100.d003ad953256c886.js`](./world.atlas-nodes.0100.d003ad953256c886.js)
- Static atlas data chunk: [`world.atlas-nodes.0101.f6cb3f317b15ca90.js`](./world.atlas-nodes.0101.f6cb3f317b15ca90.js)
- Static atlas data chunk: [`world.atlas-nodes.0102.bf9938335f94b101.js`](./world.atlas-nodes.0102.bf9938335f94b101.js)
- Static atlas data chunk: [`world.atlas-nodes.0103.514cb58688d34b81.js`](./world.atlas-nodes.0103.514cb58688d34b81.js)
- Static atlas data chunk: [`world.atlas-nodes.0104.a64d23719b5a507d.js`](./world.atlas-nodes.0104.a64d23719b5a507d.js)
- Static atlas data chunk: [`world.atlas-nodes.0105.04c0709e8d1740c4.js`](./world.atlas-nodes.0105.04c0709e8d1740c4.js)
- Static atlas data chunk: [`world.atlas-nodes.0106.58c9bb6518f3ed7a.js`](./world.atlas-nodes.0106.58c9bb6518f3ed7a.js)
- Static atlas data chunk: [`world.atlas-nodes.0107.4348092bfabbb093.js`](./world.atlas-nodes.0107.4348092bfabbb093.js)
- Static atlas data chunk: [`world.atlas-nodes.0108.32cd70a5165287da.js`](./world.atlas-nodes.0108.32cd70a5165287da.js)
- Static atlas data chunk: [`world.atlas-nodes.0109.831c8cb7532a89ec.js`](./world.atlas-nodes.0109.831c8cb7532a89ec.js)
- Static atlas data chunk: [`world.atlas-nodes.0110.cd645450ef53815c.js`](./world.atlas-nodes.0110.cd645450ef53815c.js)
- Static atlas data chunk: [`world.atlas-nodes.0111.54049e89c125d9df.js`](./world.atlas-nodes.0111.54049e89c125d9df.js)
- Static atlas data chunk: [`world.atlas-nodes.0112.0c75e38687cb2ac5.js`](./world.atlas-nodes.0112.0c75e38687cb2ac5.js)
- Static atlas data chunk: [`world.atlas-edges.0113.29a4ed2539e207a7.js`](./world.atlas-edges.0113.29a4ed2539e207a7.js)
- Static atlas data chunk: [`world.atlas-sequences.0114.7babc28f7dfebcf3.js`](./world.atlas-sequences.0114.7babc28f7dfebcf3.js)
- Static atlas data chunk: [`world.atlas-indexes.0115.abf63681dd219577.js`](./world.atlas-indexes.0115.abf63681dd219577.js)
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
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Goat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `25` |
| Goat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `1` |
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `63` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Cat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `24` |
| Cat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `9` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `476` |
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

- Total animal locality points: `151`
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
| approximate | 6 |
| exact | 143 |
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
| goat | Capra hircus | domesticated_core | 25 |
| goat | Capra hircus | wild_or_progenitor_context | 1 |
| horse | Equus caballus | domesticated_core | 63 |
| horse | Equus caballus | wild_or_progenitor_context | 15 |
| cat | Felis catus | domesticated_core | 24 |
| cat | Felis catus | wild_or_progenitor_context | 15 |
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |


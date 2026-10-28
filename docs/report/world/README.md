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
- Static atlas data chunk: [`world.atlas-provenance.0000.69771794b9ca6e73.js`](./world.atlas-provenance.0000.69771794b9ca6e73.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.0f72aca0fa98866f.js`](./world.atlas-nodes.0001.0f72aca0fa98866f.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.0c95adc788fc193b.js`](./world.atlas-nodes.0002.0c95adc788fc193b.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.ae7bad61599a1f62.js`](./world.atlas-nodes.0003.ae7bad61599a1f62.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.e226ee1f7d6d7f12.js`](./world.atlas-nodes.0004.e226ee1f7d6d7f12.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.2a42cf1581399c95.js`](./world.atlas-nodes.0005.2a42cf1581399c95.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.10afcaf1d20ae505.js`](./world.atlas-nodes.0006.10afcaf1d20ae505.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.9f321334f86e6677.js`](./world.atlas-nodes.0007.9f321334f86e6677.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.6a6fed115cfdb7f6.js`](./world.atlas-nodes.0008.6a6fed115cfdb7f6.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.8b080f90d67bb056.js`](./world.atlas-nodes.0009.8b080f90d67bb056.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.592d597ae5203b63.js`](./world.atlas-nodes.0010.592d597ae5203b63.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.280e301e3c508b90.js`](./world.atlas-nodes.0011.280e301e3c508b90.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.c030a1d2cf93e847.js`](./world.atlas-nodes.0012.c030a1d2cf93e847.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.0861a07eb2228548.js`](./world.atlas-nodes.0013.0861a07eb2228548.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.ee1a036e0cb612b7.js`](./world.atlas-nodes.0014.ee1a036e0cb612b7.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.8b1e58c4fde5135a.js`](./world.atlas-nodes.0015.8b1e58c4fde5135a.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.1137f7e5f7d23398.js`](./world.atlas-nodes.0016.1137f7e5f7d23398.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.d232ab5c82f92484.js`](./world.atlas-nodes.0017.d232ab5c82f92484.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.920f051ef2c62e49.js`](./world.atlas-nodes.0018.920f051ef2c62e49.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.56875ebe768f055d.js`](./world.atlas-nodes.0019.56875ebe768f055d.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.d23c979d2dd69301.js`](./world.atlas-nodes.0020.d23c979d2dd69301.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.4c23083014e25738.js`](./world.atlas-nodes.0021.4c23083014e25738.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.aff53f482eb8eafe.js`](./world.atlas-nodes.0022.aff53f482eb8eafe.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.4dfa2ff826b69c9d.js`](./world.atlas-nodes.0023.4dfa2ff826b69c9d.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.2360b2f34daa75c3.js`](./world.atlas-nodes.0024.2360b2f34daa75c3.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.c4899548019689db.js`](./world.atlas-nodes.0025.c4899548019689db.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.2df201273b8ed02e.js`](./world.atlas-nodes.0026.2df201273b8ed02e.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.e141600627fb6ea0.js`](./world.atlas-nodes.0027.e141600627fb6ea0.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.b1852002f1c25e86.js`](./world.atlas-nodes.0028.b1852002f1c25e86.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.a7509ff63a82ab5d.js`](./world.atlas-nodes.0029.a7509ff63a82ab5d.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.f296742c4955e7bf.js`](./world.atlas-nodes.0030.f296742c4955e7bf.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.5be2a7d4c020d724.js`](./world.atlas-nodes.0031.5be2a7d4c020d724.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.1f82726f1f6821e5.js`](./world.atlas-nodes.0032.1f82726f1f6821e5.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.f63dd08d8cbcc956.js`](./world.atlas-nodes.0033.f63dd08d8cbcc956.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.8ce351e3c516475f.js`](./world.atlas-nodes.0034.8ce351e3c516475f.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.f628ccb122636add.js`](./world.atlas-nodes.0035.f628ccb122636add.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.29ca2a8d9245e2c2.js`](./world.atlas-nodes.0036.29ca2a8d9245e2c2.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.bb23672db07a2849.js`](./world.atlas-nodes.0037.bb23672db07a2849.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.3cf0626aad6a3ae6.js`](./world.atlas-nodes.0038.3cf0626aad6a3ae6.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.016079eb45e51e8b.js`](./world.atlas-nodes.0039.016079eb45e51e8b.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.ea205580074a6b2d.js`](./world.atlas-nodes.0040.ea205580074a6b2d.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.9d59e0b43ec57c68.js`](./world.atlas-nodes.0041.9d59e0b43ec57c68.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.e6a52a92da422172.js`](./world.atlas-nodes.0042.e6a52a92da422172.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.c73127349e4f9a0b.js`](./world.atlas-nodes.0043.c73127349e4f9a0b.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.bc848467110109eb.js`](./world.atlas-nodes.0044.bc848467110109eb.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.c1b7d8221f11a363.js`](./world.atlas-nodes.0045.c1b7d8221f11a363.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.ab107d4cb9ee80de.js`](./world.atlas-nodes.0046.ab107d4cb9ee80de.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.10f3261903ffc93c.js`](./world.atlas-nodes.0047.10f3261903ffc93c.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.a478bb2b34db93ab.js`](./world.atlas-nodes.0048.a478bb2b34db93ab.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.cba3d7614a12295f.js`](./world.atlas-nodes.0049.cba3d7614a12295f.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.a6992995d7dc160f.js`](./world.atlas-nodes.0050.a6992995d7dc160f.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.aff895042744502d.js`](./world.atlas-nodes.0051.aff895042744502d.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.25921f2e675eda1b.js`](./world.atlas-nodes.0052.25921f2e675eda1b.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.6a76315a69e4a779.js`](./world.atlas-nodes.0053.6a76315a69e4a779.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.50937173d25f6761.js`](./world.atlas-nodes.0054.50937173d25f6761.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.c5efe5b34745415c.js`](./world.atlas-nodes.0055.c5efe5b34745415c.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.aa0b76b75d20fbc9.js`](./world.atlas-nodes.0056.aa0b76b75d20fbc9.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.ae12ddaf73cca372.js`](./world.atlas-nodes.0057.ae12ddaf73cca372.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.2983e58a2cc60cbe.js`](./world.atlas-nodes.0058.2983e58a2cc60cbe.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.ef80b10ddbe4d159.js`](./world.atlas-nodes.0059.ef80b10ddbe4d159.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.37e7814d2fc5f73a.js`](./world.atlas-nodes.0060.37e7814d2fc5f73a.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.a6129a528a39bc8d.js`](./world.atlas-nodes.0061.a6129a528a39bc8d.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.c7d88da38f2aec56.js`](./world.atlas-nodes.0062.c7d88da38f2aec56.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.ada7824844ea768c.js`](./world.atlas-nodes.0063.ada7824844ea768c.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.487b7817541c8be1.js`](./world.atlas-nodes.0064.487b7817541c8be1.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.7383b1e902e0cc65.js`](./world.atlas-nodes.0065.7383b1e902e0cc65.js)
- Static atlas data chunk: [`world.atlas-nodes.0066.885084375a649d13.js`](./world.atlas-nodes.0066.885084375a649d13.js)
- Static atlas data chunk: [`world.atlas-nodes.0067.5dddec2c7b76b331.js`](./world.atlas-nodes.0067.5dddec2c7b76b331.js)
- Static atlas data chunk: [`world.atlas-nodes.0068.fc112d274f5bcc05.js`](./world.atlas-nodes.0068.fc112d274f5bcc05.js)
- Static atlas data chunk: [`world.atlas-nodes.0069.8ad8e790d6eeaa50.js`](./world.atlas-nodes.0069.8ad8e790d6eeaa50.js)
- Static atlas data chunk: [`world.atlas-nodes.0070.db2536f886b560b6.js`](./world.atlas-nodes.0070.db2536f886b560b6.js)
- Static atlas data chunk: [`world.atlas-nodes.0071.b54c0875c69b8893.js`](./world.atlas-nodes.0071.b54c0875c69b8893.js)
- Static atlas data chunk: [`world.atlas-nodes.0072.465c20ecbe02d5d5.js`](./world.atlas-nodes.0072.465c20ecbe02d5d5.js)
- Static atlas data chunk: [`world.atlas-nodes.0073.30cb8c125dcc984c.js`](./world.atlas-nodes.0073.30cb8c125dcc984c.js)
- Static atlas data chunk: [`world.atlas-nodes.0074.f72bc9de1ba1b53a.js`](./world.atlas-nodes.0074.f72bc9de1ba1b53a.js)
- Static atlas data chunk: [`world.atlas-nodes.0075.23984751c97c2ec7.js`](./world.atlas-nodes.0075.23984751c97c2ec7.js)
- Static atlas data chunk: [`world.atlas-nodes.0076.5d84410c8328f725.js`](./world.atlas-nodes.0076.5d84410c8328f725.js)
- Static atlas data chunk: [`world.atlas-nodes.0077.98fea28fb1c4d573.js`](./world.atlas-nodes.0077.98fea28fb1c4d573.js)
- Static atlas data chunk: [`world.atlas-nodes.0078.5a10fa748ced214c.js`](./world.atlas-nodes.0078.5a10fa748ced214c.js)
- Static atlas data chunk: [`world.atlas-nodes.0079.51a4f92184d28e00.js`](./world.atlas-nodes.0079.51a4f92184d28e00.js)
- Static atlas data chunk: [`world.atlas-nodes.0080.bda8bb23b487e3f4.js`](./world.atlas-nodes.0080.bda8bb23b487e3f4.js)
- Static atlas data chunk: [`world.atlas-nodes.0081.af960a0d185ad04b.js`](./world.atlas-nodes.0081.af960a0d185ad04b.js)
- Static atlas data chunk: [`world.atlas-nodes.0082.e3f14c15a72ea9f8.js`](./world.atlas-nodes.0082.e3f14c15a72ea9f8.js)
- Static atlas data chunk: [`world.atlas-nodes.0083.afd87914fabeda85.js`](./world.atlas-nodes.0083.afd87914fabeda85.js)
- Static atlas data chunk: [`world.atlas-nodes.0084.1059983f4d3d590e.js`](./world.atlas-nodes.0084.1059983f4d3d590e.js)
- Static atlas data chunk: [`world.atlas-nodes.0085.038294c3e4d046a9.js`](./world.atlas-nodes.0085.038294c3e4d046a9.js)
- Static atlas data chunk: [`world.atlas-nodes.0086.39e9557d98ca7ac5.js`](./world.atlas-nodes.0086.39e9557d98ca7ac5.js)
- Static atlas data chunk: [`world.atlas-nodes.0087.909da1e176aa750e.js`](./world.atlas-nodes.0087.909da1e176aa750e.js)
- Static atlas data chunk: [`world.atlas-nodes.0088.a0750c693d58502e.js`](./world.atlas-nodes.0088.a0750c693d58502e.js)
- Static atlas data chunk: [`world.atlas-nodes.0089.3e2ebecd84357582.js`](./world.atlas-nodes.0089.3e2ebecd84357582.js)
- Static atlas data chunk: [`world.atlas-nodes.0090.8f1fa87fcc013692.js`](./world.atlas-nodes.0090.8f1fa87fcc013692.js)
- Static atlas data chunk: [`world.atlas-nodes.0091.345bf4ce5a2a137b.js`](./world.atlas-nodes.0091.345bf4ce5a2a137b.js)
- Static atlas data chunk: [`world.atlas-nodes.0092.cf228b9c02e68403.js`](./world.atlas-nodes.0092.cf228b9c02e68403.js)
- Static atlas data chunk: [`world.atlas-nodes.0093.865456741693e928.js`](./world.atlas-nodes.0093.865456741693e928.js)
- Static atlas data chunk: [`world.atlas-nodes.0094.a88db4d31f7e9c51.js`](./world.atlas-nodes.0094.a88db4d31f7e9c51.js)
- Static atlas data chunk: [`world.atlas-nodes.0095.d79a9613b8c6a2e2.js`](./world.atlas-nodes.0095.d79a9613b8c6a2e2.js)
- Static atlas data chunk: [`world.atlas-nodes.0096.29543c5cb28d74f7.js`](./world.atlas-nodes.0096.29543c5cb28d74f7.js)
- Static atlas data chunk: [`world.atlas-nodes.0097.4ed8782c5bcb3931.js`](./world.atlas-nodes.0097.4ed8782c5bcb3931.js)
- Static atlas data chunk: [`world.atlas-nodes.0098.b531686f39dc6866.js`](./world.atlas-nodes.0098.b531686f39dc6866.js)
- Static atlas data chunk: [`world.atlas-nodes.0099.d4d1ed6982408562.js`](./world.atlas-nodes.0099.d4d1ed6982408562.js)
- Static atlas data chunk: [`world.atlas-nodes.0100.0fb045cf55325b36.js`](./world.atlas-nodes.0100.0fb045cf55325b36.js)
- Static atlas data chunk: [`world.atlas-nodes.0101.4a9317caf877d01d.js`](./world.atlas-nodes.0101.4a9317caf877d01d.js)
- Static atlas data chunk: [`world.atlas-nodes.0102.f9dee9e0d11bd780.js`](./world.atlas-nodes.0102.f9dee9e0d11bd780.js)
- Static atlas data chunk: [`world.atlas-nodes.0103.1f44a79a6c018d9f.js`](./world.atlas-nodes.0103.1f44a79a6c018d9f.js)
- Static atlas data chunk: [`world.atlas-nodes.0104.acc0817375318fac.js`](./world.atlas-nodes.0104.acc0817375318fac.js)
- Static atlas data chunk: [`world.atlas-nodes.0105.f4358ec4ac85e669.js`](./world.atlas-nodes.0105.f4358ec4ac85e669.js)
- Static atlas data chunk: [`world.atlas-nodes.0106.e288256f3cfee801.js`](./world.atlas-nodes.0106.e288256f3cfee801.js)
- Static atlas data chunk: [`world.atlas-nodes.0107.b7eff647ea1cc072.js`](./world.atlas-nodes.0107.b7eff647ea1cc072.js)
- Static atlas data chunk: [`world.atlas-nodes.0108.a9e652d3588ed432.js`](./world.atlas-nodes.0108.a9e652d3588ed432.js)
- Static atlas data chunk: [`world.atlas-nodes.0109.30f2af9e0216716f.js`](./world.atlas-nodes.0109.30f2af9e0216716f.js)
- Static atlas data chunk: [`world.atlas-nodes.0110.84e273da940b4bb6.js`](./world.atlas-nodes.0110.84e273da940b4bb6.js)
- Static atlas data chunk: [`world.atlas-nodes.0111.b6f7450fbe524bc0.js`](./world.atlas-nodes.0111.b6f7450fbe524bc0.js)
- Static atlas data chunk: [`world.atlas-nodes.0112.fd82e2cd9f150217.js`](./world.atlas-nodes.0112.fd82e2cd9f150217.js)
- Static atlas data chunk: [`world.atlas-nodes.0113.9fbc2333a8cf23cd.js`](./world.atlas-nodes.0113.9fbc2333a8cf23cd.js)
- Static atlas data chunk: [`world.atlas-nodes.0114.0d38926bfc7f7d6c.js`](./world.atlas-nodes.0114.0d38926bfc7f7d6c.js)
- Static atlas data chunk: [`world.atlas-nodes.0115.7cd0d9de4b326f23.js`](./world.atlas-nodes.0115.7cd0d9de4b326f23.js)
- Static atlas data chunk: [`world.atlas-nodes.0116.d3a5174c279ff408.js`](./world.atlas-nodes.0116.d3a5174c279ff408.js)
- Static atlas data chunk: [`world.atlas-nodes.0117.3b0955059479c9fc.js`](./world.atlas-nodes.0117.3b0955059479c9fc.js)
- Static atlas data chunk: [`world.atlas-nodes.0118.03d7af514f012086.js`](./world.atlas-nodes.0118.03d7af514f012086.js)
- Static atlas data chunk: [`world.atlas-nodes.0119.82eaa1d5f71bf9e0.js`](./world.atlas-nodes.0119.82eaa1d5f71bf9e0.js)
- Static atlas data chunk: [`world.atlas-edges.0120.6be7ce14d3ea393d.js`](./world.atlas-edges.0120.6be7ce14d3ea393d.js)
- Static atlas data chunk: [`world.atlas-sequences.0121.df42accfcfee8157.js`](./world.atlas-sequences.0121.df42accfcfee8157.js)
- Static atlas data chunk: [`world.atlas-indexes.0122.b35adc2f64028d2f.js`](./world.atlas-indexes.0122.b35adc2f64028d2f.js)
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
| Horse aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `66` |
| Horse aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `13` |
| Cat aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `24` |
| Cat aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `15` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `31` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `5` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `258` |
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

- Total animal locality points: `167`
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
| exact | 141 |
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
| horse | Equus caballus | domesticated_core | 66 |
| horse | Equus caballus | wild_or_progenitor_context | 13 |
| cat | Felis catus | domesticated_core | 24 |
| cat | Felis catus | wild_or_progenitor_context | 15 |
| sheep | Ovis aries | domesticated_core | 2 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The current world publication retains the human metadata population and carries 167 animal locality features for 335 mapped normalized records plus 335 distinct source-chronology record uses. Typed child supports preserve original dates and gaps; these display populations do not establish independent animals or ecological events.

**Unsupported claim.** World is a scope name, not worldwide source completeness, genotype analysis, scientific country/chronology admission or validated fieldwork advice.

**Actual verification performed.** The current saved atlas consumer at 1b338ee91 reconciles all 1,481 normalized source records. Native map assembly at that source passed in 333.12 seconds, RSS 5,366,333,440 B; independent decoded preservation and search references passed in 35.10 seconds, RSS 708,460,544 B. All unrelated scientific payloads, dates and coordinates are preserved. Current world/Europe index factories pass; Nordic qualification is reused only after exact code, bootstrap, controller, wire and semantic equality. Actual served runtime passes 27 cases, including four contextual Qinghai dates and a recovered horse owner. Seventeen targeted reader guards pass. Prior failures and their corrections are retained; no model or source census replay. The current thirteen-input entity reconciliation at 10bf26d61 confirms 1,481 = 335 mapped + 1,146 excluded in 167 features, with unchanged twelve-ID Nordic subset; country producers and older captures were not rerun.

**Remaining input or review.** Broader source coverage, sample chronology/geography/rights and scientific admission remain incomplete. The narrow served World temporal cases do not qualify all browser/network behavior or query latency.

**Cause category.** Publication scope and heterogeneous metadata layers with incomplete scientific/global coverage.

**Consequence.** Withheld Nordic environmental/context overlays do not become globally available by widening the map frame; source-sample chronology overlays are not additional biological samples.

**Precise next acceptance route.** Use the qualified current bundle/assets and source-bound temporal/index evidence; qualify broader source coverage and each family role before worldwide scientific or historical inference.

**Negative or refused result.** Nordic-only context overlays remain withheld; zero comparator layers do not imply absence of wild/progenitor context. Earlier 161/318, 165/322 and 170/331 animal populations remain historical.

**Matched denominator.** 1,733 point-layer record uses across fifteen point layers: 1,231 human metadata records + 167 animal locality features + 335 source-chronology uses. Human metadata retains 447 localities. The 335 mapped animal records and 335 source-chronology uses have different identity populations despite equal counts. Global animal accounting is 1,481 normalized records = 335 mapped + 1,146 exclusions. All 1,492 source chronology owners = 335 displayable + 1,157 refusals. Do not pool these units.

- [Retained qualification evidence: docs/report/world/world_summary.json](world_summary.json) (SHA-256 `abcec5e43b4e2ef10b970108aa2596c1fe16dfced1d4964df55a34d3fc058832`).

- [Retained qualification evidence: docs/report/world/world_map_publication_contract.json](world_map_publication_contract.json) (SHA-256 `c786a6feed15289ee5f54904703044361da2f6b4caab8b19c63abe22ece68153`).

- [Retained qualification evidence: reports/science/animal-entity-capability/report.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/report.json) (SHA-256 `a397c3e5d71adb1b77f3aca3a0f0e991dbac4e81f0946554b5b78ee9228089e4`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

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
- Static atlas data chunk: [`world.atlas-provenance.0000.43efb4e2cbd5a646.js`](./world.atlas-provenance.0000.43efb4e2cbd5a646.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.0dbe65bd053317ab.js`](./world.atlas-nodes.0001.0dbe65bd053317ab.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.6f5df582620e76fe.js`](./world.atlas-nodes.0002.6f5df582620e76fe.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.5b8df33062016000.js`](./world.atlas-nodes.0003.5b8df33062016000.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.84dbccf52a8f72de.js`](./world.atlas-nodes.0004.84dbccf52a8f72de.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.fd7cc2026f3183e3.js`](./world.atlas-nodes.0005.fd7cc2026f3183e3.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.c91938aa3bb4ce7b.js`](./world.atlas-nodes.0006.c91938aa3bb4ce7b.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.782d90b32529aac9.js`](./world.atlas-nodes.0007.782d90b32529aac9.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.8b8d6bf36801babf.js`](./world.atlas-nodes.0008.8b8d6bf36801babf.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.2590016e0439b6ae.js`](./world.atlas-nodes.0009.2590016e0439b6ae.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.62795128939f15b5.js`](./world.atlas-nodes.0010.62795128939f15b5.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.d0d57e976fe15cfb.js`](./world.atlas-nodes.0011.d0d57e976fe15cfb.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.e8ce6928b2a17f7a.js`](./world.atlas-nodes.0012.e8ce6928b2a17f7a.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.016c01f0c6cbeb6b.js`](./world.atlas-nodes.0013.016c01f0c6cbeb6b.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.2e8a6bc3b35baeeb.js`](./world.atlas-nodes.0014.2e8a6bc3b35baeeb.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.e7c2bd0834edb074.js`](./world.atlas-nodes.0015.e7c2bd0834edb074.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.2e1f534746f618c2.js`](./world.atlas-nodes.0016.2e1f534746f618c2.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.70387724d60dee98.js`](./world.atlas-nodes.0017.70387724d60dee98.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.56d59d5e2c2f1a02.js`](./world.atlas-nodes.0018.56d59d5e2c2f1a02.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.713ba32c503fcbf7.js`](./world.atlas-nodes.0019.713ba32c503fcbf7.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.201b0ff348b69f69.js`](./world.atlas-nodes.0020.201b0ff348b69f69.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.cb7cf54aaa06834b.js`](./world.atlas-nodes.0021.cb7cf54aaa06834b.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.a061a46b375f696f.js`](./world.atlas-nodes.0022.a061a46b375f696f.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.b572b2fb8fb39839.js`](./world.atlas-nodes.0023.b572b2fb8fb39839.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.c844adf590f82b76.js`](./world.atlas-nodes.0024.c844adf590f82b76.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.6747c2ab405f8653.js`](./world.atlas-nodes.0025.6747c2ab405f8653.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.762ce98c6a28bbda.js`](./world.atlas-nodes.0026.762ce98c6a28bbda.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.3dd021276c2028ea.js`](./world.atlas-nodes.0027.3dd021276c2028ea.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.31f3c4b05f60c834.js`](./world.atlas-nodes.0028.31f3c4b05f60c834.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.922367eec6465b03.js`](./world.atlas-nodes.0029.922367eec6465b03.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.fa6c23d97ae83f05.js`](./world.atlas-nodes.0030.fa6c23d97ae83f05.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.32b1d6e6bc65202a.js`](./world.atlas-nodes.0031.32b1d6e6bc65202a.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.012aebdf5c30fd84.js`](./world.atlas-nodes.0032.012aebdf5c30fd84.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.df4964f3db5377b9.js`](./world.atlas-nodes.0033.df4964f3db5377b9.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.fde97d84d29a7e0d.js`](./world.atlas-nodes.0034.fde97d84d29a7e0d.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.c3f3ac60edc7c531.js`](./world.atlas-nodes.0035.c3f3ac60edc7c531.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.c2a85e09dce5ed4a.js`](./world.atlas-nodes.0036.c2a85e09dce5ed4a.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.e57668e3af090d07.js`](./world.atlas-nodes.0037.e57668e3af090d07.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.c0d099842a6e090b.js`](./world.atlas-nodes.0038.c0d099842a6e090b.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.54c73daa57e3c574.js`](./world.atlas-nodes.0039.54c73daa57e3c574.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.fb71d44d88a43d62.js`](./world.atlas-nodes.0040.fb71d44d88a43d62.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.d26cf46590c7e38f.js`](./world.atlas-nodes.0041.d26cf46590c7e38f.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.1ec57c7e61cac33e.js`](./world.atlas-nodes.0042.1ec57c7e61cac33e.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.9fd009cc3c54fb9c.js`](./world.atlas-nodes.0043.9fd009cc3c54fb9c.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.f8c45bfb88441bd0.js`](./world.atlas-nodes.0044.f8c45bfb88441bd0.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.0f975c37586a1873.js`](./world.atlas-nodes.0045.0f975c37586a1873.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.9b5bbb9f43a5cff3.js`](./world.atlas-nodes.0046.9b5bbb9f43a5cff3.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.0355947a7ed317bd.js`](./world.atlas-nodes.0047.0355947a7ed317bd.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.becf298c26d4aec0.js`](./world.atlas-nodes.0048.becf298c26d4aec0.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.34ee06e793f791b6.js`](./world.atlas-nodes.0049.34ee06e793f791b6.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.c717346e2e0eb202.js`](./world.atlas-nodes.0050.c717346e2e0eb202.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.d5e224ca934806f2.js`](./world.atlas-nodes.0051.d5e224ca934806f2.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.800a6f37c842c3be.js`](./world.atlas-nodes.0052.800a6f37c842c3be.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.0d999badf44c8da4.js`](./world.atlas-nodes.0053.0d999badf44c8da4.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.625d91cd42104ecc.js`](./world.atlas-nodes.0054.625d91cd42104ecc.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.9f292455819414c1.js`](./world.atlas-nodes.0055.9f292455819414c1.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.bbaebe0a587349ff.js`](./world.atlas-nodes.0056.bbaebe0a587349ff.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.0ea7315bb88d4692.js`](./world.atlas-nodes.0057.0ea7315bb88d4692.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.d499739430186347.js`](./world.atlas-nodes.0058.d499739430186347.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.cadbf0df7af04b1b.js`](./world.atlas-nodes.0059.cadbf0df7af04b1b.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.3adf26e20b82f0ad.js`](./world.atlas-nodes.0060.3adf26e20b82f0ad.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.99d619621325a2db.js`](./world.atlas-nodes.0061.99d619621325a2db.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.c66e8f8f779b049a.js`](./world.atlas-nodes.0062.c66e8f8f779b049a.js)
- Static atlas data chunk: [`world.atlas-nodes.0063.08dea91ce4ab4acf.js`](./world.atlas-nodes.0063.08dea91ce4ab4acf.js)
- Static atlas data chunk: [`world.atlas-nodes.0064.4400ed0731472aad.js`](./world.atlas-nodes.0064.4400ed0731472aad.js)
- Static atlas data chunk: [`world.atlas-nodes.0065.460684a8f18b0859.js`](./world.atlas-nodes.0065.460684a8f18b0859.js)
- Static atlas data chunk: [`world.atlas-nodes.0066.810feb881f6af056.js`](./world.atlas-nodes.0066.810feb881f6af056.js)
- Static atlas data chunk: [`world.atlas-nodes.0067.e65310d1132c9a9c.js`](./world.atlas-nodes.0067.e65310d1132c9a9c.js)
- Static atlas data chunk: [`world.atlas-nodes.0068.e4181118293d7f2d.js`](./world.atlas-nodes.0068.e4181118293d7f2d.js)
- Static atlas data chunk: [`world.atlas-nodes.0069.c8fd2143d656e303.js`](./world.atlas-nodes.0069.c8fd2143d656e303.js)
- Static atlas data chunk: [`world.atlas-nodes.0070.6b34d25dd33d5d20.js`](./world.atlas-nodes.0070.6b34d25dd33d5d20.js)
- Static atlas data chunk: [`world.atlas-nodes.0071.bfff95ee5a3a41a2.js`](./world.atlas-nodes.0071.bfff95ee5a3a41a2.js)
- Static atlas data chunk: [`world.atlas-nodes.0072.75212e7a651a1b10.js`](./world.atlas-nodes.0072.75212e7a651a1b10.js)
- Static atlas data chunk: [`world.atlas-nodes.0073.91f6cbd9a788850a.js`](./world.atlas-nodes.0073.91f6cbd9a788850a.js)
- Static atlas data chunk: [`world.atlas-nodes.0074.78f1ceb19e41828b.js`](./world.atlas-nodes.0074.78f1ceb19e41828b.js)
- Static atlas data chunk: [`world.atlas-nodes.0075.3daf56bac86b0835.js`](./world.atlas-nodes.0075.3daf56bac86b0835.js)
- Static atlas data chunk: [`world.atlas-nodes.0076.18fbb02d545087bd.js`](./world.atlas-nodes.0076.18fbb02d545087bd.js)
- Static atlas data chunk: [`world.atlas-nodes.0077.b7ce1c7a35016725.js`](./world.atlas-nodes.0077.b7ce1c7a35016725.js)
- Static atlas data chunk: [`world.atlas-nodes.0078.f71b888df4c00524.js`](./world.atlas-nodes.0078.f71b888df4c00524.js)
- Static atlas data chunk: [`world.atlas-nodes.0079.2f7cefe0f3789cbf.js`](./world.atlas-nodes.0079.2f7cefe0f3789cbf.js)
- Static atlas data chunk: [`world.atlas-nodes.0080.8f31511f09701c6e.js`](./world.atlas-nodes.0080.8f31511f09701c6e.js)
- Static atlas data chunk: [`world.atlas-nodes.0081.24cbc1d938b39c7e.js`](./world.atlas-nodes.0081.24cbc1d938b39c7e.js)
- Static atlas data chunk: [`world.atlas-nodes.0082.dc41959513cd41f9.js`](./world.atlas-nodes.0082.dc41959513cd41f9.js)
- Static atlas data chunk: [`world.atlas-nodes.0083.dcc5753afe2789e1.js`](./world.atlas-nodes.0083.dcc5753afe2789e1.js)
- Static atlas data chunk: [`world.atlas-nodes.0084.3da1f84fc1e67f13.js`](./world.atlas-nodes.0084.3da1f84fc1e67f13.js)
- Static atlas data chunk: [`world.atlas-nodes.0085.19a47dc72fb4aad7.js`](./world.atlas-nodes.0085.19a47dc72fb4aad7.js)
- Static atlas data chunk: [`world.atlas-nodes.0086.db91154508bfdb36.js`](./world.atlas-nodes.0086.db91154508bfdb36.js)
- Static atlas data chunk: [`world.atlas-nodes.0087.607ba6dd4be24b2b.js`](./world.atlas-nodes.0087.607ba6dd4be24b2b.js)
- Static atlas data chunk: [`world.atlas-nodes.0088.8294f82fdbb782b5.js`](./world.atlas-nodes.0088.8294f82fdbb782b5.js)
- Static atlas data chunk: [`world.atlas-nodes.0089.3143c619272df26b.js`](./world.atlas-nodes.0089.3143c619272df26b.js)
- Static atlas data chunk: [`world.atlas-nodes.0090.7c8ab9e4bff42125.js`](./world.atlas-nodes.0090.7c8ab9e4bff42125.js)
- Static atlas data chunk: [`world.atlas-nodes.0091.f309a2126d6f54ce.js`](./world.atlas-nodes.0091.f309a2126d6f54ce.js)
- Static atlas data chunk: [`world.atlas-nodes.0092.ab7e7b5c8f4027f2.js`](./world.atlas-nodes.0092.ab7e7b5c8f4027f2.js)
- Static atlas data chunk: [`world.atlas-nodes.0093.9ee83e9549c63f54.js`](./world.atlas-nodes.0093.9ee83e9549c63f54.js)
- Static atlas data chunk: [`world.atlas-nodes.0094.3933eade0782aa40.js`](./world.atlas-nodes.0094.3933eade0782aa40.js)
- Static atlas data chunk: [`world.atlas-nodes.0095.a1f88fddd2a9f48d.js`](./world.atlas-nodes.0095.a1f88fddd2a9f48d.js)
- Static atlas data chunk: [`world.atlas-nodes.0096.96dba3db9ca28df3.js`](./world.atlas-nodes.0096.96dba3db9ca28df3.js)
- Static atlas data chunk: [`world.atlas-nodes.0097.efdf9990c8f6d296.js`](./world.atlas-nodes.0097.efdf9990c8f6d296.js)
- Static atlas data chunk: [`world.atlas-nodes.0098.65a2433a836891ad.js`](./world.atlas-nodes.0098.65a2433a836891ad.js)
- Static atlas data chunk: [`world.atlas-nodes.0099.39228372a5f432f5.js`](./world.atlas-nodes.0099.39228372a5f432f5.js)
- Static atlas data chunk: [`world.atlas-nodes.0100.bcd6c38d30bb0d5a.js`](./world.atlas-nodes.0100.bcd6c38d30bb0d5a.js)
- Static atlas data chunk: [`world.atlas-nodes.0101.fb5f047fe54d8850.js`](./world.atlas-nodes.0101.fb5f047fe54d8850.js)
- Static atlas data chunk: [`world.atlas-nodes.0102.0cd10648e8bccb1b.js`](./world.atlas-nodes.0102.0cd10648e8bccb1b.js)
- Static atlas data chunk: [`world.atlas-nodes.0103.5fd4c57d2ac6edcd.js`](./world.atlas-nodes.0103.5fd4c57d2ac6edcd.js)
- Static atlas data chunk: [`world.atlas-nodes.0104.60f46432f636981b.js`](./world.atlas-nodes.0104.60f46432f636981b.js)
- Static atlas data chunk: [`world.atlas-nodes.0105.60fe5c4541d6824c.js`](./world.atlas-nodes.0105.60fe5c4541d6824c.js)
- Static atlas data chunk: [`world.atlas-nodes.0106.dac835dc2df92d88.js`](./world.atlas-nodes.0106.dac835dc2df92d88.js)
- Static atlas data chunk: [`world.atlas-nodes.0107.a0f42bf8e7264205.js`](./world.atlas-nodes.0107.a0f42bf8e7264205.js)
- Static atlas data chunk: [`world.atlas-nodes.0108.0da639475353c04b.js`](./world.atlas-nodes.0108.0da639475353c04b.js)
- Static atlas data chunk: [`world.atlas-nodes.0109.fc5fc5dc28e99afb.js`](./world.atlas-nodes.0109.fc5fc5dc28e99afb.js)
- Static atlas data chunk: [`world.atlas-nodes.0110.3aad187fb7a88440.js`](./world.atlas-nodes.0110.3aad187fb7a88440.js)
- Static atlas data chunk: [`world.atlas-nodes.0111.258a9f5a44b121fa.js`](./world.atlas-nodes.0111.258a9f5a44b121fa.js)
- Static atlas data chunk: [`world.atlas-nodes.0112.e5f6b95b3e0c86cf.js`](./world.atlas-nodes.0112.e5f6b95b3e0c86cf.js)
- Static atlas data chunk: [`world.atlas-edges.0113.29a4ed2539e207a7.js`](./world.atlas-edges.0113.29a4ed2539e207a7.js)
- Static atlas data chunk: [`world.atlas-sequences.0114.7babc28f7dfebcf3.js`](./world.atlas-sequences.0114.7babc28f7dfebcf3.js)
- Static atlas data chunk: [`world.atlas-indexes.0115.41ce9f3f2c83016c.js`](./world.atlas-indexes.0115.41ce9f3f2c83016c.js)
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


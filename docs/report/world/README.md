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
- Static atlas data chunk: [`world.atlas-provenance.0000.702815c6774437a4.js`](./world.atlas-provenance.0000.702815c6774437a4.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.ed99ce3fc9cc6ed0.js`](./world.atlas-nodes.0001.ed99ce3fc9cc6ed0.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.c2997e4a9e19017d.js`](./world.atlas-nodes.0002.c2997e4a9e19017d.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.163f7a09b4dd9ce4.js`](./world.atlas-nodes.0003.163f7a09b4dd9ce4.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.a34ca8489da0b12c.js`](./world.atlas-nodes.0004.a34ca8489da0b12c.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.3b560c16e2982f0b.js`](./world.atlas-nodes.0005.3b560c16e2982f0b.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.3fec420a48ec41ec.js`](./world.atlas-nodes.0006.3fec420a48ec41ec.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.907a4ad28330e958.js`](./world.atlas-nodes.0007.907a4ad28330e958.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.8c962c2a29ec8b72.js`](./world.atlas-nodes.0008.8c962c2a29ec8b72.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.7f9ea58829e2add9.js`](./world.atlas-nodes.0009.7f9ea58829e2add9.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.60bc3c0e95d1fa9b.js`](./world.atlas-nodes.0010.60bc3c0e95d1fa9b.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.6a5810a66abf689e.js`](./world.atlas-nodes.0011.6a5810a66abf689e.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.189e9a132a6b0124.js`](./world.atlas-nodes.0012.189e9a132a6b0124.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.daf28f2cc61f5c14.js`](./world.atlas-nodes.0013.daf28f2cc61f5c14.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.a5f0621c2251b1ca.js`](./world.atlas-nodes.0014.a5f0621c2251b1ca.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.7fe12e310e1f6f65.js`](./world.atlas-nodes.0015.7fe12e310e1f6f65.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.225f1da6584411a7.js`](./world.atlas-nodes.0016.225f1da6584411a7.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.3dfee86bfac08ab2.js`](./world.atlas-nodes.0017.3dfee86bfac08ab2.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.b9d38f3c5efce9a6.js`](./world.atlas-nodes.0018.b9d38f3c5efce9a6.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.64a51a0b7251ba22.js`](./world.atlas-nodes.0019.64a51a0b7251ba22.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.372364ed8eebaee4.js`](./world.atlas-nodes.0020.372364ed8eebaee4.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.57fa64443224c20e.js`](./world.atlas-nodes.0021.57fa64443224c20e.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.da89fa71ee9f0d29.js`](./world.atlas-nodes.0022.da89fa71ee9f0d29.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.c9d7251462c61731.js`](./world.atlas-nodes.0023.c9d7251462c61731.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.56162da8d90c72a8.js`](./world.atlas-nodes.0024.56162da8d90c72a8.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.9ecee6dcc00399e9.js`](./world.atlas-nodes.0025.9ecee6dcc00399e9.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.365a7245f97c1b85.js`](./world.atlas-nodes.0026.365a7245f97c1b85.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.8a15903abbe39787.js`](./world.atlas-nodes.0027.8a15903abbe39787.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.95ad58e911223f5c.js`](./world.atlas-nodes.0028.95ad58e911223f5c.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.4f589443541a8b52.js`](./world.atlas-nodes.0029.4f589443541a8b52.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.a8eb07d88749aceb.js`](./world.atlas-nodes.0030.a8eb07d88749aceb.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.56e5c589c5d91374.js`](./world.atlas-nodes.0031.56e5c589c5d91374.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.a8e28d27f77d03e4.js`](./world.atlas-nodes.0032.a8e28d27f77d03e4.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.b294dde4550a3f73.js`](./world.atlas-nodes.0033.b294dde4550a3f73.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.52efcca1c3341e9f.js`](./world.atlas-nodes.0034.52efcca1c3341e9f.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.a8dc918271b21012.js`](./world.atlas-nodes.0035.a8dc918271b21012.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.04af3d13e4ba9798.js`](./world.atlas-nodes.0036.04af3d13e4ba9798.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.e5e7421f54977d07.js`](./world.atlas-nodes.0037.e5e7421f54977d07.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.dc9a883411c5cbfa.js`](./world.atlas-nodes.0038.dc9a883411c5cbfa.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.7f108c1e81129dd2.js`](./world.atlas-nodes.0039.7f108c1e81129dd2.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.70636fb0fe7b2c8e.js`](./world.atlas-nodes.0040.70636fb0fe7b2c8e.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.bfa43a1ae584f4b9.js`](./world.atlas-nodes.0041.bfa43a1ae584f4b9.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.26e03dd8036d3826.js`](./world.atlas-nodes.0042.26e03dd8036d3826.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.de395fbaf6ae1af9.js`](./world.atlas-nodes.0043.de395fbaf6ae1af9.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.0bfaf3a82fc3316c.js`](./world.atlas-nodes.0044.0bfaf3a82fc3316c.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.e9173f20dea32da9.js`](./world.atlas-nodes.0045.e9173f20dea32da9.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.26dd9f15eec9838c.js`](./world.atlas-nodes.0046.26dd9f15eec9838c.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.7634573df35a58e0.js`](./world.atlas-nodes.0047.7634573df35a58e0.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.11cd7bc815f939fd.js`](./world.atlas-nodes.0048.11cd7bc815f939fd.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.54e1488aa6ad8fef.js`](./world.atlas-nodes.0049.54e1488aa6ad8fef.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.48bc2ed8c04ff5db.js`](./world.atlas-nodes.0050.48bc2ed8c04ff5db.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.73da0193807b1b09.js`](./world.atlas-nodes.0051.73da0193807b1b09.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.e4cf83fdb8e334d3.js`](./world.atlas-nodes.0052.e4cf83fdb8e334d3.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.b8b995b2d866b246.js`](./world.atlas-nodes.0053.b8b995b2d866b246.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.4e8a83ea32e65784.js`](./world.atlas-nodes.0054.4e8a83ea32e65784.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.85ccb213e47dcbde.js`](./world.atlas-nodes.0055.85ccb213e47dcbde.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.54ff54ba01e34c6f.js`](./world.atlas-nodes.0056.54ff54ba01e34c6f.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.0d708719956a9cd3.js`](./world.atlas-nodes.0057.0d708719956a9cd3.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.2ee9d286d0556d63.js`](./world.atlas-nodes.0058.2ee9d286d0556d63.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.c729dd4fb2109a74.js`](./world.atlas-nodes.0059.c729dd4fb2109a74.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.8be8329b1bb66716.js`](./world.atlas-nodes.0060.8be8329b1bb66716.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.eadd378d19edfe98.js`](./world.atlas-nodes.0061.eadd378d19edfe98.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.e52e0b8bdbb29007.js`](./world.atlas-nodes.0062.e52e0b8bdbb29007.js)
- Static atlas data chunk: [`world.atlas-edges.0063.14722c4811250994.js`](./world.atlas-edges.0063.14722c4811250994.js)
- Static atlas data chunk: [`world.atlas-sequences.0064.ec0b6d01e7b9b10f.js`](./world.atlas-sequences.0064.ec0b6d01e7b9b10f.js)
- Static atlas data chunk: [`world.atlas-indexes.0065.0580e955e3ffc029.js`](./world.atlas-indexes.0065.0580e955e3ffc029.js)
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


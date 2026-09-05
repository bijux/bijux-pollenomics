# World Evidence Surface

This shared interactive map bundle was generated on `2026-09-05` from Homo
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
- Default basemap: `voyager`
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
- Animal atlas evidence CSV: [`world_animal_atlas_evidence.csv`](./world_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`world_animal_atlas_evidence.json`](./world_animal_atlas_evidence.json)
- Animal point traceability JSON: [`world_animal_point_traceability.json`](./world_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`world_map_assets.json`](./world_map_assets.json)
- Static atlas data chunk: [`world.atlas-provenance.0000.3e775997194d8c8d.js`](./world.atlas-provenance.0000.3e775997194d8c8d.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.6b709491f1020dcb.js`](./world.atlas-nodes.0001.6b709491f1020dcb.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.a566d8157a774505.js`](./world.atlas-nodes.0002.a566d8157a774505.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.944cbd3aba6f7ba1.js`](./world.atlas-nodes.0003.944cbd3aba6f7ba1.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.2728c1f96a44540d.js`](./world.atlas-nodes.0004.2728c1f96a44540d.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.dae4a101e76e1bf5.js`](./world.atlas-nodes.0005.dae4a101e76e1bf5.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.eeb371084933bc10.js`](./world.atlas-nodes.0006.eeb371084933bc10.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.94f3356e501fb3ca.js`](./world.atlas-nodes.0007.94f3356e501fb3ca.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.3245c2f622bb90b5.js`](./world.atlas-nodes.0008.3245c2f622bb90b5.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.8272192c45dfd1cc.js`](./world.atlas-nodes.0009.8272192c45dfd1cc.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.8967cdb665a0d39a.js`](./world.atlas-nodes.0010.8967cdb665a0d39a.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.cd0b35f9a890f0a2.js`](./world.atlas-nodes.0011.cd0b35f9a890f0a2.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.afdc8ec3597091c0.js`](./world.atlas-nodes.0012.afdc8ec3597091c0.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.f6a0ccd11eca58dd.js`](./world.atlas-nodes.0013.f6a0ccd11eca58dd.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.a94594cb7ee2d9f2.js`](./world.atlas-nodes.0014.a94594cb7ee2d9f2.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.54ca3c71183e6cc8.js`](./world.atlas-nodes.0015.54ca3c71183e6cc8.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.67eb96f10bf14ab0.js`](./world.atlas-nodes.0016.67eb96f10bf14ab0.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.ccf57f155e50b5fd.js`](./world.atlas-nodes.0017.ccf57f155e50b5fd.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.475f43419dcc2179.js`](./world.atlas-nodes.0018.475f43419dcc2179.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.280c3236bfaf8101.js`](./world.atlas-nodes.0019.280c3236bfaf8101.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.58b2aa25515cd045.js`](./world.atlas-nodes.0020.58b2aa25515cd045.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.0897a9bb451c3b29.js`](./world.atlas-nodes.0021.0897a9bb451c3b29.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.ab26037e49e97add.js`](./world.atlas-nodes.0022.ab26037e49e97add.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.acd7d3cf9f418d4b.js`](./world.atlas-nodes.0023.acd7d3cf9f418d4b.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.79295988279a3ffe.js`](./world.atlas-nodes.0024.79295988279a3ffe.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.0c09335633a30db3.js`](./world.atlas-nodes.0025.0c09335633a30db3.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.8f6494936ddcab78.js`](./world.atlas-nodes.0026.8f6494936ddcab78.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.e605bbca6571e3f8.js`](./world.atlas-nodes.0027.e605bbca6571e3f8.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.190707f6a6e28ef5.js`](./world.atlas-nodes.0028.190707f6a6e28ef5.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.7bec2310258ffaec.js`](./world.atlas-nodes.0029.7bec2310258ffaec.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.957541a392b0e43c.js`](./world.atlas-nodes.0030.957541a392b0e43c.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.c95562e5a6b981e6.js`](./world.atlas-nodes.0031.c95562e5a6b981e6.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.628c398da575bcf2.js`](./world.atlas-nodes.0032.628c398da575bcf2.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.96ee8b0fa24195c5.js`](./world.atlas-nodes.0033.96ee8b0fa24195c5.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.b24558f9b59f4306.js`](./world.atlas-nodes.0034.b24558f9b59f4306.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.3397ce9ae6647c36.js`](./world.atlas-nodes.0035.3397ce9ae6647c36.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.c28bc2715c756a43.js`](./world.atlas-nodes.0036.c28bc2715c756a43.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.55558e0c20e8d839.js`](./world.atlas-nodes.0037.55558e0c20e8d839.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.2f6bc6135b3fb370.js`](./world.atlas-nodes.0038.2f6bc6135b3fb370.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.767dae97cc1b09fa.js`](./world.atlas-nodes.0039.767dae97cc1b09fa.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.f52e5bc428d6cb0a.js`](./world.atlas-nodes.0040.f52e5bc428d6cb0a.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.182e7fd607fd2e8a.js`](./world.atlas-nodes.0041.182e7fd607fd2e8a.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.47568e40c4e8cfff.js`](./world.atlas-nodes.0042.47568e40c4e8cfff.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.d8f48ef258ab83eb.js`](./world.atlas-nodes.0043.d8f48ef258ab83eb.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.fd63925bab170b67.js`](./world.atlas-nodes.0044.fd63925bab170b67.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.e8abb72bc6c0776f.js`](./world.atlas-nodes.0045.e8abb72bc6c0776f.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.7c04a86b3a28e705.js`](./world.atlas-nodes.0046.7c04a86b3a28e705.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.284381268abf813d.js`](./world.atlas-nodes.0047.284381268abf813d.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.9229f25a914ea33f.js`](./world.atlas-nodes.0048.9229f25a914ea33f.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.7e3913d35a0f3e72.js`](./world.atlas-nodes.0049.7e3913d35a0f3e72.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.c94be03388751fc0.js`](./world.atlas-nodes.0050.c94be03388751fc0.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.def1857848f8a3a3.js`](./world.atlas-nodes.0051.def1857848f8a3a3.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.70df81b488740dba.js`](./world.atlas-nodes.0052.70df81b488740dba.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.2a1746c7a5815117.js`](./world.atlas-nodes.0053.2a1746c7a5815117.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.134f05d033eab9fd.js`](./world.atlas-nodes.0054.134f05d033eab9fd.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.3f8b1c32e727c3c3.js`](./world.atlas-nodes.0055.3f8b1c32e727c3c3.js)
- Static atlas data chunk: [`world.atlas-edges.0056.7f1b35eb0effd7ea.js`](./world.atlas-edges.0056.7f1b35eb0effd7ea.js)
- Static atlas data chunk: [`world.atlas-sequences.0057.0cd6162dde5f2a2c.js`](./world.atlas-sequences.0057.0cd6162dde5f2a2c.js)
- Static atlas data chunk: [`world.atlas-indexes.0058.e6929affb87fa3e0.js`](./world.atlas-indexes.0058.e6929affb87fa3e0.js)
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
| Goat aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `26` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `207` |
| Pig aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
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

- Total animal locality points: `235`
- Shipped animal species: `3`
- Domesticated-core species layers: `3`
- Comparator species layers: `0`

### Layer Groups

- Domesticated-core animal evidence
- Comparator animal evidence

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
| approximate | 2 |
| exact | 233 |

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| goat | Capra hircus | domesticated_core | 26 |
| horse | Equus caballus | domesticated_core | 207 |
| pig | Sus scrofa domesticus | domesticated_core | 2 |


# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-05` from Homo
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
- Default basemap: `voyager`
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
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.91cb31e04b1e0bc4.js`](./nordic.atlas-provenance.0000.91cb31e04b1e0bc4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.727aabb155e3c5f3.js`](./nordic.atlas-nodes.0001.727aabb155e3c5f3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.ad43079490d7dc57.js`](./nordic.atlas-nodes.0002.ad43079490d7dc57.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.238cb9c9d40bc136.js`](./nordic.atlas-nodes.0003.238cb9c9d40bc136.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.0ec9c0c0ded5da40.js`](./nordic.atlas-nodes.0004.0ec9c0c0ded5da40.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.3d53d32a6891a95a.js`](./nordic.atlas-nodes.0005.3d53d32a6891a95a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.0aa3e6351ec345e1.js`](./nordic.atlas-nodes.0006.0aa3e6351ec345e1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.425206b5ede40ddb.js`](./nordic.atlas-nodes.0007.425206b5ede40ddb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.616ec3ce70a67ec1.js`](./nordic.atlas-nodes.0008.616ec3ce70a67ec1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.7cb9c9204adf2e41.js`](./nordic.atlas-nodes.0009.7cb9c9204adf2e41.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.2c82d005a535f965.js`](./nordic.atlas-nodes.0010.2c82d005a535f965.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.e006aad7f1d9a28b.js`](./nordic.atlas-nodes.0011.e006aad7f1d9a28b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.5204d5bd23f301b8.js`](./nordic.atlas-nodes.0012.5204d5bd23f301b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.06747229382d9b98.js`](./nordic.atlas-nodes.0013.06747229382d9b98.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.e794e2eeb57ba114.js`](./nordic.atlas-nodes.0014.e794e2eeb57ba114.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.60700af0d3daa3c0.js`](./nordic.atlas-nodes.0015.60700af0d3daa3c0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.fab53ee2364a2a21.js`](./nordic.atlas-nodes.0016.fab53ee2364a2a21.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.d90e0277a4dbbb1b.js`](./nordic.atlas-nodes.0017.d90e0277a4dbbb1b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.37e1469fb673b6a9.js`](./nordic.atlas-nodes.0018.37e1469fb673b6a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.a077348fcd34823d.js`](./nordic.atlas-nodes.0019.a077348fcd34823d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.b3ec507ff4eec325.js`](./nordic.atlas-nodes.0020.b3ec507ff4eec325.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.b1a625cfbc0a011f.js`](./nordic.atlas-nodes.0021.b1a625cfbc0a011f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.d27a36192cf7e1ed.js`](./nordic.atlas-nodes.0022.d27a36192cf7e1ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.8fa6e8001c3ff249.js`](./nordic.atlas-nodes.0023.8fa6e8001c3ff249.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.7d92bd12bd3eab00.js`](./nordic.atlas-nodes.0024.7d92bd12bd3eab00.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.eb5614ff01f29d20.js`](./nordic.atlas-nodes.0025.eb5614ff01f29d20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.462f09d092072b38.js`](./nordic.atlas-nodes.0026.462f09d092072b38.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.501c1049f40d3db0.js`](./nordic.atlas-nodes.0027.501c1049f40d3db0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.4ca43ea21f998ce3.js`](./nordic.atlas-nodes.0028.4ca43ea21f998ce3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.1bd8851a439f0244.js`](./nordic.atlas-nodes.0029.1bd8851a439f0244.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.58ce1aa22d100f3e.js`](./nordic.atlas-nodes.0030.58ce1aa22d100f3e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.b6f59262f8e7fdbf.js`](./nordic.atlas-nodes.0031.b6f59262f8e7fdbf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.0017de52b654afb2.js`](./nordic.atlas-nodes.0032.0017de52b654afb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.2d96cee53a70dcd4.js`](./nordic.atlas-nodes.0033.2d96cee53a70dcd4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.436d67cd40b4841c.js`](./nordic.atlas-nodes.0034.436d67cd40b4841c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.c91629cc5847c2e0.js`](./nordic.atlas-nodes.0035.c91629cc5847c2e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.1243ed07ec9449fe.js`](./nordic.atlas-nodes.0036.1243ed07ec9449fe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.f0752ae02a0b5dfd.js`](./nordic.atlas-nodes.0037.f0752ae02a0b5dfd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.d14ea442b26e893b.js`](./nordic.atlas-nodes.0038.d14ea442b26e893b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.99aed0cfe3f4eee9.js`](./nordic.atlas-nodes.0039.99aed0cfe3f4eee9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.c372bc8c4aa90b59.js`](./nordic.atlas-nodes.0040.c372bc8c4aa90b59.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.e5b1370b536bcf25.js`](./nordic.atlas-nodes.0041.e5b1370b536bcf25.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.932d46b13d8b61e1.js`](./nordic.atlas-nodes.0042.932d46b13d8b61e1.js)
- Static atlas data chunk: [`nordic.atlas-details.0043.2bed5bead23a5ca8.js`](./nordic.atlas-details.0043.2bed5bead23a5ca8.js)
- Static atlas data chunk: [`nordic.atlas-details.0044.0dfbabcf954447ef.js`](./nordic.atlas-details.0044.0dfbabcf954447ef.js)
- Static atlas data chunk: [`nordic.atlas-details.0045.efa18b1f0bfbf876.js`](./nordic.atlas-details.0045.efa18b1f0bfbf876.js)
- Static atlas data chunk: [`nordic.atlas-details.0046.1912367c7c1da410.js`](./nordic.atlas-details.0046.1912367c7c1da410.js)
- Static atlas data chunk: [`nordic.atlas-details.0047.799de841db992ab2.js`](./nordic.atlas-details.0047.799de841db992ab2.js)
- Static atlas data chunk: [`nordic.atlas-details.0048.d20ee6d1fb3dde54.js`](./nordic.atlas-details.0048.d20ee6d1fb3dde54.js)
- Static atlas data chunk: [`nordic.atlas-details.0049.14802c402631c491.js`](./nordic.atlas-details.0049.14802c402631c491.js)
- Static atlas data chunk: [`nordic.atlas-details.0050.18c961da9bcdb483.js`](./nordic.atlas-details.0050.18c961da9bcdb483.js)
- Static atlas data chunk: [`nordic.atlas-details.0051.0c683b1df919a949.js`](./nordic.atlas-details.0051.0c683b1df919a949.js)
- Static atlas data chunk: [`nordic.atlas-details.0052.526c55d5106c1b96.js`](./nordic.atlas-details.0052.526c55d5106c1b96.js)
- Static atlas data chunk: [`nordic.atlas-details.0053.c5695585637577db.js`](./nordic.atlas-details.0053.c5695585637577db.js)
- Static atlas data chunk: [`nordic.atlas-details.0054.db713634676dce2c.js`](./nordic.atlas-details.0054.db713634676dce2c.js)
- Static atlas data chunk: [`nordic.atlas-details.0055.6cb20241ad975583.js`](./nordic.atlas-details.0055.6cb20241ad975583.js)
- Static atlas data chunk: [`nordic.atlas-details.0056.3bcf983a29fb2efd.js`](./nordic.atlas-details.0056.3bcf983a29fb2efd.js)
- Static atlas data chunk: [`nordic.atlas-details.0057.95dbd15129745658.js`](./nordic.atlas-details.0057.95dbd15129745658.js)
- Static atlas data chunk: [`nordic.atlas-details.0058.9815af48add816d3.js`](./nordic.atlas-details.0058.9815af48add816d3.js)
- Static atlas data chunk: [`nordic.atlas-details.0059.701cea18a33532bb.js`](./nordic.atlas-details.0059.701cea18a33532bb.js)
- Static atlas data chunk: [`nordic.atlas-details.0060.3af8ab9ebb3e0632.js`](./nordic.atlas-details.0060.3af8ab9ebb3e0632.js)
- Static atlas data chunk: [`nordic.atlas-details.0061.cf62d76a4c86f7ec.js`](./nordic.atlas-details.0061.cf62d76a4c86f7ec.js)
- Static atlas data chunk: [`nordic.atlas-details.0062.f3a1629c47ea5448.js`](./nordic.atlas-details.0062.f3a1629c47ea5448.js)
- Static atlas data chunk: [`nordic.atlas-details.0063.02e46e02952cdd6a.js`](./nordic.atlas-details.0063.02e46e02952cdd6a.js)
- Static atlas data chunk: [`nordic.atlas-details.0064.6dc4ef874dde5899.js`](./nordic.atlas-details.0064.6dc4ef874dde5899.js)
- Static atlas data chunk: [`nordic.atlas-details.0065.9cf2ecf582d8e488.js`](./nordic.atlas-details.0065.9cf2ecf582d8e488.js)
- Static atlas data chunk: [`nordic.atlas-details.0066.f85bbcb28783c843.js`](./nordic.atlas-details.0066.f85bbcb28783c843.js)
- Static atlas data chunk: [`nordic.atlas-details.0067.349163334d69cae5.js`](./nordic.atlas-details.0067.349163334d69cae5.js)
- Static atlas data chunk: [`nordic.atlas-details.0068.8a399dab8ebda077.js`](./nordic.atlas-details.0068.8a399dab8ebda077.js)
- Static atlas data chunk: [`nordic.atlas-details.0069.e4f0f888577ab29f.js`](./nordic.atlas-details.0069.e4f0f888577ab29f.js)
- Static atlas data chunk: [`nordic.atlas-details.0070.9be4e2e69b804849.js`](./nordic.atlas-details.0070.9be4e2e69b804849.js)
- Static atlas data chunk: [`nordic.atlas-details.0071.3b7dd8cabc832287.js`](./nordic.atlas-details.0071.3b7dd8cabc832287.js)
- Static atlas data chunk: [`nordic.atlas-details.0072.2974d4a615167b75.js`](./nordic.atlas-details.0072.2974d4a615167b75.js)
- Static atlas data chunk: [`nordic.atlas-details.0073.411ccf1879fcd456.js`](./nordic.atlas-details.0073.411ccf1879fcd456.js)
- Static atlas data chunk: [`nordic.atlas-details.0074.9fed5662105b222b.js`](./nordic.atlas-details.0074.9fed5662105b222b.js)
- Static atlas data chunk: [`nordic.atlas-details.0075.063b67538ca21938.js`](./nordic.atlas-details.0075.063b67538ca21938.js)
- Static atlas data chunk: [`nordic.atlas-details.0076.fbf7460a066038dc.js`](./nordic.atlas-details.0076.fbf7460a066038dc.js)
- Static atlas data chunk: [`nordic.atlas-details.0077.c4cf0d2eb0ff2c6f.js`](./nordic.atlas-details.0077.c4cf0d2eb0ff2c6f.js)
- Static atlas data chunk: [`nordic.atlas-details.0078.01ab7f4eb531115a.js`](./nordic.atlas-details.0078.01ab7f4eb531115a.js)
- Static atlas data chunk: [`nordic.atlas-details.0079.96c15b557fc8b82d.js`](./nordic.atlas-details.0079.96c15b557fc8b82d.js)
- Static atlas data chunk: [`nordic.atlas-details.0080.2c83d65e5e1c7f05.js`](./nordic.atlas-details.0080.2c83d65e5e1c7f05.js)
- Static atlas data chunk: [`nordic.atlas-details.0081.b3a6872d39a0420f.js`](./nordic.atlas-details.0081.b3a6872d39a0420f.js)
- Static atlas data chunk: [`nordic.atlas-details.0082.ecc439ae23cee10b.js`](./nordic.atlas-details.0082.ecc439ae23cee10b.js)
- Static atlas data chunk: [`nordic.atlas-details.0083.49fb2d9a25a6f1bf.js`](./nordic.atlas-details.0083.49fb2d9a25a6f1bf.js)
- Static atlas data chunk: [`nordic.atlas-details.0084.f08dc15914d9a7f5.js`](./nordic.atlas-details.0084.f08dc15914d9a7f5.js)
- Static atlas data chunk: [`nordic.atlas-details.0085.afbb2f5f2d396622.js`](./nordic.atlas-details.0085.afbb2f5f2d396622.js)
- Static atlas data chunk: [`nordic.atlas-details.0086.5d2b039ac658635b.js`](./nordic.atlas-details.0086.5d2b039ac658635b.js)
- Static atlas data chunk: [`nordic.atlas-details.0087.2c2de3850fc9966a.js`](./nordic.atlas-details.0087.2c2de3850fc9966a.js)
- Static atlas data chunk: [`nordic.atlas-details.0088.e1208940b57c0534.js`](./nordic.atlas-details.0088.e1208940b57c0534.js)
- Static atlas data chunk: [`nordic.atlas-details.0089.3a1ad4cbfcdf311a.js`](./nordic.atlas-details.0089.3a1ad4cbfcdf311a.js)
- Static atlas data chunk: [`nordic.atlas-details.0090.cd40903949e2ecc9.js`](./nordic.atlas-details.0090.cd40903949e2ecc9.js)
- Static atlas data chunk: [`nordic.atlas-details.0091.1e0195964d81c81b.js`](./nordic.atlas-details.0091.1e0195964d81c81b.js)
- Static atlas data chunk: [`nordic.atlas-details.0092.a408aa4903317af8.js`](./nordic.atlas-details.0092.a408aa4903317af8.js)
- Static atlas data chunk: [`nordic.atlas-details.0093.7e41651bd3a38357.js`](./nordic.atlas-details.0093.7e41651bd3a38357.js)
- Static atlas data chunk: [`nordic.atlas-details.0094.d223c390b2f4941a.js`](./nordic.atlas-details.0094.d223c390b2f4941a.js)
- Static atlas data chunk: [`nordic.atlas-details.0095.36abb76fdb5ef183.js`](./nordic.atlas-details.0095.36abb76fdb5ef183.js)
- Static atlas data chunk: [`nordic.atlas-details.0096.dbe383c24bce6413.js`](./nordic.atlas-details.0096.dbe383c24bce6413.js)
- Static atlas data chunk: [`nordic.atlas-details.0097.a993964ae7cb77da.js`](./nordic.atlas-details.0097.a993964ae7cb77da.js)
- Static atlas data chunk: [`nordic.atlas-details.0098.d593418ffeee57f0.js`](./nordic.atlas-details.0098.d593418ffeee57f0.js)
- Static atlas data chunk: [`nordic.atlas-details.0099.dc51ce29139cd9fb.js`](./nordic.atlas-details.0099.dc51ce29139cd9fb.js)
- Static atlas data chunk: [`nordic.atlas-details.0100.404029cf9cf504b0.js`](./nordic.atlas-details.0100.404029cf9cf504b0.js)
- Static atlas data chunk: [`nordic.atlas-details.0101.320880b9ef69154b.js`](./nordic.atlas-details.0101.320880b9ef69154b.js)
- Static atlas data chunk: [`nordic.atlas-details.0102.364eeea41c7e8377.js`](./nordic.atlas-details.0102.364eeea41c7e8377.js)
- Static atlas data chunk: [`nordic.atlas-details.0103.eefa87e748ff11ff.js`](./nordic.atlas-details.0103.eefa87e748ff11ff.js)
- Static atlas data chunk: [`nordic.atlas-details.0104.d7cc484b07bb5ee3.js`](./nordic.atlas-details.0104.d7cc484b07bb5ee3.js)
- Static atlas data chunk: [`nordic.atlas-details.0105.92438f6307b8f717.js`](./nordic.atlas-details.0105.92438f6307b8f717.js)
- Static atlas data chunk: [`nordic.atlas-details.0106.a4851b9c40ebbbc1.js`](./nordic.atlas-details.0106.a4851b9c40ebbbc1.js)
- Static atlas data chunk: [`nordic.atlas-edges.0107.1a4b4d641ff56dbd.js`](./nordic.atlas-edges.0107.1a4b4d641ff56dbd.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0108.d4ecaf24d84525b2.js`](./nordic.atlas-sequences.0108.d4ecaf24d84525b2.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0109.d3d847cff3b8c539.js`](./nordic.atlas-indexes.0109.d3d847cff3b8c539.js)
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

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | Pollen sequences staged from the LandClim normalization bundle. | `490` |
| Neotoma pollen sites | `scope_specific_overlay` | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `200` |
| SEAD sites | `scope_specific_overlay` | Environmental archaeology sites staged from the SEAD normalization bundle. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `9738` |
| Horse aDNA site evidence | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |
| LandClim REVEALS time-window grids | `scope_specific_overlay` | Time-window-specific REVEALS grid estimates from published LandClim PANGAEA datasets. | `2515` |

## Governed Filters

- Country filters
- Layer toggles
- Search
- Time window
- Distance circles
- Basemap switch
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

- Total animal locality points: `2`
- Shipped animal species: `1`
- Domesticated-core species layers: `1`
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
| exact | 2 |

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| horse | Equus caballus | domesticated_core | 2 |


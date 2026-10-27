# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-29` from Homo
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
- RAÄ atlas input status: [`raa_atlas_input_status.json`](./raa_atlas_input_status.json)
- RAÄ archaeology density: [`sweden_archaeology_density.geojson`](./sweden_archaeology_density.geojson)
- Animal locality GeoJSON: [`nordic_animal_localities.geojson`](./nordic_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`nordic_domesticated_animal_localities.geojson`](./nordic_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`nordic_comparator_animal_localities.geojson`](./nordic_comparator_animal_localities.geojson)
- Wild and progenitor animal locality GeoJSON: [`nordic_progenitor_animal_localities.geojson`](./nordic_progenitor_animal_localities.geojson)
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.7765e73328a7d055.js`](./nordic.atlas-provenance.0000.7765e73328a7d055.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.0db2e2f9401703f0.js`](./nordic.atlas-nodes.0001.0db2e2f9401703f0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.ee7cb3acfa80aacf.js`](./nordic.atlas-nodes.0002.ee7cb3acfa80aacf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.d81d02684164df1a.js`](./nordic.atlas-nodes.0003.d81d02684164df1a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.4348253fd6adf426.js`](./nordic.atlas-nodes.0004.4348253fd6adf426.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.bb165092058bea5e.js`](./nordic.atlas-nodes.0005.bb165092058bea5e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.3551f05325223aeb.js`](./nordic.atlas-nodes.0006.3551f05325223aeb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.7bffa995eef26373.js`](./nordic.atlas-nodes.0007.7bffa995eef26373.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.acf6f026dcac70d7.js`](./nordic.atlas-nodes.0008.acf6f026dcac70d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.d78e4350ac1ea845.js`](./nordic.atlas-nodes.0009.d78e4350ac1ea845.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.1a0b456f2e574cc9.js`](./nordic.atlas-nodes.0010.1a0b456f2e574cc9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.3626c21dfe150198.js`](./nordic.atlas-nodes.0011.3626c21dfe150198.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.60de09c425e60fe0.js`](./nordic.atlas-nodes.0012.60de09c425e60fe0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.7af78cd99467c235.js`](./nordic.atlas-nodes.0013.7af78cd99467c235.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.2970329585fcb5a3.js`](./nordic.atlas-nodes.0014.2970329585fcb5a3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.b416708f0e990a3d.js`](./nordic.atlas-nodes.0015.b416708f0e990a3d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.ed0d6eac13a70dec.js`](./nordic.atlas-nodes.0016.ed0d6eac13a70dec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.247f356267a87b2e.js`](./nordic.atlas-nodes.0017.247f356267a87b2e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.57b984f2d29c6b81.js`](./nordic.atlas-nodes.0018.57b984f2d29c6b81.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.3806f7243898dbfc.js`](./nordic.atlas-nodes.0019.3806f7243898dbfc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.a9d162da37262cb7.js`](./nordic.atlas-nodes.0020.a9d162da37262cb7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.2da6bd4b8f6a5336.js`](./nordic.atlas-nodes.0021.2da6bd4b8f6a5336.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.4da898dc64f366a3.js`](./nordic.atlas-nodes.0022.4da898dc64f366a3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.271d2cbff929f32d.js`](./nordic.atlas-nodes.0023.271d2cbff929f32d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.ad422fe153706314.js`](./nordic.atlas-nodes.0024.ad422fe153706314.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.1f59995bc8018dac.js`](./nordic.atlas-nodes.0025.1f59995bc8018dac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.3b7916d3ad51da90.js`](./nordic.atlas-nodes.0026.3b7916d3ad51da90.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.78a32e0df87e2c61.js`](./nordic.atlas-nodes.0027.78a32e0df87e2c61.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.aa916de0da9a46f8.js`](./nordic.atlas-nodes.0028.aa916de0da9a46f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.fd36948fd8ae1751.js`](./nordic.atlas-nodes.0029.fd36948fd8ae1751.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.0c0204a1f64642d5.js`](./nordic.atlas-nodes.0030.0c0204a1f64642d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.e667f27774ef2949.js`](./nordic.atlas-nodes.0031.e667f27774ef2949.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.0a803d200c5e48f1.js`](./nordic.atlas-nodes.0032.0a803d200c5e48f1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.8c070c82ae944bf7.js`](./nordic.atlas-nodes.0033.8c070c82ae944bf7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.facc6f42887d122d.js`](./nordic.atlas-nodes.0034.facc6f42887d122d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.4a01e0209d147bbb.js`](./nordic.atlas-nodes.0035.4a01e0209d147bbb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.370cc877e4cb666d.js`](./nordic.atlas-nodes.0036.370cc877e4cb666d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.6a7c4ddadb604075.js`](./nordic.atlas-nodes.0037.6a7c4ddadb604075.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.2b52a1734c5a40a0.js`](./nordic.atlas-nodes.0038.2b52a1734c5a40a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.23d9aaddd272e741.js`](./nordic.atlas-nodes.0039.23d9aaddd272e741.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.5124305fafa7772c.js`](./nordic.atlas-nodes.0040.5124305fafa7772c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.2789eba0f5cea086.js`](./nordic.atlas-nodes.0041.2789eba0f5cea086.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.eb38b28e900289dc.js`](./nordic.atlas-nodes.0042.eb38b28e900289dc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.e918df2e977d86b7.js`](./nordic.atlas-nodes.0043.e918df2e977d86b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.fbcc4686ebe51255.js`](./nordic.atlas-nodes.0044.fbcc4686ebe51255.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.4a3c1a7c692deecb.js`](./nordic.atlas-nodes.0045.4a3c1a7c692deecb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.c95ff8631e8b5fbb.js`](./nordic.atlas-nodes.0046.c95ff8631e8b5fbb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.14d3a05aeb458d8c.js`](./nordic.atlas-nodes.0047.14d3a05aeb458d8c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.1600934ce4e9a8b0.js`](./nordic.atlas-nodes.0048.1600934ce4e9a8b0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.afc46b5656139ee6.js`](./nordic.atlas-nodes.0049.afc46b5656139ee6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.5dfc56024dedbc65.js`](./nordic.atlas-nodes.0050.5dfc56024dedbc65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.63accd0f777087f8.js`](./nordic.atlas-nodes.0051.63accd0f777087f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.19143c521fb3aab3.js`](./nordic.atlas-nodes.0052.19143c521fb3aab3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.07f6bf5c78db999c.js`](./nordic.atlas-nodes.0053.07f6bf5c78db999c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.1d41bf7757cb8e43.js`](./nordic.atlas-nodes.0054.1d41bf7757cb8e43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.f957e056789d3c9b.js`](./nordic.atlas-nodes.0055.f957e056789d3c9b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.c8916311d2bd670c.js`](./nordic.atlas-nodes.0056.c8916311d2bd670c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.1ac343997e3b4b3b.js`](./nordic.atlas-nodes.0057.1ac343997e3b4b3b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.11cf05e09291a0bd.js`](./nordic.atlas-nodes.0058.11cf05e09291a0bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.c38b9c1e2727cb20.js`](./nordic.atlas-nodes.0059.c38b9c1e2727cb20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.f51518102545afa5.js`](./nordic.atlas-nodes.0060.f51518102545afa5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.bcd5c666ecab96c4.js`](./nordic.atlas-nodes.0061.bcd5c666ecab96c4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.0f66867456b79ed2.js`](./nordic.atlas-nodes.0062.0f66867456b79ed2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.2b77208da1dd4b92.js`](./nordic.atlas-nodes.0063.2b77208da1dd4b92.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.bb60d30d57896729.js`](./nordic.atlas-nodes.0064.bb60d30d57896729.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.89802f683236b77a.js`](./nordic.atlas-nodes.0065.89802f683236b77a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.8f66fb813df1f5a6.js`](./nordic.atlas-nodes.0066.8f66fb813df1f5a6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.c3c4f09380097047.js`](./nordic.atlas-nodes.0067.c3c4f09380097047.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.06e4516f0ee3b3c3.js`](./nordic.atlas-nodes.0068.06e4516f0ee3b3c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.43f1abb889276e36.js`](./nordic.atlas-nodes.0069.43f1abb889276e36.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.fb878aa4d41c84a7.js`](./nordic.atlas-nodes.0070.fb878aa4d41c84a7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.43b322b6d2ed4fa3.js`](./nordic.atlas-nodes.0071.43b322b6d2ed4fa3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.fe94129c2a063ab6.js`](./nordic.atlas-nodes.0072.fe94129c2a063ab6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.78cd026644f820ec.js`](./nordic.atlas-nodes.0073.78cd026644f820ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.ef7af74036b09936.js`](./nordic.atlas-nodes.0074.ef7af74036b09936.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.15204b012ab08e6a.js`](./nordic.atlas-nodes.0075.15204b012ab08e6a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.fc010728ef20e028.js`](./nordic.atlas-nodes.0076.fc010728ef20e028.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.086dc16de79299ce.js`](./nordic.atlas-nodes.0077.086dc16de79299ce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.154b450bab90d3bf.js`](./nordic.atlas-nodes.0078.154b450bab90d3bf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.a1129a2b5582b903.js`](./nordic.atlas-nodes.0079.a1129a2b5582b903.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.80443665521dced3.js`](./nordic.atlas-nodes.0080.80443665521dced3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.d5fa9b0792df1745.js`](./nordic.atlas-nodes.0081.d5fa9b0792df1745.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.db530f68761130e1.js`](./nordic.atlas-nodes.0082.db530f68761130e1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.4de152b54658d1ea.js`](./nordic.atlas-nodes.0083.4de152b54658d1ea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.04c41bde6e7768d8.js`](./nordic.atlas-nodes.0084.04c41bde6e7768d8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.072f60c071872721.js`](./nordic.atlas-nodes.0085.072f60c071872721.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.182567e6961d1413.js`](./nordic.atlas-nodes.0086.182567e6961d1413.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.aedd3af84057d055.js`](./nordic.atlas-nodes.0087.aedd3af84057d055.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.39c778975e4714dd.js`](./nordic.atlas-nodes.0088.39c778975e4714dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.2ff582842a08e05a.js`](./nordic.atlas-nodes.0089.2ff582842a08e05a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.fe2acbbb7ea62fb4.js`](./nordic.atlas-nodes.0090.fe2acbbb7ea62fb4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.c8752341dd15f490.js`](./nordic.atlas-nodes.0091.c8752341dd15f490.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.acfce24c2ddce175.js`](./nordic.atlas-nodes.0092.acfce24c2ddce175.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.3f0a07bc87e03a8e.js`](./nordic.atlas-nodes.0093.3f0a07bc87e03a8e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.f705d1eed790bfda.js`](./nordic.atlas-nodes.0094.f705d1eed790bfda.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.ce57a5cd7b517d67.js`](./nordic.atlas-nodes.0095.ce57a5cd7b517d67.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.cd667bd9a70f39ec.js`](./nordic.atlas-nodes.0096.cd667bd9a70f39ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.4805f0bdc413f7d2.js`](./nordic.atlas-nodes.0097.4805f0bdc413f7d2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.6e503f7b2824675c.js`](./nordic.atlas-nodes.0098.6e503f7b2824675c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.6c44b13778f2e28f.js`](./nordic.atlas-nodes.0099.6c44b13778f2e28f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.097718433962b5ce.js`](./nordic.atlas-nodes.0100.097718433962b5ce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.22f0a100255ed99d.js`](./nordic.atlas-nodes.0101.22f0a100255ed99d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.a6e10a0d968d04eb.js`](./nordic.atlas-nodes.0102.a6e10a0d968d04eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.c80b4b176ea23b34.js`](./nordic.atlas-nodes.0103.c80b4b176ea23b34.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.3c8c1bbf448ffa0a.js`](./nordic.atlas-nodes.0104.3c8c1bbf448ffa0a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.d185e0c3db0f0040.js`](./nordic.atlas-nodes.0105.d185e0c3db0f0040.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.420d8a7ed1a49027.js`](./nordic.atlas-nodes.0106.420d8a7ed1a49027.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.90482a69d038886f.js`](./nordic.atlas-nodes.0107.90482a69d038886f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.162719ff9e59320d.js`](./nordic.atlas-nodes.0108.162719ff9e59320d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.70263a5c2ae1d937.js`](./nordic.atlas-nodes.0109.70263a5c2ae1d937.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.7b8a56a0c7ca7216.js`](./nordic.atlas-nodes.0110.7b8a56a0c7ca7216.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.9b46fe8f7d151860.js`](./nordic.atlas-nodes.0111.9b46fe8f7d151860.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.ddb7286e8ec962c9.js`](./nordic.atlas-nodes.0112.ddb7286e8ec962c9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.039bda4794795136.js`](./nordic.atlas-nodes.0113.039bda4794795136.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.89bb01e3cbbeaf42.js`](./nordic.atlas-nodes.0114.89bb01e3cbbeaf42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.a1c4c6b2f548e96e.js`](./nordic.atlas-nodes.0115.a1c4c6b2f548e96e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.fdb8e30820a5b520.js`](./nordic.atlas-nodes.0116.fdb8e30820a5b520.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.589316a14bc3d4f7.js`](./nordic.atlas-nodes.0117.589316a14bc3d4f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.938b5fe6a9b6a406.js`](./nordic.atlas-nodes.0118.938b5fe6a9b6a406.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.7587a4e9dd52a4c4.js`](./nordic.atlas-nodes.0119.7587a4e9dd52a4c4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.255492b9458b092c.js`](./nordic.atlas-nodes.0120.255492b9458b092c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.a7fbf4b24813628e.js`](./nordic.atlas-nodes.0121.a7fbf4b24813628e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.f766b7143da0ce79.js`](./nordic.atlas-nodes.0122.f766b7143da0ce79.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.89291b92fbcfa0de.js`](./nordic.atlas-nodes.0123.89291b92fbcfa0de.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.f4e423f6a4671cea.js`](./nordic.atlas-nodes.0124.f4e423f6a4671cea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.1be0fb86f18c6d43.js`](./nordic.atlas-nodes.0125.1be0fb86f18c6d43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.91baf1b0ee314415.js`](./nordic.atlas-nodes.0126.91baf1b0ee314415.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.7d0996ffe8d8fb5b.js`](./nordic.atlas-nodes.0127.7d0996ffe8d8fb5b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.aa574c7854534ab4.js`](./nordic.atlas-nodes.0128.aa574c7854534ab4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.2e52dce95daa708d.js`](./nordic.atlas-nodes.0129.2e52dce95daa708d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.54bb7b5098095115.js`](./nordic.atlas-nodes.0130.54bb7b5098095115.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.33f0baa474423513.js`](./nordic.atlas-nodes.0131.33f0baa474423513.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.4553232d4a89ccf4.js`](./nordic.atlas-nodes.0132.4553232d4a89ccf4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.1b67bc77f155e150.js`](./nordic.atlas-nodes.0133.1b67bc77f155e150.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.446206657bf86c84.js`](./nordic.atlas-nodes.0134.446206657bf86c84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.6263f7688b29172d.js`](./nordic.atlas-nodes.0135.6263f7688b29172d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.9befa741c7cd272b.js`](./nordic.atlas-nodes.0136.9befa741c7cd272b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.a496450a5e771015.js`](./nordic.atlas-nodes.0137.a496450a5e771015.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.dd28d99e00a59f09.js`](./nordic.atlas-nodes.0138.dd28d99e00a59f09.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.bf07246aece24841.js`](./nordic.atlas-nodes.0139.bf07246aece24841.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.605009cdcaa2de10.js`](./nordic.atlas-nodes.0140.605009cdcaa2de10.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.885d37cdd8279bf3.js`](./nordic.atlas-nodes.0141.885d37cdd8279bf3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.b7d541f2a7001c6f.js`](./nordic.atlas-nodes.0142.b7d541f2a7001c6f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.d74223dfda63aca9.js`](./nordic.atlas-nodes.0143.d74223dfda63aca9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.7a3971e49cfb8cff.js`](./nordic.atlas-nodes.0144.7a3971e49cfb8cff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.b86de2393f0865a2.js`](./nordic.atlas-nodes.0145.b86de2393f0865a2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.b0060452b52a6678.js`](./nordic.atlas-nodes.0146.b0060452b52a6678.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.2f5fc80c0a37237d.js`](./nordic.atlas-nodes.0147.2f5fc80c0a37237d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.37d4fc87adb01d63.js`](./nordic.atlas-nodes.0148.37d4fc87adb01d63.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.0f83825722bd4202.js`](./nordic.atlas-nodes.0149.0f83825722bd4202.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.63fed5b4d0030ae9.js`](./nordic.atlas-nodes.0150.63fed5b4d0030ae9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.a7535dc222e0c42d.js`](./nordic.atlas-nodes.0151.a7535dc222e0c42d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.95033133423243ca.js`](./nordic.atlas-nodes.0152.95033133423243ca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.4ec54fec29194f57.js`](./nordic.atlas-nodes.0153.4ec54fec29194f57.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.05ae9aed24a9c173.js`](./nordic.atlas-nodes.0154.05ae9aed24a9c173.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.08030b31fa80c709.js`](./nordic.atlas-nodes.0155.08030b31fa80c709.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.690ab5e1e910681a.js`](./nordic.atlas-nodes.0156.690ab5e1e910681a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.631efc7190eb19b9.js`](./nordic.atlas-nodes.0157.631efc7190eb19b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.56335924d5101f64.js`](./nordic.atlas-nodes.0158.56335924d5101f64.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.2908df4c2e9f270a.js`](./nordic.atlas-nodes.0159.2908df4c2e9f270a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.3a431df433a1249c.js`](./nordic.atlas-nodes.0160.3a431df433a1249c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.47faa577922771bd.js`](./nordic.atlas-nodes.0161.47faa577922771bd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.26e832f82a7ea47e.js`](./nordic.atlas-nodes.0162.26e832f82a7ea47e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.451cc11e8085bb9a.js`](./nordic.atlas-nodes.0163.451cc11e8085bb9a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.ed3d772326d0218b.js`](./nordic.atlas-nodes.0164.ed3d772326d0218b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.1178abecd5a55c59.js`](./nordic.atlas-nodes.0165.1178abecd5a55c59.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.364f45f049022ae5.js`](./nordic.atlas-nodes.0166.364f45f049022ae5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.f1f6b0195c561591.js`](./nordic.atlas-nodes.0167.f1f6b0195c561591.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.556cc96d625fee9b.js`](./nordic.atlas-nodes.0168.556cc96d625fee9b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.feb7bd0167bee5e4.js`](./nordic.atlas-nodes.0169.feb7bd0167bee5e4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.2fb4566eebd2171b.js`](./nordic.atlas-nodes.0170.2fb4566eebd2171b.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.b77f1612f56a4cff.js`](./nordic.atlas-details.0171.b77f1612f56a4cff.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.8992464394852770.js`](./nordic.atlas-details.0172.8992464394852770.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.91e546811135c58a.js`](./nordic.atlas-details.0173.91e546811135c58a.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.6eea34f9aaa70f2b.js`](./nordic.atlas-details.0174.6eea34f9aaa70f2b.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.f114a8730fd131b3.js`](./nordic.atlas-details.0175.f114a8730fd131b3.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.17870e644330e910.js`](./nordic.atlas-details.0176.17870e644330e910.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.bae11027de577bd7.js`](./nordic.atlas-details.0177.bae11027de577bd7.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.aa0f55eca186c7d1.js`](./nordic.atlas-details.0178.aa0f55eca186c7d1.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.d69babd8c7c2dc0e.js`](./nordic.atlas-details.0179.d69babd8c7c2dc0e.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.cebbc586e0b5b656.js`](./nordic.atlas-details.0180.cebbc586e0b5b656.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.88e04fa0996c76c2.js`](./nordic.atlas-details.0181.88e04fa0996c76c2.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.893c3d2a4ab54bbc.js`](./nordic.atlas-details.0182.893c3d2a4ab54bbc.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.a7d26cdee63da82a.js`](./nordic.atlas-details.0183.a7d26cdee63da82a.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.16f2ecab38c638bd.js`](./nordic.atlas-details.0184.16f2ecab38c638bd.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.44c271a5aba0e790.js`](./nordic.atlas-details.0185.44c271a5aba0e790.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.6b742507a495aff0.js`](./nordic.atlas-details.0186.6b742507a495aff0.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.d50e85c55e9791bc.js`](./nordic.atlas-details.0187.d50e85c55e9791bc.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.02146b7579d176d4.js`](./nordic.atlas-details.0188.02146b7579d176d4.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.8928a2d1fd132d77.js`](./nordic.atlas-details.0189.8928a2d1fd132d77.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.30ff8133f0fa9626.js`](./nordic.atlas-details.0190.30ff8133f0fa9626.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.8c539bc151ac0168.js`](./nordic.atlas-details.0191.8c539bc151ac0168.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.5b1b8e4b09317a1a.js`](./nordic.atlas-details.0192.5b1b8e4b09317a1a.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.ca94c1880814c6a7.js`](./nordic.atlas-details.0193.ca94c1880814c6a7.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.18fa09ca080e7d1f.js`](./nordic.atlas-details.0194.18fa09ca080e7d1f.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.32ebb22626f3feb6.js`](./nordic.atlas-details.0195.32ebb22626f3feb6.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.bd430ec29308197f.js`](./nordic.atlas-details.0196.bd430ec29308197f.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.0c9bc18843c12c34.js`](./nordic.atlas-details.0197.0c9bc18843c12c34.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.64b435fb6252f615.js`](./nordic.atlas-details.0198.64b435fb6252f615.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.473ad0366c6e9b69.js`](./nordic.atlas-details.0199.473ad0366c6e9b69.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.7235c3211bf56211.js`](./nordic.atlas-details.0200.7235c3211bf56211.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.bcea58d5bb7f70a0.js`](./nordic.atlas-details.0201.bcea58d5bb7f70a0.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.5f26595ad0eb06f7.js`](./nordic.atlas-details.0202.5f26595ad0eb06f7.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.2b2c251288d7bd01.js`](./nordic.atlas-details.0203.2b2c251288d7bd01.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.6602a8a80d8bac50.js`](./nordic.atlas-details.0204.6602a8a80d8bac50.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.9af601f4b70aede3.js`](./nordic.atlas-details.0205.9af601f4b70aede3.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.bd057cddc859c398.js`](./nordic.atlas-details.0206.bd057cddc859c398.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.2e0aa414d432b12c.js`](./nordic.atlas-details.0207.2e0aa414d432b12c.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.82a089a1ae895488.js`](./nordic.atlas-details.0208.82a089a1ae895488.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.bfd4480c6606b2ed.js`](./nordic.atlas-details.0209.bfd4480c6606b2ed.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.634b213066100330.js`](./nordic.atlas-details.0210.634b213066100330.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.54996646f0ebfbe8.js`](./nordic.atlas-details.0211.54996646f0ebfbe8.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.92582fa92d5446bb.js`](./nordic.atlas-details.0212.92582fa92d5446bb.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.fd0caab2a8ad18ec.js`](./nordic.atlas-details.0213.fd0caab2a8ad18ec.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.3b3a9ef9d1cef79d.js`](./nordic.atlas-details.0214.3b3a9ef9d1cef79d.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.cc34ca293105b1d0.js`](./nordic.atlas-details.0215.cc34ca293105b1d0.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.45a888f57011bdc3.js`](./nordic.atlas-details.0216.45a888f57011bdc3.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.4b994f60b71d35f3.js`](./nordic.atlas-details.0217.4b994f60b71d35f3.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.3908991fb8674110.js`](./nordic.atlas-details.0218.3908991fb8674110.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.5c4fc8f88ee4c190.js`](./nordic.atlas-details.0219.5c4fc8f88ee4c190.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.a9296899c90b734b.js`](./nordic.atlas-details.0220.a9296899c90b734b.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.e2445b60d4741878.js`](./nordic.atlas-details.0221.e2445b60d4741878.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.8039396d3357b396.js`](./nordic.atlas-details.0222.8039396d3357b396.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.04231e8adb05c887.js`](./nordic.atlas-details.0223.04231e8adb05c887.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.e8cf253dd5b9667f.js`](./nordic.atlas-details.0224.e8cf253dd5b9667f.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.d6b04d74fb06b3af.js`](./nordic.atlas-details.0225.d6b04d74fb06b3af.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.7f1b41562142fbc2.js`](./nordic.atlas-details.0226.7f1b41562142fbc2.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.7f6bd2e75517f053.js`](./nordic.atlas-details.0227.7f6bd2e75517f053.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.0147e484ea44ca8b.js`](./nordic.atlas-details.0228.0147e484ea44ca8b.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.0bfa437248998674.js`](./nordic.atlas-details.0229.0bfa437248998674.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.417578ae1267cb29.js`](./nordic.atlas-details.0230.417578ae1267cb29.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.4ba60071a06093ed.js`](./nordic.atlas-details.0231.4ba60071a06093ed.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.5bdcf141ced891c0.js`](./nordic.atlas-details.0232.5bdcf141ced891c0.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.3ddb146c7d31a966.js`](./nordic.atlas-details.0233.3ddb146c7d31a966.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.ab12336c635539ab.js`](./nordic.atlas-details.0234.ab12336c635539ab.js)
- Static atlas data chunk: [`nordic.atlas-edges.0235.09609680275615bf.js`](./nordic.atlas-edges.0235.09609680275615bf.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0236.9211d8ece031427d.js`](./nordic.atlas-sequences.0236.9211d8ece031427d.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0237.d36f54c44885495f.js`](./nordic.atlas-indexes.0237.d36f54c44885495f.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0238.e23597174ae2803e.js`](./nordic.atlas-indexes.0238.e23597174ae2803e.js)
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
- Static atlas runtime: [`nordic_map.atlas-runtime.3b396f6bf8d8ce15.js`](./nordic_map.atlas-runtime.3b396f6bf8d8ce15.js)
- Interactive evidence tools: [`nordic_map.atlas-evidence-tools.bac3f9295a5c95bb.js`](./nordic_map.atlas-evidence-tools.bac3f9295a5c95bb.js)
- Static atlas index transport: [`nordic_map.atlas-index-transport.2168d29af8354bcb.js`](./nordic_map.atlas-index-transport.2168d29af8354bcb.js)

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | Pollen sequences staged from the LandClim normalization bundle. | `490` |
| Neotoma pollen sites | `scope_specific_overlay` | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `193` |
| SEAD sites | `scope_specific_overlay` | SEAD site inventory for spatial context. Site envelopes summarize source chronology and are not dated events or interval evidence. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `8799` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `2` |
| Cat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Sheep source-sample chronology | `shared_world_scale_layer` |  | `4` |
| Pig source-sample chronology | `shared_world_scale_layer` |  | `2` |
| Neotoma sample pollen-presence context | `scope_specific_overlay` | Dated source samples with positive reported pollen observations; not reviewed pollen-sum events. | `9988` |
| Neotoma literal ecological codes | `scope_specific_overlay` | Literal source ecological codes without cross-source equivalence or propagation claims. | `25165` |
| Neotoma exact source taxa | `scope_specific_overlay` | Exact source taxon identities without accepted ecological classification or propagation claims. | `215751` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |
| LandClim REVEALS time-window grids | `scope_specific_overlay` | Time-window-specific REVEALS grid estimates from published LandClim PANGAEA datasets. | `2515` |
| RAÄ archaeology density | `scope_specific_overlay` | Sweden only. Density cells summarize `Fornlämning` counts. | `106` |

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



<!-- scientific-account-route:begin -->
## Scientific verification and limits

Cross-domain map/evidence wrapper; country/source entity accounting and explicit ecological/chronological limits remain separate.

**Supported claim.** The retained Nordic bundle adds governed pollen, archaeology, modeled, boundary and fieldwork overlays to the same shared human/animal publication engine.

**Unsupported claim.** Overlay co-location is not causal farming history, scientific admission of pollen/LRA inputs, genotype-aware analysis or measured vegetation accuracy.

**Actual verification performed.** The actual three-scope producer at 04f1c4857 passed source-value, temporal, layer, point-traceability, static-budget and playback guards in 266.419 s. Regional chronology retains 13 nodes and its original source fields. The independent actual Nordic JavaScript index observer recovered every original logical search entry in 30.51 s; this is not full browser or query-latency acceptance.

**Remaining input or review.** Each layer needs its own chronology, entity, rights and scientific decisions, plus actual browser/provider qualification for delivery claims.

**Cause category.** Regional context publication with mixed source families.

**Consequence.** Nordic overlays remain local scope evidence; a map display cannot transfer biological or chronological authority between layers.

**Precise next acceptance route.** Replay the Nordic owner and inspect source-sample/exact-label/model-window lineage, then qualify any named cross-layer scientific comparison with admitted observations.

**Negative or refused result.** Unresolved animal chronology and approximate locality warnings remain visible. Missing external basemap tiles offline are not an empty scientific layer.

**Matched denominator.** Four-country human display totals1,231 samples (SE416/NO130/FI32/DK653); eight animal locality points and one documented fieldwork location are separate evidence populations.

- [Retained qualification evidence: docs/report/regions/nordic/nordic_summary.json](nordic_summary.json) (SHA-256 `1e1c333e09061f31dc316865d162ed99988d75bc6dd93863654951c16abf390c`).

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

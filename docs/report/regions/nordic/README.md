# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-21` from Homo
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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.d159c78f54f84c39.js`](./nordic.atlas-provenance.0000.d159c78f54f84c39.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.35b174618553feeb.js`](./nordic.atlas-nodes.0001.35b174618553feeb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.534688e325c095ac.js`](./nordic.atlas-nodes.0002.534688e325c095ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.2f21b6b52a3d7c5d.js`](./nordic.atlas-nodes.0003.2f21b6b52a3d7c5d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.f6922b4fd621d983.js`](./nordic.atlas-nodes.0004.f6922b4fd621d983.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.ab1c1ac516b488cd.js`](./nordic.atlas-nodes.0005.ab1c1ac516b488cd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.d06fc47b27b34819.js`](./nordic.atlas-nodes.0006.d06fc47b27b34819.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.97bba883b1af13dc.js`](./nordic.atlas-nodes.0007.97bba883b1af13dc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.1d1078a038d0a77c.js`](./nordic.atlas-nodes.0008.1d1078a038d0a77c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.f577990beb8a4aeb.js`](./nordic.atlas-nodes.0009.f577990beb8a4aeb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.491c987cf8e5820a.js`](./nordic.atlas-nodes.0010.491c987cf8e5820a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.a597fe8195e1d0f7.js`](./nordic.atlas-nodes.0011.a597fe8195e1d0f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.e902c3a478ef9023.js`](./nordic.atlas-nodes.0012.e902c3a478ef9023.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.cba61832d6b5f78b.js`](./nordic.atlas-nodes.0013.cba61832d6b5f78b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.d8ff55d0913c7196.js`](./nordic.atlas-nodes.0014.d8ff55d0913c7196.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.1efa461faf08da88.js`](./nordic.atlas-nodes.0015.1efa461faf08da88.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.bb7a90eeb4e3b406.js`](./nordic.atlas-nodes.0016.bb7a90eeb4e3b406.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.44173322c75e6e15.js`](./nordic.atlas-nodes.0017.44173322c75e6e15.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.17471d33bd4afebf.js`](./nordic.atlas-nodes.0018.17471d33bd4afebf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.1648d03a018d0ee5.js`](./nordic.atlas-nodes.0019.1648d03a018d0ee5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.310ce2c2c3862f16.js`](./nordic.atlas-nodes.0020.310ce2c2c3862f16.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.1a4c5d19f4ab8b23.js`](./nordic.atlas-nodes.0021.1a4c5d19f4ab8b23.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.bf72230a0e600236.js`](./nordic.atlas-nodes.0022.bf72230a0e600236.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.5bbe43bdce7da6f8.js`](./nordic.atlas-nodes.0023.5bbe43bdce7da6f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.2207c5fbf66c377e.js`](./nordic.atlas-nodes.0024.2207c5fbf66c377e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.7600dd719af435e7.js`](./nordic.atlas-nodes.0025.7600dd719af435e7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.1dc7a1da3ee63b77.js`](./nordic.atlas-nodes.0026.1dc7a1da3ee63b77.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.7625e2d23a997cbe.js`](./nordic.atlas-nodes.0027.7625e2d23a997cbe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.4a1055165873cdf5.js`](./nordic.atlas-nodes.0028.4a1055165873cdf5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.55ffb036e5b62f53.js`](./nordic.atlas-nodes.0029.55ffb036e5b62f53.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.2ff2464e8037cf41.js`](./nordic.atlas-nodes.0030.2ff2464e8037cf41.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.061bd07a45109d06.js`](./nordic.atlas-nodes.0031.061bd07a45109d06.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.872c5335188f1af5.js`](./nordic.atlas-nodes.0032.872c5335188f1af5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.8029b4920d7b3262.js`](./nordic.atlas-nodes.0033.8029b4920d7b3262.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.5efded008de842a4.js`](./nordic.atlas-nodes.0034.5efded008de842a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.074091cecb06f5e7.js`](./nordic.atlas-nodes.0035.074091cecb06f5e7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.623ee7c3ddab6034.js`](./nordic.atlas-nodes.0036.623ee7c3ddab6034.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.c28efa841781900f.js`](./nordic.atlas-nodes.0037.c28efa841781900f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.bd1f0a77bdac56b5.js`](./nordic.atlas-nodes.0038.bd1f0a77bdac56b5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.f73a83ad2fd8342d.js`](./nordic.atlas-nodes.0039.f73a83ad2fd8342d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.0817501affdfd1ee.js`](./nordic.atlas-nodes.0040.0817501affdfd1ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.da722b7ff09c6973.js`](./nordic.atlas-nodes.0041.da722b7ff09c6973.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.b629fa1fcd814f39.js`](./nordic.atlas-nodes.0042.b629fa1fcd814f39.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.c11c005e17982611.js`](./nordic.atlas-nodes.0043.c11c005e17982611.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.d02878676d2a32d4.js`](./nordic.atlas-nodes.0044.d02878676d2a32d4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.bec3c266acd41808.js`](./nordic.atlas-nodes.0045.bec3c266acd41808.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.f205e33b57cf98e2.js`](./nordic.atlas-nodes.0046.f205e33b57cf98e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.ebfeb060f9781712.js`](./nordic.atlas-nodes.0047.ebfeb060f9781712.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.9de5e030fdda4b79.js`](./nordic.atlas-nodes.0048.9de5e030fdda4b79.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.e77122b743c28ae0.js`](./nordic.atlas-nodes.0049.e77122b743c28ae0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.4160a536d71a99a5.js`](./nordic.atlas-nodes.0050.4160a536d71a99a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.83293c9d3ff7916c.js`](./nordic.atlas-nodes.0051.83293c9d3ff7916c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.f0075aa8d88e165a.js`](./nordic.atlas-nodes.0052.f0075aa8d88e165a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.53cb0193411ae6ee.js`](./nordic.atlas-nodes.0053.53cb0193411ae6ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.4ffab6dcc79d0b87.js`](./nordic.atlas-nodes.0054.4ffab6dcc79d0b87.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.341614b85497004b.js`](./nordic.atlas-nodes.0055.341614b85497004b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.2805909db34d5b65.js`](./nordic.atlas-nodes.0056.2805909db34d5b65.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.0a80a38273f38af2.js`](./nordic.atlas-nodes.0057.0a80a38273f38af2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.add51dffb769a7ae.js`](./nordic.atlas-nodes.0058.add51dffb769a7ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.24ca12f640d4d4ab.js`](./nordic.atlas-nodes.0059.24ca12f640d4d4ab.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.a1d4ca1cfb702c3b.js`](./nordic.atlas-nodes.0060.a1d4ca1cfb702c3b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.ee9a35765905dea4.js`](./nordic.atlas-nodes.0061.ee9a35765905dea4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.82d2475b37a7e9b3.js`](./nordic.atlas-nodes.0062.82d2475b37a7e9b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.6a12099df1f337eb.js`](./nordic.atlas-nodes.0063.6a12099df1f337eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.c5902c07ee997f62.js`](./nordic.atlas-nodes.0064.c5902c07ee997f62.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.af861137987b289e.js`](./nordic.atlas-nodes.0065.af861137987b289e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.a6fb7f5193678cb8.js`](./nordic.atlas-nodes.0066.a6fb7f5193678cb8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.5fb98025f3a7d03d.js`](./nordic.atlas-nodes.0067.5fb98025f3a7d03d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.08a727f6a682e7d4.js`](./nordic.atlas-nodes.0068.08a727f6a682e7d4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.20ab53d0e1bd7dcd.js`](./nordic.atlas-nodes.0069.20ab53d0e1bd7dcd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.dd0011b0650f656c.js`](./nordic.atlas-nodes.0070.dd0011b0650f656c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.5d29a2d1f8c02328.js`](./nordic.atlas-nodes.0071.5d29a2d1f8c02328.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.db7417167af62145.js`](./nordic.atlas-nodes.0072.db7417167af62145.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.27b3a10f84f5203d.js`](./nordic.atlas-nodes.0073.27b3a10f84f5203d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.96a6d157f2610cdb.js`](./nordic.atlas-nodes.0074.96a6d157f2610cdb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.fbfc568d416d6375.js`](./nordic.atlas-nodes.0075.fbfc568d416d6375.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.4c13404fe9b22652.js`](./nordic.atlas-nodes.0076.4c13404fe9b22652.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.d50524bdef08f551.js`](./nordic.atlas-nodes.0077.d50524bdef08f551.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.4362f64adeb4187b.js`](./nordic.atlas-nodes.0078.4362f64adeb4187b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.8c47906e3e752e3b.js`](./nordic.atlas-nodes.0079.8c47906e3e752e3b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.8536fb5b621224a4.js`](./nordic.atlas-nodes.0080.8536fb5b621224a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.8fe046bd22e52a74.js`](./nordic.atlas-nodes.0081.8fe046bd22e52a74.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.f00c8db6b6497aa2.js`](./nordic.atlas-nodes.0082.f00c8db6b6497aa2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.bb98b5a792ac01c3.js`](./nordic.atlas-nodes.0083.bb98b5a792ac01c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.e3f534ea6fbae723.js`](./nordic.atlas-nodes.0084.e3f534ea6fbae723.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.b230d2731c6b6469.js`](./nordic.atlas-nodes.0085.b230d2731c6b6469.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.a7ec041eb75a6f7d.js`](./nordic.atlas-nodes.0086.a7ec041eb75a6f7d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.89f0aadbb2287615.js`](./nordic.atlas-nodes.0087.89f0aadbb2287615.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.aab1d9aab055f6ec.js`](./nordic.atlas-nodes.0088.aab1d9aab055f6ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.9c3e70cfc1fe1b2d.js`](./nordic.atlas-nodes.0089.9c3e70cfc1fe1b2d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.0d5c90096bf1e784.js`](./nordic.atlas-nodes.0090.0d5c90096bf1e784.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.40db05830e800610.js`](./nordic.atlas-nodes.0091.40db05830e800610.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.e9f1a79ebc1d0cda.js`](./nordic.atlas-nodes.0092.e9f1a79ebc1d0cda.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.d7853ddff16c4592.js`](./nordic.atlas-nodes.0093.d7853ddff16c4592.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.c16bd0cf617ecc88.js`](./nordic.atlas-nodes.0094.c16bd0cf617ecc88.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.50058c1a6e33a709.js`](./nordic.atlas-nodes.0095.50058c1a6e33a709.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.1ce1e16405361c47.js`](./nordic.atlas-nodes.0096.1ce1e16405361c47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.d5d29a1594110701.js`](./nordic.atlas-nodes.0097.d5d29a1594110701.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.5e74fcae5e456c69.js`](./nordic.atlas-nodes.0098.5e74fcae5e456c69.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.b4d8d1f84e4a2937.js`](./nordic.atlas-nodes.0099.b4d8d1f84e4a2937.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.712bf6d15422b27b.js`](./nordic.atlas-nodes.0100.712bf6d15422b27b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.85d224939f5ec78c.js`](./nordic.atlas-nodes.0101.85d224939f5ec78c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.850772a726b5746b.js`](./nordic.atlas-nodes.0102.850772a726b5746b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.78e1c60e55f1eeb0.js`](./nordic.atlas-nodes.0103.78e1c60e55f1eeb0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.952a9087269de997.js`](./nordic.atlas-nodes.0104.952a9087269de997.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.90af760675c80789.js`](./nordic.atlas-nodes.0105.90af760675c80789.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.4a588b03deddc89e.js`](./nordic.atlas-nodes.0106.4a588b03deddc89e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.87913df145f7a04b.js`](./nordic.atlas-nodes.0107.87913df145f7a04b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.cf3b7c69d4b3b6c3.js`](./nordic.atlas-nodes.0108.cf3b7c69d4b3b6c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.ccd668a23778254f.js`](./nordic.atlas-nodes.0109.ccd668a23778254f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.e131b7df9c1ea42e.js`](./nordic.atlas-nodes.0110.e131b7df9c1ea42e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.f9e25293dac64a5a.js`](./nordic.atlas-nodes.0111.f9e25293dac64a5a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.081916d6698f5f43.js`](./nordic.atlas-nodes.0112.081916d6698f5f43.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.59bd6cff32289456.js`](./nordic.atlas-nodes.0113.59bd6cff32289456.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.fe3ccbef577f5714.js`](./nordic.atlas-nodes.0114.fe3ccbef577f5714.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.7a8d8e1a4229213e.js`](./nordic.atlas-nodes.0115.7a8d8e1a4229213e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.681ad5a2e4505f26.js`](./nordic.atlas-nodes.0116.681ad5a2e4505f26.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.b9b0a9535c3eedc8.js`](./nordic.atlas-nodes.0117.b9b0a9535c3eedc8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.fb0033cfcec28c2c.js`](./nordic.atlas-nodes.0118.fb0033cfcec28c2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.77e589e5891eadd3.js`](./nordic.atlas-nodes.0119.77e589e5891eadd3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.c2d8caa16ccb848d.js`](./nordic.atlas-nodes.0120.c2d8caa16ccb848d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.4e9159cc68a8e983.js`](./nordic.atlas-nodes.0121.4e9159cc68a8e983.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.de6e97e2c2c9e6de.js`](./nordic.atlas-nodes.0122.de6e97e2c2c9e6de.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.fb7241020cc40b89.js`](./nordic.atlas-nodes.0123.fb7241020cc40b89.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.f2cc010d66e969d5.js`](./nordic.atlas-nodes.0124.f2cc010d66e969d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.d7b8aa9a0d24c8d7.js`](./nordic.atlas-nodes.0125.d7b8aa9a0d24c8d7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.f46186c051be2446.js`](./nordic.atlas-nodes.0126.f46186c051be2446.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.24ad405bd32c325a.js`](./nordic.atlas-nodes.0127.24ad405bd32c325a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.eb3a79cc0105ddfa.js`](./nordic.atlas-nodes.0128.eb3a79cc0105ddfa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.dda6bbafe2987c8d.js`](./nordic.atlas-nodes.0129.dda6bbafe2987c8d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.d091839ace4e4f86.js`](./nordic.atlas-nodes.0130.d091839ace4e4f86.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.9ec56b13c6019aad.js`](./nordic.atlas-nodes.0131.9ec56b13c6019aad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.60ed87beaeb62330.js`](./nordic.atlas-nodes.0132.60ed87beaeb62330.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.05b1b477510f6024.js`](./nordic.atlas-nodes.0133.05b1b477510f6024.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.28ce268f02333ce7.js`](./nordic.atlas-nodes.0134.28ce268f02333ce7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.ce6a46112b5ddbdc.js`](./nordic.atlas-nodes.0135.ce6a46112b5ddbdc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.85dfebd12cb95c7b.js`](./nordic.atlas-nodes.0136.85dfebd12cb95c7b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.0da895af01d66f34.js`](./nordic.atlas-nodes.0137.0da895af01d66f34.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.77678b34063a647f.js`](./nordic.atlas-nodes.0138.77678b34063a647f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.74fdbe2fab22da42.js`](./nordic.atlas-nodes.0139.74fdbe2fab22da42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.9c3e15d462bafbd9.js`](./nordic.atlas-nodes.0140.9c3e15d462bafbd9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.d64c9c240322a701.js`](./nordic.atlas-nodes.0141.d64c9c240322a701.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.74b216d5202bf942.js`](./nordic.atlas-nodes.0142.74b216d5202bf942.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.85d3f97886f148f7.js`](./nordic.atlas-nodes.0143.85d3f97886f148f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.805e528bf19ba61e.js`](./nordic.atlas-nodes.0144.805e528bf19ba61e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.b4d52cd80be4c36d.js`](./nordic.atlas-nodes.0145.b4d52cd80be4c36d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.34afe8992ebb8bc2.js`](./nordic.atlas-nodes.0146.34afe8992ebb8bc2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.e82032265a52b3e0.js`](./nordic.atlas-nodes.0147.e82032265a52b3e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.67752eb80b0c07af.js`](./nordic.atlas-nodes.0148.67752eb80b0c07af.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.17cc3cd406d3f7e2.js`](./nordic.atlas-nodes.0149.17cc3cd406d3f7e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.271e39b32d437224.js`](./nordic.atlas-nodes.0150.271e39b32d437224.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.647bf3296d63a605.js`](./nordic.atlas-nodes.0151.647bf3296d63a605.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.3b4b06df4f63ae49.js`](./nordic.atlas-nodes.0152.3b4b06df4f63ae49.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.86d7c74b7c61f1a5.js`](./nordic.atlas-nodes.0153.86d7c74b7c61f1a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.26a1795b6d5f6b41.js`](./nordic.atlas-nodes.0154.26a1795b6d5f6b41.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.27850f97672ce8a5.js`](./nordic.atlas-nodes.0155.27850f97672ce8a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.66cabd795e90bd79.js`](./nordic.atlas-nodes.0156.66cabd795e90bd79.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.18ac66d88e116821.js`](./nordic.atlas-nodes.0157.18ac66d88e116821.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.aa064580fb3bb242.js`](./nordic.atlas-nodes.0158.aa064580fb3bb242.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.28d5b241ba9394bb.js`](./nordic.atlas-nodes.0159.28d5b241ba9394bb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.48b638692fc3cb51.js`](./nordic.atlas-nodes.0160.48b638692fc3cb51.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.7a7f013eac712e6b.js`](./nordic.atlas-nodes.0161.7a7f013eac712e6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.f7d41a2b12f1e533.js`](./nordic.atlas-nodes.0162.f7d41a2b12f1e533.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.7bd3e9142bb4dc55.js`](./nordic.atlas-nodes.0163.7bd3e9142bb4dc55.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.180de3a5c4c4c0c1.js`](./nordic.atlas-nodes.0164.180de3a5c4c4c0c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.259cded89d560cf0.js`](./nordic.atlas-nodes.0165.259cded89d560cf0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.ab88457c018ff562.js`](./nordic.atlas-nodes.0166.ab88457c018ff562.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.168275548a3c7384.js`](./nordic.atlas-nodes.0167.168275548a3c7384.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.7f35fadf5b5488bb.js`](./nordic.atlas-nodes.0168.7f35fadf5b5488bb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.5f3ece6bae17b5ea.js`](./nordic.atlas-nodes.0169.5f3ece6bae17b5ea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.22c45ef423b81f72.js`](./nordic.atlas-nodes.0170.22c45ef423b81f72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0171.8ec343f935b4fa1f.js`](./nordic.atlas-nodes.0171.8ec343f935b4fa1f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0172.a030442075107e80.js`](./nordic.atlas-nodes.0172.a030442075107e80.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.1fd49588884c2a07.js`](./nordic.atlas-details.0173.1fd49588884c2a07.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.3a2b974ddf3a5254.js`](./nordic.atlas-details.0174.3a2b974ddf3a5254.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.56507dcd412df22e.js`](./nordic.atlas-details.0175.56507dcd412df22e.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.367d4c48f29722ca.js`](./nordic.atlas-details.0176.367d4c48f29722ca.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.3fd222aa9598c539.js`](./nordic.atlas-details.0177.3fd222aa9598c539.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.0a747e6e95b9d476.js`](./nordic.atlas-details.0178.0a747e6e95b9d476.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.5761367cd06db53d.js`](./nordic.atlas-details.0179.5761367cd06db53d.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.1487c14db939c9a8.js`](./nordic.atlas-details.0180.1487c14db939c9a8.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.a4a7cfb6fcc04ab9.js`](./nordic.atlas-details.0181.a4a7cfb6fcc04ab9.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.e2996b4dd9fc7c77.js`](./nordic.atlas-details.0182.e2996b4dd9fc7c77.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.1ab8c81603c96270.js`](./nordic.atlas-details.0183.1ab8c81603c96270.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.86bd34e66d29bb76.js`](./nordic.atlas-details.0184.86bd34e66d29bb76.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.7639c701abf798fd.js`](./nordic.atlas-details.0185.7639c701abf798fd.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.22d43076ae924b4a.js`](./nordic.atlas-details.0186.22d43076ae924b4a.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.411580aa15e03cc1.js`](./nordic.atlas-details.0187.411580aa15e03cc1.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.15f76a392a71a847.js`](./nordic.atlas-details.0188.15f76a392a71a847.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.92bfed26bf06fca4.js`](./nordic.atlas-details.0189.92bfed26bf06fca4.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.0a27f46028226085.js`](./nordic.atlas-details.0190.0a27f46028226085.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.1f7cb6511a10fbd3.js`](./nordic.atlas-details.0191.1f7cb6511a10fbd3.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.7efb3ef36d002864.js`](./nordic.atlas-details.0192.7efb3ef36d002864.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.2b9d0500e592b887.js`](./nordic.atlas-details.0193.2b9d0500e592b887.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.79ee15bb1205bfb1.js`](./nordic.atlas-details.0194.79ee15bb1205bfb1.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.8c8a855fa90f4823.js`](./nordic.atlas-details.0195.8c8a855fa90f4823.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.60f5806ccdd5703c.js`](./nordic.atlas-details.0196.60f5806ccdd5703c.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.04d14f28cba3ed6b.js`](./nordic.atlas-details.0197.04d14f28cba3ed6b.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.fa6d3f1d15fdbc07.js`](./nordic.atlas-details.0198.fa6d3f1d15fdbc07.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.d8454ea834e88e5a.js`](./nordic.atlas-details.0199.d8454ea834e88e5a.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.bf635ca9b3afca6c.js`](./nordic.atlas-details.0200.bf635ca9b3afca6c.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.e4cb55747df5d48d.js`](./nordic.atlas-details.0201.e4cb55747df5d48d.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.e1e5698b518e6941.js`](./nordic.atlas-details.0202.e1e5698b518e6941.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.7df874ed91e9e7d2.js`](./nordic.atlas-details.0203.7df874ed91e9e7d2.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.92c25e0e6bc61fa3.js`](./nordic.atlas-details.0204.92c25e0e6bc61fa3.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.070b6004940ab8bf.js`](./nordic.atlas-details.0205.070b6004940ab8bf.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.9b82f83c85a0824c.js`](./nordic.atlas-details.0206.9b82f83c85a0824c.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.39e3a74112ead892.js`](./nordic.atlas-details.0207.39e3a74112ead892.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.cc2da1bc560c1251.js`](./nordic.atlas-details.0208.cc2da1bc560c1251.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.d218564ae29c7fc6.js`](./nordic.atlas-details.0209.d218564ae29c7fc6.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.195ee3161a9bb791.js`](./nordic.atlas-details.0210.195ee3161a9bb791.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.a8cc0fb86ffc8a42.js`](./nordic.atlas-details.0211.a8cc0fb86ffc8a42.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.dc4023b30d6ae84a.js`](./nordic.atlas-details.0212.dc4023b30d6ae84a.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.a774b29996df1be1.js`](./nordic.atlas-details.0213.a774b29996df1be1.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.c8cd9ae53f982530.js`](./nordic.atlas-details.0214.c8cd9ae53f982530.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.ff6479c087a07d4f.js`](./nordic.atlas-details.0215.ff6479c087a07d4f.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.0faf50aafb052741.js`](./nordic.atlas-details.0216.0faf50aafb052741.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.a14e241b7c013ba4.js`](./nordic.atlas-details.0217.a14e241b7c013ba4.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.c2265a643682e319.js`](./nordic.atlas-details.0218.c2265a643682e319.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.597f0ccb36a77964.js`](./nordic.atlas-details.0219.597f0ccb36a77964.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.6a117c64e35b406b.js`](./nordic.atlas-details.0220.6a117c64e35b406b.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.7af066cd57d734ac.js`](./nordic.atlas-details.0221.7af066cd57d734ac.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.3da1c77cc15d7212.js`](./nordic.atlas-details.0222.3da1c77cc15d7212.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.3d2b94182c9c3477.js`](./nordic.atlas-details.0223.3d2b94182c9c3477.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.5adc4e28456316c8.js`](./nordic.atlas-details.0224.5adc4e28456316c8.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.113f090ea322b844.js`](./nordic.atlas-details.0225.113f090ea322b844.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.cdaa66b7a5e953b8.js`](./nordic.atlas-details.0226.cdaa66b7a5e953b8.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.bf2ef67e616f4daf.js`](./nordic.atlas-details.0227.bf2ef67e616f4daf.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.5b80b5b8aeda6e41.js`](./nordic.atlas-details.0228.5b80b5b8aeda6e41.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.16d8548b6e500444.js`](./nordic.atlas-details.0229.16d8548b6e500444.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.6a81e3e6477c871e.js`](./nordic.atlas-details.0230.6a81e3e6477c871e.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.def3ce8a4c139941.js`](./nordic.atlas-details.0231.def3ce8a4c139941.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.ee2021f717cc8113.js`](./nordic.atlas-details.0232.ee2021f717cc8113.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.cf00b88188079d77.js`](./nordic.atlas-details.0233.cf00b88188079d77.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.13e0c27a6146e031.js`](./nordic.atlas-details.0234.13e0c27a6146e031.js)
- Static atlas data chunk: [`nordic.atlas-details.0235.347d4f1325439300.js`](./nordic.atlas-details.0235.347d4f1325439300.js)
- Static atlas data chunk: [`nordic.atlas-details.0236.9cb74ac93fd231d9.js`](./nordic.atlas-details.0236.9cb74ac93fd231d9.js)
- Static atlas data chunk: [`nordic.atlas-edges.0237.4b13d21b01dba001.js`](./nordic.atlas-edges.0237.4b13d21b01dba001.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0238.687cbebe0d7a66a7.js`](./nordic.atlas-sequences.0238.687cbebe0d7a66a7.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0239.30ba693aa210c990.js`](./nordic.atlas-indexes.0239.30ba693aa210c990.js)
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

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
| AADR-v66 aDNA samples | `shared_world_scale_layer` | Country assignment follows the AADR political entity field. | `1231` |
| Fieldwork documentation | `scope_specific_overlay` | Observed sampling location documented on 2026-02-26 at Lyngsjön Lake. | `1` |
| LandClim pollen sites | `scope_specific_overlay` | Pollen sequences staged from the LandClim normalization bundle. | `490` |
| Neotoma pollen sites | `scope_specific_overlay` | Pollen and paleoecology sites staged from the Neotoma normalization bundle. | `193` |
| SEAD sites | `scope_specific_overlay` | Environmental archaeology sites staged from the SEAD normalization bundle. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `9727` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Cattle source-sample chronology | `shared_world_scale_layer` |  | `5` |
| Goat source-sample chronology | `shared_world_scale_layer` |  | `0` |
| Horse source-sample chronology | `shared_world_scale_layer` |  | `3` |
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


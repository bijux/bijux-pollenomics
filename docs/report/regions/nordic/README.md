# Nordic Evidence Surface

This shared interactive map bundle was generated on `2026-09-06` from Homo
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
- Animal locality GeoJSON: [`nordic_animal_localities.geojson`](./nordic_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`nordic_domesticated_animal_localities.geojson`](./nordic_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`nordic_comparator_animal_localities.geojson`](./nordic_comparator_animal_localities.geojson)
- Wild and progenitor animal locality GeoJSON: [`nordic_progenitor_animal_localities.geojson`](./nordic_progenitor_animal_localities.geojson)
- Animal atlas evidence CSV: [`nordic_animal_atlas_evidence.csv`](./nordic_animal_atlas_evidence.csv)
- Animal atlas evidence JSON: [`nordic_animal_atlas_evidence.json`](./nordic_animal_atlas_evidence.json)
- Animal point traceability JSON: [`nordic_animal_point_traceability.json`](./nordic_animal_point_traceability.json)
- Static atlas bootstrap manifest: [`nordic_map_assets.json`](./nordic_map_assets.json)
- Static atlas data chunk: [`nordic.atlas-provenance.0000.d2b0ba02f6d96325.js`](./nordic.atlas-provenance.0000.d2b0ba02f6d96325.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.ec19d720f0cdc154.js`](./nordic.atlas-nodes.0001.ec19d720f0cdc154.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.d1eb1dabcb4cdca9.js`](./nordic.atlas-nodes.0002.d1eb1dabcb4cdca9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.7df66733de7c9958.js`](./nordic.atlas-nodes.0003.7df66733de7c9958.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.40d03fa29a06902a.js`](./nordic.atlas-nodes.0004.40d03fa29a06902a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.02d5239211a855a5.js`](./nordic.atlas-nodes.0005.02d5239211a855a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.a45fa805169bbf71.js`](./nordic.atlas-nodes.0006.a45fa805169bbf71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.9b7ff7825d7fb275.js`](./nordic.atlas-nodes.0007.9b7ff7825d7fb275.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.8dd9d34a4151fabe.js`](./nordic.atlas-nodes.0008.8dd9d34a4151fabe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.af5aad231b9e1408.js`](./nordic.atlas-nodes.0009.af5aad231b9e1408.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.ffbeea16a9b37f4d.js`](./nordic.atlas-nodes.0010.ffbeea16a9b37f4d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.ec3907557d409390.js`](./nordic.atlas-nodes.0011.ec3907557d409390.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.e70743f16836af28.js`](./nordic.atlas-nodes.0012.e70743f16836af28.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.c16ac7fd7d34a806.js`](./nordic.atlas-nodes.0013.c16ac7fd7d34a806.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.3b692d2ec4d42669.js`](./nordic.atlas-nodes.0014.3b692d2ec4d42669.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.0cc5d225d43a091c.js`](./nordic.atlas-nodes.0015.0cc5d225d43a091c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.04dca2f038c12c0d.js`](./nordic.atlas-nodes.0016.04dca2f038c12c0d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.1ff8dc0522f9a025.js`](./nordic.atlas-nodes.0017.1ff8dc0522f9a025.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.46de0763dc30e496.js`](./nordic.atlas-nodes.0018.46de0763dc30e496.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.3b3e5df4ad297e57.js`](./nordic.atlas-nodes.0019.3b3e5df4ad297e57.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.fe54ea3c43a6f125.js`](./nordic.atlas-nodes.0020.fe54ea3c43a6f125.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.8509de1d9d6f480e.js`](./nordic.atlas-nodes.0021.8509de1d9d6f480e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.afae2be5aa41ad6d.js`](./nordic.atlas-nodes.0022.afae2be5aa41ad6d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.4dfeb4102239e501.js`](./nordic.atlas-nodes.0023.4dfeb4102239e501.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.f7f7ee00d028518d.js`](./nordic.atlas-nodes.0024.f7f7ee00d028518d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.8393db53f2f9e42f.js`](./nordic.atlas-nodes.0025.8393db53f2f9e42f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.8684edf398886107.js`](./nordic.atlas-nodes.0026.8684edf398886107.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.e6395465c5a3c6db.js`](./nordic.atlas-nodes.0027.e6395465c5a3c6db.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.b0b16503d1dcb69b.js`](./nordic.atlas-nodes.0028.b0b16503d1dcb69b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.a780e68ba59c1436.js`](./nordic.atlas-nodes.0029.a780e68ba59c1436.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.523671a44754aa93.js`](./nordic.atlas-nodes.0030.523671a44754aa93.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.38996740e1ef4245.js`](./nordic.atlas-nodes.0031.38996740e1ef4245.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.6411e0bcb3c07720.js`](./nordic.atlas-nodes.0032.6411e0bcb3c07720.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.0336edc23a80da3f.js`](./nordic.atlas-nodes.0033.0336edc23a80da3f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.e2737303676c1c3d.js`](./nordic.atlas-nodes.0034.e2737303676c1c3d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.b8008e2238b85b31.js`](./nordic.atlas-nodes.0035.b8008e2238b85b31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.76f009ab68ab7a40.js`](./nordic.atlas-nodes.0036.76f009ab68ab7a40.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.8867799086215f0f.js`](./nordic.atlas-nodes.0037.8867799086215f0f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.4b43d895073c4288.js`](./nordic.atlas-nodes.0038.4b43d895073c4288.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.81b6c93e5e629590.js`](./nordic.atlas-nodes.0039.81b6c93e5e629590.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.c5e8f32485634120.js`](./nordic.atlas-nodes.0040.c5e8f32485634120.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.f80e09a2c8982a5c.js`](./nordic.atlas-nodes.0041.f80e09a2c8982a5c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.779d52b63f2f9efa.js`](./nordic.atlas-nodes.0042.779d52b63f2f9efa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.19dd08dcd6cdfa94.js`](./nordic.atlas-nodes.0043.19dd08dcd6cdfa94.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.95823745b258cb19.js`](./nordic.atlas-nodes.0044.95823745b258cb19.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.8b8f0f4e8abcf978.js`](./nordic.atlas-nodes.0045.8b8f0f4e8abcf978.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.7f8410626c03398d.js`](./nordic.atlas-nodes.0046.7f8410626c03398d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.e60584b969964413.js`](./nordic.atlas-nodes.0047.e60584b969964413.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.16605aa46428a141.js`](./nordic.atlas-nodes.0048.16605aa46428a141.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.dca2989539a91eb4.js`](./nordic.atlas-nodes.0049.dca2989539a91eb4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.60ecd8ab7c457a59.js`](./nordic.atlas-nodes.0050.60ecd8ab7c457a59.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.0e0db0a351249260.js`](./nordic.atlas-nodes.0051.0e0db0a351249260.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.272d117395619bf2.js`](./nordic.atlas-nodes.0052.272d117395619bf2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.f84865165ebab399.js`](./nordic.atlas-nodes.0053.f84865165ebab399.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.8987161870030975.js`](./nordic.atlas-nodes.0054.8987161870030975.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.fee533365a6a3556.js`](./nordic.atlas-nodes.0055.fee533365a6a3556.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.e717eab834f32081.js`](./nordic.atlas-nodes.0056.e717eab834f32081.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.7a3553b215d71a17.js`](./nordic.atlas-nodes.0057.7a3553b215d71a17.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.584012c3e0f3b764.js`](./nordic.atlas-nodes.0058.584012c3e0f3b764.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.ca157802f9283c81.js`](./nordic.atlas-nodes.0059.ca157802f9283c81.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.7ed4825a5a812a88.js`](./nordic.atlas-nodes.0060.7ed4825a5a812a88.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.5845a5f370da321d.js`](./nordic.atlas-nodes.0061.5845a5f370da321d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.5d63b0a86aca64a3.js`](./nordic.atlas-nodes.0062.5d63b0a86aca64a3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.78e8af8c9fa9df84.js`](./nordic.atlas-nodes.0063.78e8af8c9fa9df84.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.39d72d931b75e492.js`](./nordic.atlas-nodes.0064.39d72d931b75e492.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.09c4794511128f3e.js`](./nordic.atlas-nodes.0065.09c4794511128f3e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.c51a1222d9069b3c.js`](./nordic.atlas-nodes.0066.c51a1222d9069b3c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.c871db99b87a15be.js`](./nordic.atlas-nodes.0067.c871db99b87a15be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.f300d9350f70a5eb.js`](./nordic.atlas-nodes.0068.f300d9350f70a5eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.d88bf408d3153005.js`](./nordic.atlas-nodes.0069.d88bf408d3153005.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.6f6883131b65086b.js`](./nordic.atlas-nodes.0070.6f6883131b65086b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.63c6f83c94557a5e.js`](./nordic.atlas-nodes.0071.63c6f83c94557a5e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.c143e282f21dc0f8.js`](./nordic.atlas-nodes.0072.c143e282f21dc0f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.17c7e7382ffc7b04.js`](./nordic.atlas-nodes.0073.17c7e7382ffc7b04.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.ee0bbff39da617f5.js`](./nordic.atlas-nodes.0074.ee0bbff39da617f5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.b6017d38516d3ef0.js`](./nordic.atlas-nodes.0075.b6017d38516d3ef0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.15bbc2c9f9db5b3a.js`](./nordic.atlas-nodes.0076.15bbc2c9f9db5b3a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.4f331980f774ee35.js`](./nordic.atlas-nodes.0077.4f331980f774ee35.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.7961b608ba68a544.js`](./nordic.atlas-nodes.0078.7961b608ba68a544.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.fabff34d5b9c611f.js`](./nordic.atlas-nodes.0079.fabff34d5b9c611f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.9d41f8d5caee8afc.js`](./nordic.atlas-nodes.0080.9d41f8d5caee8afc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.475c01f9ba29f444.js`](./nordic.atlas-nodes.0081.475c01f9ba29f444.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.2b21451b91b3f359.js`](./nordic.atlas-nodes.0082.2b21451b91b3f359.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.0ccfb645615c4f8f.js`](./nordic.atlas-nodes.0083.0ccfb645615c4f8f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.71446587a80c7e2b.js`](./nordic.atlas-nodes.0084.71446587a80c7e2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.17d62c1e315ac5ae.js`](./nordic.atlas-nodes.0085.17d62c1e315ac5ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.9d2684b840b38265.js`](./nordic.atlas-nodes.0086.9d2684b840b38265.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.264ea8d8d30a5fa3.js`](./nordic.atlas-nodes.0087.264ea8d8d30a5fa3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.f268d97f5d1e5bdb.js`](./nordic.atlas-nodes.0088.f268d97f5d1e5bdb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.f575532eee953052.js`](./nordic.atlas-nodes.0089.f575532eee953052.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.573c9fc397209cd9.js`](./nordic.atlas-nodes.0090.573c9fc397209cd9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.a1f5424754a583ec.js`](./nordic.atlas-nodes.0091.a1f5424754a583ec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.89c6a08faa032851.js`](./nordic.atlas-nodes.0092.89c6a08faa032851.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.fd23b06e7d5b89ac.js`](./nordic.atlas-nodes.0093.fd23b06e7d5b89ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.2997e3f11538e5b9.js`](./nordic.atlas-nodes.0094.2997e3f11538e5b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.1dd190d454b4cf23.js`](./nordic.atlas-nodes.0095.1dd190d454b4cf23.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.7a07ac8ef088569f.js`](./nordic.atlas-nodes.0096.7a07ac8ef088569f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.beaafdd40d1b3980.js`](./nordic.atlas-nodes.0097.beaafdd40d1b3980.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.667ce1e3c3431571.js`](./nordic.atlas-nodes.0098.667ce1e3c3431571.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.0822c169b426ade5.js`](./nordic.atlas-nodes.0099.0822c169b426ade5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.522035d9b4a4d772.js`](./nordic.atlas-nodes.0100.522035d9b4a4d772.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.9c12c56aadb06ae4.js`](./nordic.atlas-nodes.0101.9c12c56aadb06ae4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.61b34eaaea8f0e18.js`](./nordic.atlas-nodes.0102.61b34eaaea8f0e18.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.087644c623bbe3ae.js`](./nordic.atlas-nodes.0103.087644c623bbe3ae.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.6e4cf7616fc32295.js`](./nordic.atlas-nodes.0104.6e4cf7616fc32295.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.a4e1cde800cc8ca2.js`](./nordic.atlas-nodes.0105.a4e1cde800cc8ca2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.ed10a2e0041be775.js`](./nordic.atlas-nodes.0106.ed10a2e0041be775.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.9c9489e9f2830230.js`](./nordic.atlas-nodes.0107.9c9489e9f2830230.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.c44eb45b771ae85c.js`](./nordic.atlas-nodes.0108.c44eb45b771ae85c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.5a6597311707a2e8.js`](./nordic.atlas-nodes.0109.5a6597311707a2e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.f24ffc38e0e17ab2.js`](./nordic.atlas-nodes.0110.f24ffc38e0e17ab2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.ab8e6e05b883ef89.js`](./nordic.atlas-nodes.0111.ab8e6e05b883ef89.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.c810819a1c4b6728.js`](./nordic.atlas-nodes.0112.c810819a1c4b6728.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.ae79a415fb8cb796.js`](./nordic.atlas-nodes.0113.ae79a415fb8cb796.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.f79b1e7335e992ab.js`](./nordic.atlas-nodes.0114.f79b1e7335e992ab.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.c8d5cde67455aeb9.js`](./nordic.atlas-nodes.0115.c8d5cde67455aeb9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.eb8cce0fe4252165.js`](./nordic.atlas-nodes.0116.eb8cce0fe4252165.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.2b6f44db41b17cfe.js`](./nordic.atlas-nodes.0117.2b6f44db41b17cfe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.a44cc7c6086b9c80.js`](./nordic.atlas-nodes.0118.a44cc7c6086b9c80.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.27e30a7acdc216ac.js`](./nordic.atlas-nodes.0119.27e30a7acdc216ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.51b548598e47992a.js`](./nordic.atlas-nodes.0120.51b548598e47992a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.8bb6c0731987baac.js`](./nordic.atlas-nodes.0121.8bb6c0731987baac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.16928609d88c368d.js`](./nordic.atlas-nodes.0122.16928609d88c368d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.51c9d5c0327c9361.js`](./nordic.atlas-nodes.0123.51c9d5c0327c9361.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.e70192e5a9ace1d2.js`](./nordic.atlas-nodes.0124.e70192e5a9ace1d2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.db21452555407dee.js`](./nordic.atlas-nodes.0125.db21452555407dee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.edabd5a9541cb4bf.js`](./nordic.atlas-nodes.0126.edabd5a9541cb4bf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.ce6826b969b2f641.js`](./nordic.atlas-nodes.0127.ce6826b969b2f641.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.9bbf40d60193dda9.js`](./nordic.atlas-nodes.0128.9bbf40d60193dda9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.dbba1d9e4baf41a2.js`](./nordic.atlas-nodes.0129.dbba1d9e4baf41a2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.9b2724195e02f3e0.js`](./nordic.atlas-nodes.0130.9b2724195e02f3e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.6c8ba4d750b8a360.js`](./nordic.atlas-nodes.0131.6c8ba4d750b8a360.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.4f8da0cdf208aaba.js`](./nordic.atlas-nodes.0132.4f8da0cdf208aaba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.3e981c16e6bd0b29.js`](./nordic.atlas-nodes.0133.3e981c16e6bd0b29.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.3f2484a1d7e7da64.js`](./nordic.atlas-nodes.0134.3f2484a1d7e7da64.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.44a07d19151ef72f.js`](./nordic.atlas-nodes.0135.44a07d19151ef72f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.597f0bae50d65b42.js`](./nordic.atlas-nodes.0136.597f0bae50d65b42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.2bcdc3c76a9a5087.js`](./nordic.atlas-nodes.0137.2bcdc3c76a9a5087.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.be56da8897e53938.js`](./nordic.atlas-nodes.0138.be56da8897e53938.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.233470da1e934e3e.js`](./nordic.atlas-nodes.0139.233470da1e934e3e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.949ce4c8275c644c.js`](./nordic.atlas-nodes.0140.949ce4c8275c644c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.b30ff04de6adc4c3.js`](./nordic.atlas-nodes.0141.b30ff04de6adc4c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.5294ba1a2dfb03a9.js`](./nordic.atlas-nodes.0142.5294ba1a2dfb03a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.efdf9183af0808f8.js`](./nordic.atlas-nodes.0143.efdf9183af0808f8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.c9997f85abfff491.js`](./nordic.atlas-nodes.0144.c9997f85abfff491.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.c09f2e9a0e9d0f51.js`](./nordic.atlas-nodes.0145.c09f2e9a0e9d0f51.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.81a69f4fca11e2f4.js`](./nordic.atlas-nodes.0146.81a69f4fca11e2f4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.7fd051ebfa680248.js`](./nordic.atlas-nodes.0147.7fd051ebfa680248.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.ec7d8e955d0aa08f.js`](./nordic.atlas-nodes.0148.ec7d8e955d0aa08f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.95eef4cfc82e5c04.js`](./nordic.atlas-nodes.0149.95eef4cfc82e5c04.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.be2d4cabac565b08.js`](./nordic.atlas-nodes.0150.be2d4cabac565b08.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.85ccf930407cfaec.js`](./nordic.atlas-nodes.0151.85ccf930407cfaec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.cda266700a7b71e8.js`](./nordic.atlas-nodes.0152.cda266700a7b71e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.f191542930a5678f.js`](./nordic.atlas-nodes.0153.f191542930a5678f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.144fd8a931ebf326.js`](./nordic.atlas-nodes.0154.144fd8a931ebf326.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.280d68fd577ae011.js`](./nordic.atlas-nodes.0155.280d68fd577ae011.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.95840e66392b03f7.js`](./nordic.atlas-nodes.0156.95840e66392b03f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.25b8e9cac8a3885f.js`](./nordic.atlas-nodes.0157.25b8e9cac8a3885f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.c4a21e63c7850ebe.js`](./nordic.atlas-nodes.0158.c4a21e63c7850ebe.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.f6519c58603992ba.js`](./nordic.atlas-nodes.0159.f6519c58603992ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.7e1daea6b081d6f5.js`](./nordic.atlas-nodes.0160.7e1daea6b081d6f5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.bcba34c6f166e8d6.js`](./nordic.atlas-nodes.0161.bcba34c6f166e8d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.26d1d5c8bac13751.js`](./nordic.atlas-nodes.0162.26d1d5c8bac13751.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.7ed9fce4c89a82f9.js`](./nordic.atlas-nodes.0163.7ed9fce4c89a82f9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.506850174918cd66.js`](./nordic.atlas-nodes.0164.506850174918cd66.js)
- Static atlas data chunk: [`nordic.atlas-details.0165.31dfed40cede63f5.js`](./nordic.atlas-details.0165.31dfed40cede63f5.js)
- Static atlas data chunk: [`nordic.atlas-details.0166.22f44b166a2c00dd.js`](./nordic.atlas-details.0166.22f44b166a2c00dd.js)
- Static atlas data chunk: [`nordic.atlas-details.0167.fdec79af49f0accb.js`](./nordic.atlas-details.0167.fdec79af49f0accb.js)
- Static atlas data chunk: [`nordic.atlas-details.0168.0a5c81120615c540.js`](./nordic.atlas-details.0168.0a5c81120615c540.js)
- Static atlas data chunk: [`nordic.atlas-details.0169.a446bb7ee087ae03.js`](./nordic.atlas-details.0169.a446bb7ee087ae03.js)
- Static atlas data chunk: [`nordic.atlas-details.0170.7efe01d0f0d48603.js`](./nordic.atlas-details.0170.7efe01d0f0d48603.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.95c4e79ca0391a7c.js`](./nordic.atlas-details.0171.95c4e79ca0391a7c.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.5c9f5feec3a9b4cb.js`](./nordic.atlas-details.0172.5c9f5feec3a9b4cb.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.a9597ed7338c4957.js`](./nordic.atlas-details.0173.a9597ed7338c4957.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.a0131e2878e32212.js`](./nordic.atlas-details.0174.a0131e2878e32212.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.781612ff9f09655d.js`](./nordic.atlas-details.0175.781612ff9f09655d.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.40c213cf89bf6b55.js`](./nordic.atlas-details.0176.40c213cf89bf6b55.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.55ba19afacb5c5e1.js`](./nordic.atlas-details.0177.55ba19afacb5c5e1.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.cf81d1d58c4f2912.js`](./nordic.atlas-details.0178.cf81d1d58c4f2912.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.4ad0757d5807fd58.js`](./nordic.atlas-details.0179.4ad0757d5807fd58.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.b36bf6ac905e3a4c.js`](./nordic.atlas-details.0180.b36bf6ac905e3a4c.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.eedf291960320a27.js`](./nordic.atlas-details.0181.eedf291960320a27.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.05583905844da503.js`](./nordic.atlas-details.0182.05583905844da503.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.c469fddb91b69173.js`](./nordic.atlas-details.0183.c469fddb91b69173.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.8572d9bd845ddfbd.js`](./nordic.atlas-details.0184.8572d9bd845ddfbd.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.3f9d9c9fa3e44494.js`](./nordic.atlas-details.0185.3f9d9c9fa3e44494.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.9cbe9eb4f543892d.js`](./nordic.atlas-details.0186.9cbe9eb4f543892d.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.e8860f8b36a2cea8.js`](./nordic.atlas-details.0187.e8860f8b36a2cea8.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.f263015721ebf5ad.js`](./nordic.atlas-details.0188.f263015721ebf5ad.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.3d31254480f607a7.js`](./nordic.atlas-details.0189.3d31254480f607a7.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.fa7fad81b1034457.js`](./nordic.atlas-details.0190.fa7fad81b1034457.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.ca24683b045c02f3.js`](./nordic.atlas-details.0191.ca24683b045c02f3.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.15fd94918fd27d56.js`](./nordic.atlas-details.0192.15fd94918fd27d56.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.0195d82435577f2a.js`](./nordic.atlas-details.0193.0195d82435577f2a.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.78de0500ab0645ab.js`](./nordic.atlas-details.0194.78de0500ab0645ab.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.fa97ac2b88a99a5b.js`](./nordic.atlas-details.0195.fa97ac2b88a99a5b.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.3472df4656d772a3.js`](./nordic.atlas-details.0196.3472df4656d772a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.bbfacea2dd7d2446.js`](./nordic.atlas-details.0197.bbfacea2dd7d2446.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.b6bbe41b29b04a66.js`](./nordic.atlas-details.0198.b6bbe41b29b04a66.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.9169f1039f65019f.js`](./nordic.atlas-details.0199.9169f1039f65019f.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.54e218b47c2ceab8.js`](./nordic.atlas-details.0200.54e218b47c2ceab8.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.4cf7e97d8aa5f68d.js`](./nordic.atlas-details.0201.4cf7e97d8aa5f68d.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.0f9d55c1911a8206.js`](./nordic.atlas-details.0202.0f9d55c1911a8206.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.0f53d69cb086d0fb.js`](./nordic.atlas-details.0203.0f53d69cb086d0fb.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.8e23bb58d0a44ac7.js`](./nordic.atlas-details.0204.8e23bb58d0a44ac7.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.4a331c889995f1d4.js`](./nordic.atlas-details.0205.4a331c889995f1d4.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.c18ba15da34b830d.js`](./nordic.atlas-details.0206.c18ba15da34b830d.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.4d21dbb05cc6f9a0.js`](./nordic.atlas-details.0207.4d21dbb05cc6f9a0.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.768a6317c4bc38b9.js`](./nordic.atlas-details.0208.768a6317c4bc38b9.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.9e7a09e1215215a6.js`](./nordic.atlas-details.0209.9e7a09e1215215a6.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.9f2c7fc14a698546.js`](./nordic.atlas-details.0210.9f2c7fc14a698546.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.8247b26f266369e3.js`](./nordic.atlas-details.0211.8247b26f266369e3.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.c86ed721eb90cf7a.js`](./nordic.atlas-details.0212.c86ed721eb90cf7a.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.8467589b4e5f4465.js`](./nordic.atlas-details.0213.8467589b4e5f4465.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.e7194b4fe2765bb2.js`](./nordic.atlas-details.0214.e7194b4fe2765bb2.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.2a1187bcd9c377fa.js`](./nordic.atlas-details.0215.2a1187bcd9c377fa.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.40423988e96a79b5.js`](./nordic.atlas-details.0216.40423988e96a79b5.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.a939d176315a08d9.js`](./nordic.atlas-details.0217.a939d176315a08d9.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.aa84a126a6d1e255.js`](./nordic.atlas-details.0218.aa84a126a6d1e255.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.55e2c548b4e10bce.js`](./nordic.atlas-details.0219.55e2c548b4e10bce.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.a0e6f5e7c7232c90.js`](./nordic.atlas-details.0220.a0e6f5e7c7232c90.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.88434143ae98b0a9.js`](./nordic.atlas-details.0221.88434143ae98b0a9.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.7b59240c8fdbbf49.js`](./nordic.atlas-details.0222.7b59240c8fdbbf49.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.75fe7a1aff0031d4.js`](./nordic.atlas-details.0223.75fe7a1aff0031d4.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.d314073378a28d66.js`](./nordic.atlas-details.0224.d314073378a28d66.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.7e9a7f7b04040177.js`](./nordic.atlas-details.0225.7e9a7f7b04040177.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.2ab980a9a16b7ce6.js`](./nordic.atlas-details.0226.2ab980a9a16b7ce6.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.6615126ccacda4c2.js`](./nordic.atlas-details.0227.6615126ccacda4c2.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.a591e085888f5548.js`](./nordic.atlas-details.0228.a591e085888f5548.js)
- Static atlas data chunk: [`nordic.atlas-edges.0229.1b8ca2f318957def.js`](./nordic.atlas-edges.0229.1b8ca2f318957def.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0230.323686a6af374697.js`](./nordic.atlas-sequences.0230.323686a6af374697.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0231.9a7022f42f03c6a6.js`](./nordic.atlas-indexes.0231.9a7022f42f03c6a6.js)
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
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `9738` |
| Cattle aDNA site evidence (wild or progenitor context) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `4` |
| Sheep aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Pig aDNA site evidence (domesticated core) | `shared_world_scale_layer` | Mapped animal features staged from traceable evidence rows built from species-owned sample, site, coordinate, and citation surfaces. | `2` |
| Neotoma sample pollen-presence context | `scope_specific_overlay` | Dated source samples with positive reported pollen observations; not reviewed pollen-sum events. | `9988` |
| Neotoma literal ecological codes | `scope_specific_overlay` | Literal source ecological codes without cross-source equivalence or propagation claims. | `25165` |
| Neotoma exact source taxa | `scope_specific_overlay` | Exact source taxon identities without accepted ecological classification or propagation claims. | `215751` |
| Country boundaries | `region_filtered_layer` | Published country outlines used for framing and scope-aware map filtering. | `4` |
| LandClim REVEALS time-window grids | `scope_specific_overlay` | Time-window-specific REVEALS grid estimates from published LandClim PANGAEA datasets. | `2515` |

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


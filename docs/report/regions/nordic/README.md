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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.9e610aeeaccd210b.js`](./nordic.atlas-provenance.0000.9e610aeeaccd210b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.2ff4890176c36b6a.js`](./nordic.atlas-nodes.0001.2ff4890176c36b6a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.c96cba02b95f8e1c.js`](./nordic.atlas-nodes.0002.c96cba02b95f8e1c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.4da26f072f60397b.js`](./nordic.atlas-nodes.0003.4da26f072f60397b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.5f3a8ecc4ef8898e.js`](./nordic.atlas-nodes.0004.5f3a8ecc4ef8898e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.fb12e004e847b918.js`](./nordic.atlas-nodes.0005.fb12e004e847b918.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.781240318fbe0be7.js`](./nordic.atlas-nodes.0006.781240318fbe0be7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.0edaaa2981bcaca0.js`](./nordic.atlas-nodes.0007.0edaaa2981bcaca0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.edc7ad19bbdd07a1.js`](./nordic.atlas-nodes.0008.edc7ad19bbdd07a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.a9b6787b6d88f522.js`](./nordic.atlas-nodes.0009.a9b6787b6d88f522.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.2ace8c3b92b418aa.js`](./nordic.atlas-nodes.0010.2ace8c3b92b418aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.7a95f5a5b0ff818e.js`](./nordic.atlas-nodes.0011.7a95f5a5b0ff818e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.a580b674e0fd71d5.js`](./nordic.atlas-nodes.0012.a580b674e0fd71d5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.ec92b89d5e02e1a7.js`](./nordic.atlas-nodes.0013.ec92b89d5e02e1a7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.be91338e7eebc517.js`](./nordic.atlas-nodes.0014.be91338e7eebc517.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.db58bf0f324beaa7.js`](./nordic.atlas-nodes.0015.db58bf0f324beaa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.521e487af783ac92.js`](./nordic.atlas-nodes.0016.521e487af783ac92.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.036705b19d4cd9fc.js`](./nordic.atlas-nodes.0017.036705b19d4cd9fc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.796d22f1e0eed43b.js`](./nordic.atlas-nodes.0018.796d22f1e0eed43b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.96ee265d7a7f8af8.js`](./nordic.atlas-nodes.0019.96ee265d7a7f8af8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.306794204b644e6d.js`](./nordic.atlas-nodes.0020.306794204b644e6d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.53fb9b6e817eb4a4.js`](./nordic.atlas-nodes.0021.53fb9b6e817eb4a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.1d811123361af439.js`](./nordic.atlas-nodes.0022.1d811123361af439.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.015f6ac319fc942a.js`](./nordic.atlas-nodes.0023.015f6ac319fc942a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.11bc1f68aa917d5e.js`](./nordic.atlas-nodes.0024.11bc1f68aa917d5e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.0dda4d1808c89e1d.js`](./nordic.atlas-nodes.0025.0dda4d1808c89e1d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.fec7b6ce16d22465.js`](./nordic.atlas-nodes.0026.fec7b6ce16d22465.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.7d4c7654bffe929b.js`](./nordic.atlas-nodes.0027.7d4c7654bffe929b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.a81d2d2058c3e496.js`](./nordic.atlas-nodes.0028.a81d2d2058c3e496.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.b6b8e9d596479c5d.js`](./nordic.atlas-nodes.0029.b6b8e9d596479c5d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.6168f2c6662728e0.js`](./nordic.atlas-nodes.0030.6168f2c6662728e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.dee5593aaebe3fe1.js`](./nordic.atlas-nodes.0031.dee5593aaebe3fe1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.bc44d6c7f56c484c.js`](./nordic.atlas-nodes.0032.bc44d6c7f56c484c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.f1ebc678ad78c635.js`](./nordic.atlas-nodes.0033.f1ebc678ad78c635.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.1637ab92b0f03e2c.js`](./nordic.atlas-nodes.0034.1637ab92b0f03e2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.8dc68e0c1987e890.js`](./nordic.atlas-nodes.0035.8dc68e0c1987e890.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.7bf985aa8d23ed16.js`](./nordic.atlas-nodes.0036.7bf985aa8d23ed16.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.8946ece0e3cc6822.js`](./nordic.atlas-nodes.0037.8946ece0e3cc6822.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.37c199c77e3ae669.js`](./nordic.atlas-nodes.0038.37c199c77e3ae669.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.8a56b177c4bf8b00.js`](./nordic.atlas-nodes.0039.8a56b177c4bf8b00.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.c463fc03d5bf71be.js`](./nordic.atlas-nodes.0040.c463fc03d5bf71be.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.7485b36851c97429.js`](./nordic.atlas-nodes.0041.7485b36851c97429.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.368dd033d21e6da0.js`](./nordic.atlas-nodes.0042.368dd033d21e6da0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.c51463046a38b94e.js`](./nordic.atlas-nodes.0043.c51463046a38b94e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.c9f5fbfaf35d15dd.js`](./nordic.atlas-nodes.0044.c9f5fbfaf35d15dd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.96d75cf6f1496706.js`](./nordic.atlas-nodes.0045.96d75cf6f1496706.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.4a27b16c3a525ddc.js`](./nordic.atlas-nodes.0046.4a27b16c3a525ddc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.a8700903deeb0ffd.js`](./nordic.atlas-nodes.0047.a8700903deeb0ffd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.d2eaff9029b1ecab.js`](./nordic.atlas-nodes.0048.d2eaff9029b1ecab.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.a77acfa5b634c87c.js`](./nordic.atlas-nodes.0049.a77acfa5b634c87c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.16562012b79ea810.js`](./nordic.atlas-nodes.0050.16562012b79ea810.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.9f57efba2dbc5ef4.js`](./nordic.atlas-nodes.0051.9f57efba2dbc5ef4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.977553cc43898f8b.js`](./nordic.atlas-nodes.0052.977553cc43898f8b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.c07bc6f012340265.js`](./nordic.atlas-nodes.0053.c07bc6f012340265.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.dd1dec2ac3c433a0.js`](./nordic.atlas-nodes.0054.dd1dec2ac3c433a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.6b3315082aec32e8.js`](./nordic.atlas-nodes.0055.6b3315082aec32e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.8e11aa3245f09f95.js`](./nordic.atlas-nodes.0056.8e11aa3245f09f95.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.25abacf21b302d47.js`](./nordic.atlas-nodes.0057.25abacf21b302d47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.bcb1445625e3763a.js`](./nordic.atlas-nodes.0058.bcb1445625e3763a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.1e462ef6507e5263.js`](./nordic.atlas-nodes.0059.1e462ef6507e5263.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.4c850b03d2bcfc09.js`](./nordic.atlas-nodes.0060.4c850b03d2bcfc09.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.632d23da6527380b.js`](./nordic.atlas-nodes.0061.632d23da6527380b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.79adf04be06931d6.js`](./nordic.atlas-nodes.0062.79adf04be06931d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.ec0f742a8ec9f7eb.js`](./nordic.atlas-nodes.0063.ec0f742a8ec9f7eb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.8e80929490f3c0e7.js`](./nordic.atlas-nodes.0064.8e80929490f3c0e7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.c872520710d90a34.js`](./nordic.atlas-nodes.0065.c872520710d90a34.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.90ccc963c094a33d.js`](./nordic.atlas-nodes.0066.90ccc963c094a33d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.16a58c12b5560a1d.js`](./nordic.atlas-nodes.0067.16a58c12b5560a1d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.6677d4680f119ee6.js`](./nordic.atlas-nodes.0068.6677d4680f119ee6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.50d1e3cdca406941.js`](./nordic.atlas-nodes.0069.50d1e3cdca406941.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.98ff806971fe9571.js`](./nordic.atlas-nodes.0070.98ff806971fe9571.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.c560641f34670822.js`](./nordic.atlas-nodes.0071.c560641f34670822.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.770b2da2e1381ec6.js`](./nordic.atlas-nodes.0072.770b2da2e1381ec6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.56140d089f9a0571.js`](./nordic.atlas-nodes.0073.56140d089f9a0571.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.2df94ec52bdbafb7.js`](./nordic.atlas-nodes.0074.2df94ec52bdbafb7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.65f2f3ae22a263d3.js`](./nordic.atlas-nodes.0075.65f2f3ae22a263d3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.bd92bcae1ca3eda5.js`](./nordic.atlas-nodes.0076.bd92bcae1ca3eda5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.b979e43fedd50c22.js`](./nordic.atlas-nodes.0077.b979e43fedd50c22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.2aed7112ce021066.js`](./nordic.atlas-nodes.0078.2aed7112ce021066.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.2cb0b422876a1e22.js`](./nordic.atlas-nodes.0079.2cb0b422876a1e22.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.8e5637f858ed5a25.js`](./nordic.atlas-nodes.0080.8e5637f858ed5a25.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.247a4c8706f61cb7.js`](./nordic.atlas-nodes.0081.247a4c8706f61cb7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.c229cd3fc0aeaf50.js`](./nordic.atlas-nodes.0082.c229cd3fc0aeaf50.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.f3de6ddaf5f3a5ff.js`](./nordic.atlas-nodes.0083.f3de6ddaf5f3a5ff.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.d7cda9a8078e22c2.js`](./nordic.atlas-nodes.0084.d7cda9a8078e22c2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.d9e3d083072d8033.js`](./nordic.atlas-nodes.0085.d9e3d083072d8033.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.d372a561359a1478.js`](./nordic.atlas-nodes.0086.d372a561359a1478.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.18ef204edb487401.js`](./nordic.atlas-nodes.0087.18ef204edb487401.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.c7d425e1111812d6.js`](./nordic.atlas-nodes.0088.c7d425e1111812d6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.cdcd7460dc56f0d9.js`](./nordic.atlas-nodes.0089.cdcd7460dc56f0d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.95d5e9e66cdeb57f.js`](./nordic.atlas-nodes.0090.95d5e9e66cdeb57f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.5f1a7eee6128f2b7.js`](./nordic.atlas-nodes.0091.5f1a7eee6128f2b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.d3bfbba001c909cc.js`](./nordic.atlas-nodes.0092.d3bfbba001c909cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.99a362b0c42d0f27.js`](./nordic.atlas-nodes.0093.99a362b0c42d0f27.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.62a1f414b967f2fd.js`](./nordic.atlas-nodes.0094.62a1f414b967f2fd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.201c438c00df8fe5.js`](./nordic.atlas-nodes.0095.201c438c00df8fe5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.d0016491f8c8e58c.js`](./nordic.atlas-nodes.0096.d0016491f8c8e58c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.9046ce66506e2161.js`](./nordic.atlas-nodes.0097.9046ce66506e2161.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.44c7c92147ded675.js`](./nordic.atlas-nodes.0098.44c7c92147ded675.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.88e5e1a977a74282.js`](./nordic.atlas-nodes.0099.88e5e1a977a74282.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.818ed4b3f21b66f4.js`](./nordic.atlas-nodes.0100.818ed4b3f21b66f4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.d70d1ccea6e1473f.js`](./nordic.atlas-nodes.0101.d70d1ccea6e1473f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.88c27d57acc65971.js`](./nordic.atlas-nodes.0102.88c27d57acc65971.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.17f3dfb65eacf3c6.js`](./nordic.atlas-nodes.0103.17f3dfb65eacf3c6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.7000dea1b5d7e9b8.js`](./nordic.atlas-nodes.0104.7000dea1b5d7e9b8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.7ca5140845168f41.js`](./nordic.atlas-nodes.0105.7ca5140845168f41.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.9600209d404e1294.js`](./nordic.atlas-nodes.0106.9600209d404e1294.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.be974971c6494432.js`](./nordic.atlas-nodes.0107.be974971c6494432.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.b14b43561e70e23c.js`](./nordic.atlas-nodes.0108.b14b43561e70e23c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.fd358c1f6e566c72.js`](./nordic.atlas-nodes.0109.fd358c1f6e566c72.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.471ef90efb062c53.js`](./nordic.atlas-nodes.0110.471ef90efb062c53.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.e333a45bfe3c9e3a.js`](./nordic.atlas-nodes.0111.e333a45bfe3c9e3a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.14b5bfa57813923b.js`](./nordic.atlas-nodes.0112.14b5bfa57813923b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.63faefecb652176f.js`](./nordic.atlas-nodes.0113.63faefecb652176f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.1da1647ee50c521e.js`](./nordic.atlas-nodes.0114.1da1647ee50c521e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.817be95ac196ac46.js`](./nordic.atlas-nodes.0115.817be95ac196ac46.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.8aa74d334788cea9.js`](./nordic.atlas-nodes.0116.8aa74d334788cea9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.63506e488a203601.js`](./nordic.atlas-nodes.0117.63506e488a203601.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.42de9f1bae4e4e99.js`](./nordic.atlas-nodes.0118.42de9f1bae4e4e99.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.60bcd003ef6ca7ad.js`](./nordic.atlas-nodes.0119.60bcd003ef6ca7ad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.daecad7b01c9da4a.js`](./nordic.atlas-nodes.0120.daecad7b01c9da4a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.79be6efbdbd57ec8.js`](./nordic.atlas-nodes.0121.79be6efbdbd57ec8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.09bb1801d85d47b3.js`](./nordic.atlas-nodes.0122.09bb1801d85d47b3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.86e1d4704824f6a4.js`](./nordic.atlas-nodes.0123.86e1d4704824f6a4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.a82c2e18738c17a6.js`](./nordic.atlas-nodes.0124.a82c2e18738c17a6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.a0672b154d6e594b.js`](./nordic.atlas-nodes.0125.a0672b154d6e594b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.ca09c7bf5a5b91bc.js`](./nordic.atlas-nodes.0126.ca09c7bf5a5b91bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.bfa66b5b37f6c56f.js`](./nordic.atlas-nodes.0127.bfa66b5b37f6c56f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.5d7c5b0289c21cb2.js`](./nordic.atlas-nodes.0128.5d7c5b0289c21cb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.55ab4b8b0615bc1f.js`](./nordic.atlas-nodes.0129.55ab4b8b0615bc1f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.f4de962c3b1bc392.js`](./nordic.atlas-nodes.0130.f4de962c3b1bc392.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.5dfd871977511b87.js`](./nordic.atlas-nodes.0131.5dfd871977511b87.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.59f5443acad86485.js`](./nordic.atlas-nodes.0132.59f5443acad86485.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.e4a146bc04be64aa.js`](./nordic.atlas-nodes.0133.e4a146bc04be64aa.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.9d9c2edcbbcf0442.js`](./nordic.atlas-nodes.0134.9d9c2edcbbcf0442.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.0de3c2b856b4c2ef.js`](./nordic.atlas-nodes.0135.0de3c2b856b4c2ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.9bd4c9faf0bd9959.js`](./nordic.atlas-nodes.0136.9bd4c9faf0bd9959.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.24dcd03307ba3d31.js`](./nordic.atlas-nodes.0137.24dcd03307ba3d31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.a1070ef90b5eb692.js`](./nordic.atlas-nodes.0138.a1070ef90b5eb692.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.a6d077a052cff594.js`](./nordic.atlas-nodes.0139.a6d077a052cff594.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.e89cbc09cd4ba970.js`](./nordic.atlas-nodes.0140.e89cbc09cd4ba970.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.3b8081ed58f99151.js`](./nordic.atlas-nodes.0141.3b8081ed58f99151.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.239da5312a40265e.js`](./nordic.atlas-nodes.0142.239da5312a40265e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.8d48c5296854ecd0.js`](./nordic.atlas-nodes.0143.8d48c5296854ecd0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.11391c9ab3a4ee59.js`](./nordic.atlas-nodes.0144.11391c9ab3a4ee59.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.892995ecc83c6df1.js`](./nordic.atlas-nodes.0145.892995ecc83c6df1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.ed5664166113f518.js`](./nordic.atlas-nodes.0146.ed5664166113f518.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.9de99b184f98882c.js`](./nordic.atlas-nodes.0147.9de99b184f98882c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.4aa658022fee3f13.js`](./nordic.atlas-nodes.0148.4aa658022fee3f13.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.17a1551259b8bee4.js`](./nordic.atlas-nodes.0149.17a1551259b8bee4.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.a43ef330f5129bf1.js`](./nordic.atlas-nodes.0150.a43ef330f5129bf1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.7a5d49ec20881d94.js`](./nordic.atlas-nodes.0151.7a5d49ec20881d94.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.335205fdf2fdc5ac.js`](./nordic.atlas-nodes.0152.335205fdf2fdc5ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.a570bbdd1b451502.js`](./nordic.atlas-nodes.0153.a570bbdd1b451502.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.7849eee104d30241.js`](./nordic.atlas-nodes.0154.7849eee104d30241.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.cfa01de876977340.js`](./nordic.atlas-nodes.0155.cfa01de876977340.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.948d04c5cc42c969.js`](./nordic.atlas-nodes.0156.948d04c5cc42c969.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.68f194942daf47d0.js`](./nordic.atlas-nodes.0157.68f194942daf47d0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.b87aaf3a0363d9c7.js`](./nordic.atlas-nodes.0158.b87aaf3a0363d9c7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.8ab8c9e4f9765de1.js`](./nordic.atlas-nodes.0159.8ab8c9e4f9765de1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.6f365f67f2c22768.js`](./nordic.atlas-nodes.0160.6f365f67f2c22768.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.df97dc057d20942d.js`](./nordic.atlas-nodes.0161.df97dc057d20942d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.e21f978e2d58b268.js`](./nordic.atlas-nodes.0162.e21f978e2d58b268.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.1a90a9ded9f2dec7.js`](./nordic.atlas-nodes.0163.1a90a9ded9f2dec7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.62d809a374799448.js`](./nordic.atlas-nodes.0164.62d809a374799448.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.196f460e2100dbfb.js`](./nordic.atlas-nodes.0165.196f460e2100dbfb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.295409e3ff79b1e8.js`](./nordic.atlas-nodes.0166.295409e3ff79b1e8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.1d977a3331c9f689.js`](./nordic.atlas-nodes.0167.1d977a3331c9f689.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.baabd28e4879c459.js`](./nordic.atlas-nodes.0168.baabd28e4879c459.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.4593641c17b957a0.js`](./nordic.atlas-nodes.0169.4593641c17b957a0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.4251fc66dfb88b7a.js`](./nordic.atlas-nodes.0170.4251fc66dfb88b7a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0171.b99796e2343c3e7b.js`](./nordic.atlas-nodes.0171.b99796e2343c3e7b.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.d944d95be35546bb.js`](./nordic.atlas-details.0172.d944d95be35546bb.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.7a11f218b12a199b.js`](./nordic.atlas-details.0173.7a11f218b12a199b.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.86a9f676a339e58c.js`](./nordic.atlas-details.0174.86a9f676a339e58c.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.2df2fbf45a829b0c.js`](./nordic.atlas-details.0175.2df2fbf45a829b0c.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.54188e6fa10e0121.js`](./nordic.atlas-details.0176.54188e6fa10e0121.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.7d48fc993498f8ba.js`](./nordic.atlas-details.0177.7d48fc993498f8ba.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.db2f0f00b94a9b9f.js`](./nordic.atlas-details.0178.db2f0f00b94a9b9f.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.2bd8172a41c3c2d6.js`](./nordic.atlas-details.0179.2bd8172a41c3c2d6.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.a506b32ba9adcb98.js`](./nordic.atlas-details.0180.a506b32ba9adcb98.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.69dacafa3a2cdf4f.js`](./nordic.atlas-details.0181.69dacafa3a2cdf4f.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.bb0abf0e97b865f6.js`](./nordic.atlas-details.0182.bb0abf0e97b865f6.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.35341be0a20c1219.js`](./nordic.atlas-details.0183.35341be0a20c1219.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.35f1f0d211b5d129.js`](./nordic.atlas-details.0184.35f1f0d211b5d129.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.59ba0c1b32aec52a.js`](./nordic.atlas-details.0185.59ba0c1b32aec52a.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.7f9dabe8acc2e272.js`](./nordic.atlas-details.0186.7f9dabe8acc2e272.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.b6b40ffb133d0252.js`](./nordic.atlas-details.0187.b6b40ffb133d0252.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.39ac93591d7be068.js`](./nordic.atlas-details.0188.39ac93591d7be068.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.634f306df1608002.js`](./nordic.atlas-details.0189.634f306df1608002.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.70859f9e1971bff1.js`](./nordic.atlas-details.0190.70859f9e1971bff1.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.42865ed68d56a9a7.js`](./nordic.atlas-details.0191.42865ed68d56a9a7.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.287fe77022f1c4d3.js`](./nordic.atlas-details.0192.287fe77022f1c4d3.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.63dd0d0da1821eb2.js`](./nordic.atlas-details.0193.63dd0d0da1821eb2.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.9872923f0497b2d5.js`](./nordic.atlas-details.0194.9872923f0497b2d5.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.354bf5475f416cf5.js`](./nordic.atlas-details.0195.354bf5475f416cf5.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.62312f7548846729.js`](./nordic.atlas-details.0196.62312f7548846729.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.7a1e4375249d2032.js`](./nordic.atlas-details.0197.7a1e4375249d2032.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.93f40767f7f7217b.js`](./nordic.atlas-details.0198.93f40767f7f7217b.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.055dc010409a6861.js`](./nordic.atlas-details.0199.055dc010409a6861.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.83d6d4e5939e7a2f.js`](./nordic.atlas-details.0200.83d6d4e5939e7a2f.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.52fed5eafc49c854.js`](./nordic.atlas-details.0201.52fed5eafc49c854.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.70da17ae0e918252.js`](./nordic.atlas-details.0202.70da17ae0e918252.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.481b5cadc9e1dd45.js`](./nordic.atlas-details.0203.481b5cadc9e1dd45.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.61511d3137864015.js`](./nordic.atlas-details.0204.61511d3137864015.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.6f4c97808a90b00a.js`](./nordic.atlas-details.0205.6f4c97808a90b00a.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.5e268a500b7fa51a.js`](./nordic.atlas-details.0206.5e268a500b7fa51a.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.eed2b1f432253cf9.js`](./nordic.atlas-details.0207.eed2b1f432253cf9.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.3a261ce0f33678ff.js`](./nordic.atlas-details.0208.3a261ce0f33678ff.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.a97a04c696fd9a62.js`](./nordic.atlas-details.0209.a97a04c696fd9a62.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.933cb6b4a06f208f.js`](./nordic.atlas-details.0210.933cb6b4a06f208f.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.eb2f3e22749fb666.js`](./nordic.atlas-details.0211.eb2f3e22749fb666.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.5ed70210cb354a51.js`](./nordic.atlas-details.0212.5ed70210cb354a51.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.a446bba6cc9aaad8.js`](./nordic.atlas-details.0213.a446bba6cc9aaad8.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.c203c84a449d923e.js`](./nordic.atlas-details.0214.c203c84a449d923e.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.b0e475e7b3b12086.js`](./nordic.atlas-details.0215.b0e475e7b3b12086.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.63c407f78ac756cd.js`](./nordic.atlas-details.0216.63c407f78ac756cd.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.6a9fbeed13d8a198.js`](./nordic.atlas-details.0217.6a9fbeed13d8a198.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.17d25ca90f0d5376.js`](./nordic.atlas-details.0218.17d25ca90f0d5376.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.fd80c5a9bb628687.js`](./nordic.atlas-details.0219.fd80c5a9bb628687.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.333581c782969afb.js`](./nordic.atlas-details.0220.333581c782969afb.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.8c19930aec754def.js`](./nordic.atlas-details.0221.8c19930aec754def.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.e76d5937e4c6c49d.js`](./nordic.atlas-details.0222.e76d5937e4c6c49d.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.ad23c5f222be8b4f.js`](./nordic.atlas-details.0223.ad23c5f222be8b4f.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.674da0535e44c029.js`](./nordic.atlas-details.0224.674da0535e44c029.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.74f65c19b9b9ccbe.js`](./nordic.atlas-details.0225.74f65c19b9b9ccbe.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.3ec4b5239dba0c42.js`](./nordic.atlas-details.0226.3ec4b5239dba0c42.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.3d647abf00c3b5d5.js`](./nordic.atlas-details.0227.3d647abf00c3b5d5.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.a0656d9e57616efc.js`](./nordic.atlas-details.0228.a0656d9e57616efc.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.72bd49d3c3aa54f1.js`](./nordic.atlas-details.0229.72bd49d3c3aa54f1.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.522de13deeee3c37.js`](./nordic.atlas-details.0230.522de13deeee3c37.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.ee057e8c399b11a8.js`](./nordic.atlas-details.0231.ee057e8c399b11a8.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.5ad69ecc91644183.js`](./nordic.atlas-details.0232.5ad69ecc91644183.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.e16f20c8c5745e9d.js`](./nordic.atlas-details.0233.e16f20c8c5745e9d.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.a806a06e25318d00.js`](./nordic.atlas-details.0234.a806a06e25318d00.js)
- Static atlas data chunk: [`nordic.atlas-details.0235.d9cec186e95b613f.js`](./nordic.atlas-details.0235.d9cec186e95b613f.js)
- Static atlas data chunk: [`nordic.atlas-edges.0236.91b34d5ee2b0011a.js`](./nordic.atlas-edges.0236.91b34d5ee2b0011a.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0237.8fbfb5cc5004b366.js`](./nordic.atlas-sequences.0237.8fbfb5cc5004b366.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0238.3f42c142d3addfaa.js`](./nordic.atlas-indexes.0238.3f42c142d3addfaa.js)
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
| SEAD sites | `scope_specific_overlay` | SEAD site inventory for spatial context. Site envelopes summarize source chronology and are not dated events or interval evidence. | `2069` |
| Sweden archaeology site discovery | `scope_specific_overlay` | Every geolocated Swedish SEAD site, represented by each linked numeric chronology interval or by one explicitly unresolved temporal record. | `8799` |
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


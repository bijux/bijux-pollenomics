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
- Static atlas data chunk: [`nordic.atlas-provenance.0000.7831f37653dea0b9.js`](./nordic.atlas-provenance.0000.7831f37653dea0b9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0001.b3de558613d61506.js`](./nordic.atlas-nodes.0001.b3de558613d61506.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0002.1f46d68357504528.js`](./nordic.atlas-nodes.0002.1f46d68357504528.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0003.80e53e84f182d74b.js`](./nordic.atlas-nodes.0003.80e53e84f182d74b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0004.dba4b029f5891aef.js`](./nordic.atlas-nodes.0004.dba4b029f5891aef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0005.9165649e5304377a.js`](./nordic.atlas-nodes.0005.9165649e5304377a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0006.5d20c5f5103409a9.js`](./nordic.atlas-nodes.0006.5d20c5f5103409a9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0007.b976be6c73f376d9.js`](./nordic.atlas-nodes.0007.b976be6c73f376d9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0008.dc63c2d0fbffcd3e.js`](./nordic.atlas-nodes.0008.dc63c2d0fbffcd3e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0009.dfcfa8d8171c9ceb.js`](./nordic.atlas-nodes.0009.dfcfa8d8171c9ceb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0010.0c87646354bb4659.js`](./nordic.atlas-nodes.0010.0c87646354bb4659.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0011.0f952d9f2ea1914f.js`](./nordic.atlas-nodes.0011.0f952d9f2ea1914f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0012.b8e1bdefa9854761.js`](./nordic.atlas-nodes.0012.b8e1bdefa9854761.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0013.3c92a023e6738cfd.js`](./nordic.atlas-nodes.0013.3c92a023e6738cfd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0014.7ea3d954d6190c3f.js`](./nordic.atlas-nodes.0014.7ea3d954d6190c3f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0015.5945945164477500.js`](./nordic.atlas-nodes.0015.5945945164477500.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0016.18d24fc7d9b77963.js`](./nordic.atlas-nodes.0016.18d24fc7d9b77963.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0017.d2d8ea1f43dbe485.js`](./nordic.atlas-nodes.0017.d2d8ea1f43dbe485.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0018.d2dbc1c51e8daab6.js`](./nordic.atlas-nodes.0018.d2dbc1c51e8daab6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0019.38315d811ee72489.js`](./nordic.atlas-nodes.0019.38315d811ee72489.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0020.cf1962c24ecca837.js`](./nordic.atlas-nodes.0020.cf1962c24ecca837.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0021.3f09f9f88eea0003.js`](./nordic.atlas-nodes.0021.3f09f9f88eea0003.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0022.9aa22efe4176773d.js`](./nordic.atlas-nodes.0022.9aa22efe4176773d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0023.05faf8aae1e615cc.js`](./nordic.atlas-nodes.0023.05faf8aae1e615cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0024.eb7a6741151aa65c.js`](./nordic.atlas-nodes.0024.eb7a6741151aa65c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0025.3381df5138c502da.js`](./nordic.atlas-nodes.0025.3381df5138c502da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0026.b82d47e366eea28e.js`](./nordic.atlas-nodes.0026.b82d47e366eea28e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0027.ec2ef53be280de42.js`](./nordic.atlas-nodes.0027.ec2ef53be280de42.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0028.fab4a6b47905b349.js`](./nordic.atlas-nodes.0028.fab4a6b47905b349.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0029.f9357b1b2e511536.js`](./nordic.atlas-nodes.0029.f9357b1b2e511536.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0030.136b831adbbe999a.js`](./nordic.atlas-nodes.0030.136b831adbbe999a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0031.99b432191da6e18b.js`](./nordic.atlas-nodes.0031.99b432191da6e18b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0032.2736492cac97e408.js`](./nordic.atlas-nodes.0032.2736492cac97e408.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0033.5d1cc6f5445f331f.js`](./nordic.atlas-nodes.0033.5d1cc6f5445f331f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0034.31ce6c6d186c85ba.js`](./nordic.atlas-nodes.0034.31ce6c6d186c85ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0035.d552a7f2735bba69.js`](./nordic.atlas-nodes.0035.d552a7f2735bba69.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0036.f8c87b1f44944b4a.js`](./nordic.atlas-nodes.0036.f8c87b1f44944b4a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0037.5b65306af7748f5e.js`](./nordic.atlas-nodes.0037.5b65306af7748f5e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0038.b6c5897eff78bc2a.js`](./nordic.atlas-nodes.0038.b6c5897eff78bc2a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0039.9da2a46677707a71.js`](./nordic.atlas-nodes.0039.9da2a46677707a71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0040.ece5bd312a6c67c1.js`](./nordic.atlas-nodes.0040.ece5bd312a6c67c1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0041.70ab2faa7ef056a5.js`](./nordic.atlas-nodes.0041.70ab2faa7ef056a5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0042.4d3302660f53a929.js`](./nordic.atlas-nodes.0042.4d3302660f53a929.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0043.d4e7f89c6c0fc918.js`](./nordic.atlas-nodes.0043.d4e7f89c6c0fc918.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0044.24162c1c0c453bea.js`](./nordic.atlas-nodes.0044.24162c1c0c453bea.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0045.dacede3acbb23975.js`](./nordic.atlas-nodes.0045.dacede3acbb23975.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0046.a19051e008bfdcb2.js`](./nordic.atlas-nodes.0046.a19051e008bfdcb2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0047.2f44987fde439048.js`](./nordic.atlas-nodes.0047.2f44987fde439048.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0048.dd152a561c85a353.js`](./nordic.atlas-nodes.0048.dd152a561c85a353.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0049.204ed6fab1d3f0ac.js`](./nordic.atlas-nodes.0049.204ed6fab1d3f0ac.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0050.744da874b001ae2c.js`](./nordic.atlas-nodes.0050.744da874b001ae2c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0051.238c690e819b1aa2.js`](./nordic.atlas-nodes.0051.238c690e819b1aa2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0052.a7a587920fd97b96.js`](./nordic.atlas-nodes.0052.a7a587920fd97b96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0053.b9db22336cffc2e2.js`](./nordic.atlas-nodes.0053.b9db22336cffc2e2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0054.5228cf2745a78b3f.js`](./nordic.atlas-nodes.0054.5228cf2745a78b3f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0055.2e15ebbc53d6d32c.js`](./nordic.atlas-nodes.0055.2e15ebbc53d6d32c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0056.02e4eb302e467b1b.js`](./nordic.atlas-nodes.0056.02e4eb302e467b1b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0057.9dcaa2e867eec3da.js`](./nordic.atlas-nodes.0057.9dcaa2e867eec3da.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0058.31155097586683a1.js`](./nordic.atlas-nodes.0058.31155097586683a1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0059.8ef03f0b602bb8cc.js`](./nordic.atlas-nodes.0059.8ef03f0b602bb8cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0060.09ba5f3a311f51b1.js`](./nordic.atlas-nodes.0060.09ba5f3a311f51b1.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0061.d1611efd3a4e74ee.js`](./nordic.atlas-nodes.0061.d1611efd3a4e74ee.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0062.f453323b5234e6ef.js`](./nordic.atlas-nodes.0062.f453323b5234e6ef.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0063.accec1424b1f8735.js`](./nordic.atlas-nodes.0063.accec1424b1f8735.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0064.9ac663c08d5edec6.js`](./nordic.atlas-nodes.0064.9ac663c08d5edec6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0065.b5042d1ad4327189.js`](./nordic.atlas-nodes.0065.b5042d1ad4327189.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0066.734f2833e37186b5.js`](./nordic.atlas-nodes.0066.734f2833e37186b5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0067.1440c985cb28f544.js`](./nordic.atlas-nodes.0067.1440c985cb28f544.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0068.e71eb8ff8684f037.js`](./nordic.atlas-nodes.0068.e71eb8ff8684f037.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0069.e61f134009d54b6b.js`](./nordic.atlas-nodes.0069.e61f134009d54b6b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0070.2c77deab1abdc855.js`](./nordic.atlas-nodes.0070.2c77deab1abdc855.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0071.296ef50bdcf72408.js`](./nordic.atlas-nodes.0071.296ef50bdcf72408.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0072.c191b1acee6c756a.js`](./nordic.atlas-nodes.0072.c191b1acee6c756a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0073.4fc5a4457acf551e.js`](./nordic.atlas-nodes.0073.4fc5a4457acf551e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0074.f2be9b44396a8433.js`](./nordic.atlas-nodes.0074.f2be9b44396a8433.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0075.6132903221ed73ca.js`](./nordic.atlas-nodes.0075.6132903221ed73ca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0076.6198dea45b344fd9.js`](./nordic.atlas-nodes.0076.6198dea45b344fd9.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0077.4b077b819b200bf3.js`](./nordic.atlas-nodes.0077.4b077b819b200bf3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0078.b46796413c1cd2ba.js`](./nordic.atlas-nodes.0078.b46796413c1cd2ba.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0079.068a6d9c8edc8fec.js`](./nordic.atlas-nodes.0079.068a6d9c8edc8fec.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0080.24773f7311d2d143.js`](./nordic.atlas-nodes.0080.24773f7311d2d143.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0081.0bb22486d4ac7f96.js`](./nordic.atlas-nodes.0081.0bb22486d4ac7f96.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0082.f146e41cc645c1ed.js`](./nordic.atlas-nodes.0082.f146e41cc645c1ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0083.b2eb2b6efcfbe4ce.js`](./nordic.atlas-nodes.0083.b2eb2b6efcfbe4ce.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0084.86a82d0bcd4e6aca.js`](./nordic.atlas-nodes.0084.86a82d0bcd4e6aca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0085.c99d69210d2e4952.js`](./nordic.atlas-nodes.0085.c99d69210d2e4952.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0086.0ef1882b0d9ba696.js`](./nordic.atlas-nodes.0086.0ef1882b0d9ba696.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0087.bae912fb98170796.js`](./nordic.atlas-nodes.0087.bae912fb98170796.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0088.d95fb1dd41e19f71.js`](./nordic.atlas-nodes.0088.d95fb1dd41e19f71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0089.fb4cd019fa8f0532.js`](./nordic.atlas-nodes.0089.fb4cd019fa8f0532.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0090.a29caf1e01d4ce44.js`](./nordic.atlas-nodes.0090.a29caf1e01d4ce44.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0091.04c29a001a27a9cd.js`](./nordic.atlas-nodes.0091.04c29a001a27a9cd.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0092.6593de6266acf013.js`](./nordic.atlas-nodes.0092.6593de6266acf013.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0093.8fa8c2d793f83e63.js`](./nordic.atlas-nodes.0093.8fa8c2d793f83e63.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0094.ee4b7d85a18c030e.js`](./nordic.atlas-nodes.0094.ee4b7d85a18c030e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0095.46e871141edc198d.js`](./nordic.atlas-nodes.0095.46e871141edc198d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0096.e8d4b2609b7396bb.js`](./nordic.atlas-nodes.0096.e8d4b2609b7396bb.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0097.010c4907c0100254.js`](./nordic.atlas-nodes.0097.010c4907c0100254.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0098.80795e50054670c0.js`](./nordic.atlas-nodes.0098.80795e50054670c0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0099.da98ce5b2f920a20.js`](./nordic.atlas-nodes.0099.da98ce5b2f920a20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0100.e8e48cb0210a905b.js`](./nordic.atlas-nodes.0100.e8e48cb0210a905b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0101.b8d729e38da6f01c.js`](./nordic.atlas-nodes.0101.b8d729e38da6f01c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0102.33d0a643528bc38a.js`](./nordic.atlas-nodes.0102.33d0a643528bc38a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0103.0dd95fab90d360e0.js`](./nordic.atlas-nodes.0103.0dd95fab90d360e0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0104.d681cfd6d2ecbcf8.js`](./nordic.atlas-nodes.0104.d681cfd6d2ecbcf8.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0105.5709947b2bb22016.js`](./nordic.atlas-nodes.0105.5709947b2bb22016.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0106.8f5ed6b40c8a1f93.js`](./nordic.atlas-nodes.0106.8f5ed6b40c8a1f93.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0107.9de2f71774d0898c.js`](./nordic.atlas-nodes.0107.9de2f71774d0898c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0108.3e7398d22a9b758c.js`](./nordic.atlas-nodes.0108.3e7398d22a9b758c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0109.bf4c8f7b19ca2825.js`](./nordic.atlas-nodes.0109.bf4c8f7b19ca2825.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0110.cb445adaa0558a30.js`](./nordic.atlas-nodes.0110.cb445adaa0558a30.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0111.c05178276c159306.js`](./nordic.atlas-nodes.0111.c05178276c159306.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0112.4d117efc91b8cd2b.js`](./nordic.atlas-nodes.0112.4d117efc91b8cd2b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0113.c4d5421b110c8fc5.js`](./nordic.atlas-nodes.0113.c4d5421b110c8fc5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0114.269a230446d0efb0.js`](./nordic.atlas-nodes.0114.269a230446d0efb0.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0115.1861ea2681707271.js`](./nordic.atlas-nodes.0115.1861ea2681707271.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0116.7d243f8699e6831d.js`](./nordic.atlas-nodes.0116.7d243f8699e6831d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0117.eb0fbc4b90d9e32b.js`](./nordic.atlas-nodes.0117.eb0fbc4b90d9e32b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0118.7539ebdd061ab07a.js`](./nordic.atlas-nodes.0118.7539ebdd061ab07a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0119.f988ea0d93192c0e.js`](./nordic.atlas-nodes.0119.f988ea0d93192c0e.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0120.b4d722e3b0996a70.js`](./nordic.atlas-nodes.0120.b4d722e3b0996a70.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0121.460a8ea4c8efcf13.js`](./nordic.atlas-nodes.0121.460a8ea4c8efcf13.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0122.052f23c55c43ac31.js`](./nordic.atlas-nodes.0122.052f23c55c43ac31.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0123.114fc1a70ccc4804.js`](./nordic.atlas-nodes.0123.114fc1a70ccc4804.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0124.15d65be927eafbc6.js`](./nordic.atlas-nodes.0124.15d65be927eafbc6.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0125.87f5d6eeed529a47.js`](./nordic.atlas-nodes.0125.87f5d6eeed529a47.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0126.d12ea5013c439141.js`](./nordic.atlas-nodes.0126.d12ea5013c439141.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0127.e53cb24366ba4c2a.js`](./nordic.atlas-nodes.0127.e53cb24366ba4c2a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0128.e2ba24a489cfac66.js`](./nordic.atlas-nodes.0128.e2ba24a489cfac66.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0129.91344efc8bd0f0c3.js`](./nordic.atlas-nodes.0129.91344efc8bd0f0c3.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0130.d407527faedbaa3b.js`](./nordic.atlas-nodes.0130.d407527faedbaa3b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0131.b19762529b081c7a.js`](./nordic.atlas-nodes.0131.b19762529b081c7a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0132.7c353575e16f3803.js`](./nordic.atlas-nodes.0132.7c353575e16f3803.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0133.2de92a04ecdcbd0c.js`](./nordic.atlas-nodes.0133.2de92a04ecdcbd0c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0134.89081851f13863df.js`](./nordic.atlas-nodes.0134.89081851f13863df.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0135.1e6563cdb175f9cc.js`](./nordic.atlas-nodes.0135.1e6563cdb175f9cc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0136.37f7465442a15a9a.js`](./nordic.atlas-nodes.0136.37f7465442a15a9a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0137.7e1493057b42c43f.js`](./nordic.atlas-nodes.0137.7e1493057b42c43f.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0138.fc0eb3af9d924895.js`](./nordic.atlas-nodes.0138.fc0eb3af9d924895.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0139.52c6e0eaf01ea977.js`](./nordic.atlas-nodes.0139.52c6e0eaf01ea977.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0140.1e8816c469af9c8a.js`](./nordic.atlas-nodes.0140.1e8816c469af9c8a.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0141.175a981a10d2ae93.js`](./nordic.atlas-nodes.0141.175a981a10d2ae93.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0142.96edb02177618cd2.js`](./nordic.atlas-nodes.0142.96edb02177618cd2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0143.427b8cbfc8669fa7.js`](./nordic.atlas-nodes.0143.427b8cbfc8669fa7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0144.1f221109ba864bcc.js`](./nordic.atlas-nodes.0144.1f221109ba864bcc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0145.9989530c03183948.js`](./nordic.atlas-nodes.0145.9989530c03183948.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0146.a60a9e5c5d2d33cf.js`](./nordic.atlas-nodes.0146.a60a9e5c5d2d33cf.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0147.577a4059687a81b2.js`](./nordic.atlas-nodes.0147.577a4059687a81b2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0148.f26a8e1c3455933d.js`](./nordic.atlas-nodes.0148.f26a8e1c3455933d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0149.1cc21d16534df734.js`](./nordic.atlas-nodes.0149.1cc21d16534df734.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0150.a6f0f0ff6be1008d.js`](./nordic.atlas-nodes.0150.a6f0f0ff6be1008d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0151.e62d81b688577d60.js`](./nordic.atlas-nodes.0151.e62d81b688577d60.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0152.7a57f06b65665403.js`](./nordic.atlas-nodes.0152.7a57f06b65665403.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0153.da0dd0491f92d8ed.js`](./nordic.atlas-nodes.0153.da0dd0491f92d8ed.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0154.f3be8df628258fa5.js`](./nordic.atlas-nodes.0154.f3be8df628258fa5.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0155.dfebb1390f3a2857.js`](./nordic.atlas-nodes.0155.dfebb1390f3a2857.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0156.9ca035ab044e7b6d.js`](./nordic.atlas-nodes.0156.9ca035ab044e7b6d.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0157.cf4e1250479d1d20.js`](./nordic.atlas-nodes.0157.cf4e1250479d1d20.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0158.41130c4c50eb3555.js`](./nordic.atlas-nodes.0158.41130c4c50eb3555.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0159.98f0dd875c435ed2.js`](./nordic.atlas-nodes.0159.98f0dd875c435ed2.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0160.edde205a64ad6cad.js`](./nordic.atlas-nodes.0160.edde205a64ad6cad.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0161.1a495b83eeaf8f71.js`](./nordic.atlas-nodes.0161.1a495b83eeaf8f71.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0162.727047df31504ede.js`](./nordic.atlas-nodes.0162.727047df31504ede.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0163.d5ab3988c6c5e94c.js`](./nordic.atlas-nodes.0163.d5ab3988c6c5e94c.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0164.ddb45b83c9d713bc.js`](./nordic.atlas-nodes.0164.ddb45b83c9d713bc.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0165.ed7d4a52244ea7f7.js`](./nordic.atlas-nodes.0165.ed7d4a52244ea7f7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0166.b2c4ce8da9a3a25b.js`](./nordic.atlas-nodes.0166.b2c4ce8da9a3a25b.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0167.3f94696e775aa8ca.js`](./nordic.atlas-nodes.0167.3f94696e775aa8ca.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0168.add0d856f3951703.js`](./nordic.atlas-nodes.0168.add0d856f3951703.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0169.59f03a96123093b7.js`](./nordic.atlas-nodes.0169.59f03a96123093b7.js)
- Static atlas data chunk: [`nordic.atlas-nodes.0170.6366c2357f728619.js`](./nordic.atlas-nodes.0170.6366c2357f728619.js)
- Static atlas data chunk: [`nordic.atlas-details.0171.39e1fb033755fd60.js`](./nordic.atlas-details.0171.39e1fb033755fd60.js)
- Static atlas data chunk: [`nordic.atlas-details.0172.f9c1e896c81befa7.js`](./nordic.atlas-details.0172.f9c1e896c81befa7.js)
- Static atlas data chunk: [`nordic.atlas-details.0173.167d5b1754acb4e7.js`](./nordic.atlas-details.0173.167d5b1754acb4e7.js)
- Static atlas data chunk: [`nordic.atlas-details.0174.0687abd2fe07ba4b.js`](./nordic.atlas-details.0174.0687abd2fe07ba4b.js)
- Static atlas data chunk: [`nordic.atlas-details.0175.edcd4cf4ccc39028.js`](./nordic.atlas-details.0175.edcd4cf4ccc39028.js)
- Static atlas data chunk: [`nordic.atlas-details.0176.c1bad3ca5c793ba5.js`](./nordic.atlas-details.0176.c1bad3ca5c793ba5.js)
- Static atlas data chunk: [`nordic.atlas-details.0177.8d6792d3ad8fb692.js`](./nordic.atlas-details.0177.8d6792d3ad8fb692.js)
- Static atlas data chunk: [`nordic.atlas-details.0178.020c26071dd29ce0.js`](./nordic.atlas-details.0178.020c26071dd29ce0.js)
- Static atlas data chunk: [`nordic.atlas-details.0179.a413e74ca4129776.js`](./nordic.atlas-details.0179.a413e74ca4129776.js)
- Static atlas data chunk: [`nordic.atlas-details.0180.02240088e26969a9.js`](./nordic.atlas-details.0180.02240088e26969a9.js)
- Static atlas data chunk: [`nordic.atlas-details.0181.f60ef134f345da05.js`](./nordic.atlas-details.0181.f60ef134f345da05.js)
- Static atlas data chunk: [`nordic.atlas-details.0182.01e5be34418d2ba3.js`](./nordic.atlas-details.0182.01e5be34418d2ba3.js)
- Static atlas data chunk: [`nordic.atlas-details.0183.e726d9597de0fffd.js`](./nordic.atlas-details.0183.e726d9597de0fffd.js)
- Static atlas data chunk: [`nordic.atlas-details.0184.566d29c2da7507ea.js`](./nordic.atlas-details.0184.566d29c2da7507ea.js)
- Static atlas data chunk: [`nordic.atlas-details.0185.a61c623d56d7a023.js`](./nordic.atlas-details.0185.a61c623d56d7a023.js)
- Static atlas data chunk: [`nordic.atlas-details.0186.1d4ac7cab82c3b6f.js`](./nordic.atlas-details.0186.1d4ac7cab82c3b6f.js)
- Static atlas data chunk: [`nordic.atlas-details.0187.a807c9aaaf7793b6.js`](./nordic.atlas-details.0187.a807c9aaaf7793b6.js)
- Static atlas data chunk: [`nordic.atlas-details.0188.00f5148ce4dac455.js`](./nordic.atlas-details.0188.00f5148ce4dac455.js)
- Static atlas data chunk: [`nordic.atlas-details.0189.7ab6311f11c4a302.js`](./nordic.atlas-details.0189.7ab6311f11c4a302.js)
- Static atlas data chunk: [`nordic.atlas-details.0190.560b0018750a0637.js`](./nordic.atlas-details.0190.560b0018750a0637.js)
- Static atlas data chunk: [`nordic.atlas-details.0191.d0b017c5b32c5278.js`](./nordic.atlas-details.0191.d0b017c5b32c5278.js)
- Static atlas data chunk: [`nordic.atlas-details.0192.8d504ebdf2650364.js`](./nordic.atlas-details.0192.8d504ebdf2650364.js)
- Static atlas data chunk: [`nordic.atlas-details.0193.14aab70dbaa523bd.js`](./nordic.atlas-details.0193.14aab70dbaa523bd.js)
- Static atlas data chunk: [`nordic.atlas-details.0194.111c7173b0fd593e.js`](./nordic.atlas-details.0194.111c7173b0fd593e.js)
- Static atlas data chunk: [`nordic.atlas-details.0195.e254d687f539549c.js`](./nordic.atlas-details.0195.e254d687f539549c.js)
- Static atlas data chunk: [`nordic.atlas-details.0196.364d014213835392.js`](./nordic.atlas-details.0196.364d014213835392.js)
- Static atlas data chunk: [`nordic.atlas-details.0197.1a303dd7827b796b.js`](./nordic.atlas-details.0197.1a303dd7827b796b.js)
- Static atlas data chunk: [`nordic.atlas-details.0198.7a0bb563c2d793cf.js`](./nordic.atlas-details.0198.7a0bb563c2d793cf.js)
- Static atlas data chunk: [`nordic.atlas-details.0199.949c186aee7d5a4a.js`](./nordic.atlas-details.0199.949c186aee7d5a4a.js)
- Static atlas data chunk: [`nordic.atlas-details.0200.cca9020288b54170.js`](./nordic.atlas-details.0200.cca9020288b54170.js)
- Static atlas data chunk: [`nordic.atlas-details.0201.b5fd1f0b553c4586.js`](./nordic.atlas-details.0201.b5fd1f0b553c4586.js)
- Static atlas data chunk: [`nordic.atlas-details.0202.c8483196bb2ad8b0.js`](./nordic.atlas-details.0202.c8483196bb2ad8b0.js)
- Static atlas data chunk: [`nordic.atlas-details.0203.ad88b0e3c5709ebd.js`](./nordic.atlas-details.0203.ad88b0e3c5709ebd.js)
- Static atlas data chunk: [`nordic.atlas-details.0204.f40253d2e3a8b91d.js`](./nordic.atlas-details.0204.f40253d2e3a8b91d.js)
- Static atlas data chunk: [`nordic.atlas-details.0205.509fd8fcb2b39b1b.js`](./nordic.atlas-details.0205.509fd8fcb2b39b1b.js)
- Static atlas data chunk: [`nordic.atlas-details.0206.d291d683a4577efb.js`](./nordic.atlas-details.0206.d291d683a4577efb.js)
- Static atlas data chunk: [`nordic.atlas-details.0207.b222f88bc1080f6b.js`](./nordic.atlas-details.0207.b222f88bc1080f6b.js)
- Static atlas data chunk: [`nordic.atlas-details.0208.8c6d2469bb8a4e12.js`](./nordic.atlas-details.0208.8c6d2469bb8a4e12.js)
- Static atlas data chunk: [`nordic.atlas-details.0209.b9f491bbb8cad367.js`](./nordic.atlas-details.0209.b9f491bbb8cad367.js)
- Static atlas data chunk: [`nordic.atlas-details.0210.fca47b035315a803.js`](./nordic.atlas-details.0210.fca47b035315a803.js)
- Static atlas data chunk: [`nordic.atlas-details.0211.214088f5707a61a5.js`](./nordic.atlas-details.0211.214088f5707a61a5.js)
- Static atlas data chunk: [`nordic.atlas-details.0212.b005ca7228fbf08b.js`](./nordic.atlas-details.0212.b005ca7228fbf08b.js)
- Static atlas data chunk: [`nordic.atlas-details.0213.2a86e6b1c2f335a3.js`](./nordic.atlas-details.0213.2a86e6b1c2f335a3.js)
- Static atlas data chunk: [`nordic.atlas-details.0214.af29dc0c130ddb7c.js`](./nordic.atlas-details.0214.af29dc0c130ddb7c.js)
- Static atlas data chunk: [`nordic.atlas-details.0215.4472328d6d8abbee.js`](./nordic.atlas-details.0215.4472328d6d8abbee.js)
- Static atlas data chunk: [`nordic.atlas-details.0216.c6cfec1620f9b3f6.js`](./nordic.atlas-details.0216.c6cfec1620f9b3f6.js)
- Static atlas data chunk: [`nordic.atlas-details.0217.d2e347fe462f436c.js`](./nordic.atlas-details.0217.d2e347fe462f436c.js)
- Static atlas data chunk: [`nordic.atlas-details.0218.c76601c8356716d8.js`](./nordic.atlas-details.0218.c76601c8356716d8.js)
- Static atlas data chunk: [`nordic.atlas-details.0219.f792b69ae0620a04.js`](./nordic.atlas-details.0219.f792b69ae0620a04.js)
- Static atlas data chunk: [`nordic.atlas-details.0220.c3009d222c15c60c.js`](./nordic.atlas-details.0220.c3009d222c15c60c.js)
- Static atlas data chunk: [`nordic.atlas-details.0221.95079c3324ec9d83.js`](./nordic.atlas-details.0221.95079c3324ec9d83.js)
- Static atlas data chunk: [`nordic.atlas-details.0222.8de012187dec9d86.js`](./nordic.atlas-details.0222.8de012187dec9d86.js)
- Static atlas data chunk: [`nordic.atlas-details.0223.c88cb04784f65c7e.js`](./nordic.atlas-details.0223.c88cb04784f65c7e.js)
- Static atlas data chunk: [`nordic.atlas-details.0224.a77ff14b7c73c4a4.js`](./nordic.atlas-details.0224.a77ff14b7c73c4a4.js)
- Static atlas data chunk: [`nordic.atlas-details.0225.67cf0ed213ac759e.js`](./nordic.atlas-details.0225.67cf0ed213ac759e.js)
- Static atlas data chunk: [`nordic.atlas-details.0226.45f4ac596c345fb9.js`](./nordic.atlas-details.0226.45f4ac596c345fb9.js)
- Static atlas data chunk: [`nordic.atlas-details.0227.6a760911f364d4d5.js`](./nordic.atlas-details.0227.6a760911f364d4d5.js)
- Static atlas data chunk: [`nordic.atlas-details.0228.cea3b49c08b761af.js`](./nordic.atlas-details.0228.cea3b49c08b761af.js)
- Static atlas data chunk: [`nordic.atlas-details.0229.24a6f4f525bdf965.js`](./nordic.atlas-details.0229.24a6f4f525bdf965.js)
- Static atlas data chunk: [`nordic.atlas-details.0230.967219e76a2aeec6.js`](./nordic.atlas-details.0230.967219e76a2aeec6.js)
- Static atlas data chunk: [`nordic.atlas-details.0231.ba164a04f0b773a1.js`](./nordic.atlas-details.0231.ba164a04f0b773a1.js)
- Static atlas data chunk: [`nordic.atlas-details.0232.c6ac663ad0cfd730.js`](./nordic.atlas-details.0232.c6ac663ad0cfd730.js)
- Static atlas data chunk: [`nordic.atlas-details.0233.2f77152efeceed25.js`](./nordic.atlas-details.0233.2f77152efeceed25.js)
- Static atlas data chunk: [`nordic.atlas-details.0234.f7efba7c38e2cec6.js`](./nordic.atlas-details.0234.f7efba7c38e2cec6.js)
- Static atlas data chunk: [`nordic.atlas-edges.0235.d445c71a9ce2b2fc.js`](./nordic.atlas-edges.0235.d445c71a9ce2b2fc.js)
- Static atlas data chunk: [`nordic.atlas-sequences.0236.589074324a9448b9.js`](./nordic.atlas-sequences.0236.589074324a9448b9.js)
- Static atlas data chunk: [`nordic.atlas-indexes.0237.9eeb35121a70dd9a.js`](./nordic.atlas-indexes.0237.9eeb35121a70dd9a.js)
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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/country-evidence-status.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/country-evidence-status.md) (source SHA-256 `b07462b1cd31fae284b29d0b6319ac5fbfcadd0e9eabb35ab290240f0818ae3e`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/animal-entity-capability/README.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/animal-entity-capability/README.md) (source SHA-256 `3a0a899e96cfe7d95bdef41012516f39ce2b68606212efecafe1d909b6ccd045`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

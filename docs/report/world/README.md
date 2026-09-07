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
- Static atlas data chunk: [`world.atlas-provenance.0000.4ae0f0704e587357.js`](./world.atlas-provenance.0000.4ae0f0704e587357.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.114f98d7b43a1ab0.js`](./world.atlas-nodes.0001.114f98d7b43a1ab0.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.611d10bbc4fb35bd.js`](./world.atlas-nodes.0002.611d10bbc4fb35bd.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.3ba4cf8d51bd37e2.js`](./world.atlas-nodes.0003.3ba4cf8d51bd37e2.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.433b48ef55b1cc94.js`](./world.atlas-nodes.0004.433b48ef55b1cc94.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.9d532798641060a5.js`](./world.atlas-nodes.0005.9d532798641060a5.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.28105c963699d08a.js`](./world.atlas-nodes.0006.28105c963699d08a.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.350a52f911b988bd.js`](./world.atlas-nodes.0007.350a52f911b988bd.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.d9714759860a9d11.js`](./world.atlas-nodes.0008.d9714759860a9d11.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.97b593f9008d434c.js`](./world.atlas-nodes.0009.97b593f9008d434c.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.852777ecad3b024e.js`](./world.atlas-nodes.0010.852777ecad3b024e.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.af83978f1982f3e2.js`](./world.atlas-nodes.0011.af83978f1982f3e2.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.265b916677772643.js`](./world.atlas-nodes.0012.265b916677772643.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.18b364a03b1ead70.js`](./world.atlas-nodes.0013.18b364a03b1ead70.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.e67643eebae147ab.js`](./world.atlas-nodes.0014.e67643eebae147ab.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.40e3733ea3db3f08.js`](./world.atlas-nodes.0015.40e3733ea3db3f08.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.d853f3ba2c05efc5.js`](./world.atlas-nodes.0016.d853f3ba2c05efc5.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.8a57baa770adcdf4.js`](./world.atlas-nodes.0017.8a57baa770adcdf4.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.7ce4e1330f462caa.js`](./world.atlas-nodes.0018.7ce4e1330f462caa.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.6e1b1be803039142.js`](./world.atlas-nodes.0019.6e1b1be803039142.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.fa0b6c1336e27940.js`](./world.atlas-nodes.0020.fa0b6c1336e27940.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.4b740187116cfc12.js`](./world.atlas-nodes.0021.4b740187116cfc12.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.e42c833ac5635ba9.js`](./world.atlas-nodes.0022.e42c833ac5635ba9.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.ca26418a6f1b867b.js`](./world.atlas-nodes.0023.ca26418a6f1b867b.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.a20a88d05f343ead.js`](./world.atlas-nodes.0024.a20a88d05f343ead.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.ea22d47a62a49385.js`](./world.atlas-nodes.0025.ea22d47a62a49385.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.30c334ce5b03fb6a.js`](./world.atlas-nodes.0026.30c334ce5b03fb6a.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.a33db550d29bb553.js`](./world.atlas-nodes.0027.a33db550d29bb553.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.5618096146d5ea41.js`](./world.atlas-nodes.0028.5618096146d5ea41.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.9616438a916e4e71.js`](./world.atlas-nodes.0029.9616438a916e4e71.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.76ed3ee32118ff70.js`](./world.atlas-nodes.0030.76ed3ee32118ff70.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.0a94f0c8184e91b4.js`](./world.atlas-nodes.0031.0a94f0c8184e91b4.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.f45401a94d0fbacf.js`](./world.atlas-nodes.0032.f45401a94d0fbacf.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.3a35f437810737e0.js`](./world.atlas-nodes.0033.3a35f437810737e0.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.9cdf1d31abdecf41.js`](./world.atlas-nodes.0034.9cdf1d31abdecf41.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.49bfd71131df3514.js`](./world.atlas-nodes.0035.49bfd71131df3514.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.d00380b62eff97ed.js`](./world.atlas-nodes.0036.d00380b62eff97ed.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.b740bc565ed8ab69.js`](./world.atlas-nodes.0037.b740bc565ed8ab69.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.7ecba311bfde9c67.js`](./world.atlas-nodes.0038.7ecba311bfde9c67.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.e513af8f456aa29b.js`](./world.atlas-nodes.0039.e513af8f456aa29b.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.359564fdd0adccc0.js`](./world.atlas-nodes.0040.359564fdd0adccc0.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.71b9aae6dbaec78d.js`](./world.atlas-nodes.0041.71b9aae6dbaec78d.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.81ea310c8d1fb9a1.js`](./world.atlas-nodes.0042.81ea310c8d1fb9a1.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.b95d943a4d0f74f0.js`](./world.atlas-nodes.0043.b95d943a4d0f74f0.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.cf041e478553ab21.js`](./world.atlas-nodes.0044.cf041e478553ab21.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.700f8c2d4a670342.js`](./world.atlas-nodes.0045.700f8c2d4a670342.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.387816baa3823e12.js`](./world.atlas-nodes.0046.387816baa3823e12.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.e9c21c7a589bb03d.js`](./world.atlas-nodes.0047.e9c21c7a589bb03d.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.edef34d115e4843b.js`](./world.atlas-nodes.0048.edef34d115e4843b.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.e0b141d0fbecba12.js`](./world.atlas-nodes.0049.e0b141d0fbecba12.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.6f75894248f82384.js`](./world.atlas-nodes.0050.6f75894248f82384.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.7653ce4bcfd58575.js`](./world.atlas-nodes.0051.7653ce4bcfd58575.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.e56ad2a1847def9b.js`](./world.atlas-nodes.0052.e56ad2a1847def9b.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.09e0fd74f23c9b5f.js`](./world.atlas-nodes.0053.09e0fd74f23c9b5f.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.3bd35b75af7ae522.js`](./world.atlas-nodes.0054.3bd35b75af7ae522.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.a7cf5ea3225b0d32.js`](./world.atlas-nodes.0055.a7cf5ea3225b0d32.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.1b3b20ff57a705b7.js`](./world.atlas-nodes.0056.1b3b20ff57a705b7.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.8c03251553dee072.js`](./world.atlas-nodes.0057.8c03251553dee072.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.d5065d44d5281bce.js`](./world.atlas-nodes.0058.d5065d44d5281bce.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.0308580238ed2994.js`](./world.atlas-nodes.0059.0308580238ed2994.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.7eb73256ab9d306a.js`](./world.atlas-nodes.0060.7eb73256ab9d306a.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.0a27533c58ab50ee.js`](./world.atlas-nodes.0061.0a27533c58ab50ee.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.204c50ecc1b454a0.js`](./world.atlas-nodes.0062.204c50ecc1b454a0.js)
- Static atlas data chunk: [`world.atlas-edges.0063.1c2b2b67bb986643.js`](./world.atlas-edges.0063.1c2b2b67bb986643.js)
- Static atlas data chunk: [`world.atlas-sequences.0064.7b3f13d5a22ea469.js`](./world.atlas-sequences.0064.7b3f13d5a22ea469.js)
- Static atlas data chunk: [`world.atlas-indexes.0065.b9952388556f7ddf.js`](./world.atlas-indexes.0065.b9952388556f7ddf.js)
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


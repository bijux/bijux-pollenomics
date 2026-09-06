# World Evidence Surface

This shared interactive map bundle was generated on `2026-09-06` from Homo
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
- Static atlas data chunk: [`world.atlas-provenance.0000.d9a3aacf85b03797.js`](./world.atlas-provenance.0000.d9a3aacf85b03797.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.3b179e1d71fc2589.js`](./world.atlas-nodes.0001.3b179e1d71fc2589.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.965693d55c715559.js`](./world.atlas-nodes.0002.965693d55c715559.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.249e8acfdaf04838.js`](./world.atlas-nodes.0003.249e8acfdaf04838.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.ef2d0786eb30f78e.js`](./world.atlas-nodes.0004.ef2d0786eb30f78e.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.ab906e127c3e25e8.js`](./world.atlas-nodes.0005.ab906e127c3e25e8.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.c939b3e88df218e2.js`](./world.atlas-nodes.0006.c939b3e88df218e2.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.59f8eb09049c07af.js`](./world.atlas-nodes.0007.59f8eb09049c07af.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.1932406892c2f5d7.js`](./world.atlas-nodes.0008.1932406892c2f5d7.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.4eccc47775782597.js`](./world.atlas-nodes.0009.4eccc47775782597.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.627b537f5c0eb8ba.js`](./world.atlas-nodes.0010.627b537f5c0eb8ba.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.f2898f82fc252b0b.js`](./world.atlas-nodes.0011.f2898f82fc252b0b.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.963b09c2cd957f66.js`](./world.atlas-nodes.0012.963b09c2cd957f66.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.6e72222318a6e5c5.js`](./world.atlas-nodes.0013.6e72222318a6e5c5.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.126ca5285f8ac792.js`](./world.atlas-nodes.0014.126ca5285f8ac792.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.89c6f9b2a0da49e5.js`](./world.atlas-nodes.0015.89c6f9b2a0da49e5.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.05cdf87e0868351e.js`](./world.atlas-nodes.0016.05cdf87e0868351e.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.0237aa2fa5c79aa8.js`](./world.atlas-nodes.0017.0237aa2fa5c79aa8.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.aa52fbdb01be53d3.js`](./world.atlas-nodes.0018.aa52fbdb01be53d3.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.7c8dac6dfcc68823.js`](./world.atlas-nodes.0019.7c8dac6dfcc68823.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.0637d8e0a8610acd.js`](./world.atlas-nodes.0020.0637d8e0a8610acd.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.73226c0da55566ca.js`](./world.atlas-nodes.0021.73226c0da55566ca.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.f4059ffa4493ec95.js`](./world.atlas-nodes.0022.f4059ffa4493ec95.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.3b6b54e4e5a9520e.js`](./world.atlas-nodes.0023.3b6b54e4e5a9520e.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.8a16c69dee545503.js`](./world.atlas-nodes.0024.8a16c69dee545503.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.f9846e899961d4bf.js`](./world.atlas-nodes.0025.f9846e899961d4bf.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.044c7c8a79354461.js`](./world.atlas-nodes.0026.044c7c8a79354461.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.2266e3a62c545298.js`](./world.atlas-nodes.0027.2266e3a62c545298.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.cda5919b64c2ee59.js`](./world.atlas-nodes.0028.cda5919b64c2ee59.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.55009abd97e988cd.js`](./world.atlas-nodes.0029.55009abd97e988cd.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.1125c95aefd0d4c9.js`](./world.atlas-nodes.0030.1125c95aefd0d4c9.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.db453b673717c54c.js`](./world.atlas-nodes.0031.db453b673717c54c.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.2d6141c9215430a7.js`](./world.atlas-nodes.0032.2d6141c9215430a7.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.d4edf106b71fe1cb.js`](./world.atlas-nodes.0033.d4edf106b71fe1cb.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.9016926f4175763c.js`](./world.atlas-nodes.0034.9016926f4175763c.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.87ad68f49ee9c57a.js`](./world.atlas-nodes.0035.87ad68f49ee9c57a.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.fc07e7173335445a.js`](./world.atlas-nodes.0036.fc07e7173335445a.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.5890d5e882ff224c.js`](./world.atlas-nodes.0037.5890d5e882ff224c.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.4fc8c2b606c83dd7.js`](./world.atlas-nodes.0038.4fc8c2b606c83dd7.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.c5b27930559f7ed7.js`](./world.atlas-nodes.0039.c5b27930559f7ed7.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.1d66bf57ea430734.js`](./world.atlas-nodes.0040.1d66bf57ea430734.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.cc13cba43b0ef0a7.js`](./world.atlas-nodes.0041.cc13cba43b0ef0a7.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.b4d31d916c9385a9.js`](./world.atlas-nodes.0042.b4d31d916c9385a9.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.9e614f2c39998e54.js`](./world.atlas-nodes.0043.9e614f2c39998e54.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.e5cf2b48633b8ec2.js`](./world.atlas-nodes.0044.e5cf2b48633b8ec2.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.bfb5b196bb10158c.js`](./world.atlas-nodes.0045.bfb5b196bb10158c.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.307f01a6f3bce378.js`](./world.atlas-nodes.0046.307f01a6f3bce378.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.7cc5f2efe6762b70.js`](./world.atlas-nodes.0047.7cc5f2efe6762b70.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.9bda447100021ee5.js`](./world.atlas-nodes.0048.9bda447100021ee5.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.85dd47d92df73b60.js`](./world.atlas-nodes.0049.85dd47d92df73b60.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.24ad70d2cc17d236.js`](./world.atlas-nodes.0050.24ad70d2cc17d236.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.3b39ccfa5445bfa9.js`](./world.atlas-nodes.0051.3b39ccfa5445bfa9.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.ea91c99235aac2a8.js`](./world.atlas-nodes.0052.ea91c99235aac2a8.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.bdf8fb6c9e5a7489.js`](./world.atlas-nodes.0053.bdf8fb6c9e5a7489.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.2f51c814cce9f213.js`](./world.atlas-nodes.0054.2f51c814cce9f213.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.9fa59b356cb846d3.js`](./world.atlas-nodes.0055.9fa59b356cb846d3.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.8124ec0113c99c08.js`](./world.atlas-nodes.0056.8124ec0113c99c08.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.6e4e5dc88dd009ab.js`](./world.atlas-nodes.0057.6e4e5dc88dd009ab.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.3df808287cb24793.js`](./world.atlas-nodes.0058.3df808287cb24793.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.fbf5b2488ace870f.js`](./world.atlas-nodes.0059.fbf5b2488ace870f.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.d134a92de7f6fe86.js`](./world.atlas-nodes.0060.d134a92de7f6fe86.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.ec8cc67e6dc7dae7.js`](./world.atlas-nodes.0061.ec8cc67e6dc7dae7.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.59674dd184c8b356.js`](./world.atlas-nodes.0062.59674dd184c8b356.js)
- Static atlas data chunk: [`world.atlas-edges.0063.143cd8cae34064d1.js`](./world.atlas-edges.0063.143cd8cae34064d1.js)
- Static atlas data chunk: [`world.atlas-sequences.0064.9e50856539b22799.js`](./world.atlas-sequences.0064.9e50856539b22799.js)
- Static atlas data chunk: [`world.atlas-indexes.0065.a1b29dd97479c7ad.js`](./world.atlas-indexes.0065.a1b29dd97479c7ad.js)
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


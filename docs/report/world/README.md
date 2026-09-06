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
- Static atlas data chunk: [`world.atlas-provenance.0000.8935d27b4afa4e41.js`](./world.atlas-provenance.0000.8935d27b4afa4e41.js)
- Static atlas data chunk: [`world.atlas-nodes.0001.2c693cacaa810582.js`](./world.atlas-nodes.0001.2c693cacaa810582.js)
- Static atlas data chunk: [`world.atlas-nodes.0002.869c00e10380907e.js`](./world.atlas-nodes.0002.869c00e10380907e.js)
- Static atlas data chunk: [`world.atlas-nodes.0003.54ea8459fb3f469c.js`](./world.atlas-nodes.0003.54ea8459fb3f469c.js)
- Static atlas data chunk: [`world.atlas-nodes.0004.215e4d73adc164c2.js`](./world.atlas-nodes.0004.215e4d73adc164c2.js)
- Static atlas data chunk: [`world.atlas-nodes.0005.da1da3c8240c5546.js`](./world.atlas-nodes.0005.da1da3c8240c5546.js)
- Static atlas data chunk: [`world.atlas-nodes.0006.227afaa1aa88ce18.js`](./world.atlas-nodes.0006.227afaa1aa88ce18.js)
- Static atlas data chunk: [`world.atlas-nodes.0007.83c80f8e84d5db34.js`](./world.atlas-nodes.0007.83c80f8e84d5db34.js)
- Static atlas data chunk: [`world.atlas-nodes.0008.d8285d982bf34814.js`](./world.atlas-nodes.0008.d8285d982bf34814.js)
- Static atlas data chunk: [`world.atlas-nodes.0009.9ddc6432de329c00.js`](./world.atlas-nodes.0009.9ddc6432de329c00.js)
- Static atlas data chunk: [`world.atlas-nodes.0010.278d2fdf55d201fd.js`](./world.atlas-nodes.0010.278d2fdf55d201fd.js)
- Static atlas data chunk: [`world.atlas-nodes.0011.0f25289c6d18325a.js`](./world.atlas-nodes.0011.0f25289c6d18325a.js)
- Static atlas data chunk: [`world.atlas-nodes.0012.9baf80085cc1d640.js`](./world.atlas-nodes.0012.9baf80085cc1d640.js)
- Static atlas data chunk: [`world.atlas-nodes.0013.329f279a9b1f38db.js`](./world.atlas-nodes.0013.329f279a9b1f38db.js)
- Static atlas data chunk: [`world.atlas-nodes.0014.1a45bb820a57e45b.js`](./world.atlas-nodes.0014.1a45bb820a57e45b.js)
- Static atlas data chunk: [`world.atlas-nodes.0015.c4dc632e3731c8e9.js`](./world.atlas-nodes.0015.c4dc632e3731c8e9.js)
- Static atlas data chunk: [`world.atlas-nodes.0016.98c5ab8150421df1.js`](./world.atlas-nodes.0016.98c5ab8150421df1.js)
- Static atlas data chunk: [`world.atlas-nodes.0017.7b59a746b3bec185.js`](./world.atlas-nodes.0017.7b59a746b3bec185.js)
- Static atlas data chunk: [`world.atlas-nodes.0018.28a929955b9f4ede.js`](./world.atlas-nodes.0018.28a929955b9f4ede.js)
- Static atlas data chunk: [`world.atlas-nodes.0019.75c71ae38d9515c3.js`](./world.atlas-nodes.0019.75c71ae38d9515c3.js)
- Static atlas data chunk: [`world.atlas-nodes.0020.967ebc96741fe213.js`](./world.atlas-nodes.0020.967ebc96741fe213.js)
- Static atlas data chunk: [`world.atlas-nodes.0021.9f9b26f31f891376.js`](./world.atlas-nodes.0021.9f9b26f31f891376.js)
- Static atlas data chunk: [`world.atlas-nodes.0022.c8fdcac74de2455b.js`](./world.atlas-nodes.0022.c8fdcac74de2455b.js)
- Static atlas data chunk: [`world.atlas-nodes.0023.9e959563f0d73b9f.js`](./world.atlas-nodes.0023.9e959563f0d73b9f.js)
- Static atlas data chunk: [`world.atlas-nodes.0024.681d5a12ae02942f.js`](./world.atlas-nodes.0024.681d5a12ae02942f.js)
- Static atlas data chunk: [`world.atlas-nodes.0025.a2c4fdd356425198.js`](./world.atlas-nodes.0025.a2c4fdd356425198.js)
- Static atlas data chunk: [`world.atlas-nodes.0026.d639c8d5d1e0099b.js`](./world.atlas-nodes.0026.d639c8d5d1e0099b.js)
- Static atlas data chunk: [`world.atlas-nodes.0027.3daccd469f129be5.js`](./world.atlas-nodes.0027.3daccd469f129be5.js)
- Static atlas data chunk: [`world.atlas-nodes.0028.03fc2e90c98fdfd6.js`](./world.atlas-nodes.0028.03fc2e90c98fdfd6.js)
- Static atlas data chunk: [`world.atlas-nodes.0029.86020d9c4e1ddd52.js`](./world.atlas-nodes.0029.86020d9c4e1ddd52.js)
- Static atlas data chunk: [`world.atlas-nodes.0030.e71f0e930c2c0e52.js`](./world.atlas-nodes.0030.e71f0e930c2c0e52.js)
- Static atlas data chunk: [`world.atlas-nodes.0031.a5cd90fdb2f8f4dc.js`](./world.atlas-nodes.0031.a5cd90fdb2f8f4dc.js)
- Static atlas data chunk: [`world.atlas-nodes.0032.892119ed3cde154b.js`](./world.atlas-nodes.0032.892119ed3cde154b.js)
- Static atlas data chunk: [`world.atlas-nodes.0033.30ce51a97735607e.js`](./world.atlas-nodes.0033.30ce51a97735607e.js)
- Static atlas data chunk: [`world.atlas-nodes.0034.56aad8c3ebb3b66b.js`](./world.atlas-nodes.0034.56aad8c3ebb3b66b.js)
- Static atlas data chunk: [`world.atlas-nodes.0035.b697681c92a6082d.js`](./world.atlas-nodes.0035.b697681c92a6082d.js)
- Static atlas data chunk: [`world.atlas-nodes.0036.346fb7eedb0a6e83.js`](./world.atlas-nodes.0036.346fb7eedb0a6e83.js)
- Static atlas data chunk: [`world.atlas-nodes.0037.bc50e04aac577b40.js`](./world.atlas-nodes.0037.bc50e04aac577b40.js)
- Static atlas data chunk: [`world.atlas-nodes.0038.3de1799133c52bd5.js`](./world.atlas-nodes.0038.3de1799133c52bd5.js)
- Static atlas data chunk: [`world.atlas-nodes.0039.4f9e4fdd2f132fec.js`](./world.atlas-nodes.0039.4f9e4fdd2f132fec.js)
- Static atlas data chunk: [`world.atlas-nodes.0040.30c60976bab2a519.js`](./world.atlas-nodes.0040.30c60976bab2a519.js)
- Static atlas data chunk: [`world.atlas-nodes.0041.e576dc018629cb12.js`](./world.atlas-nodes.0041.e576dc018629cb12.js)
- Static atlas data chunk: [`world.atlas-nodes.0042.caf64e114e40835d.js`](./world.atlas-nodes.0042.caf64e114e40835d.js)
- Static atlas data chunk: [`world.atlas-nodes.0043.0ea2fbca4cf638a0.js`](./world.atlas-nodes.0043.0ea2fbca4cf638a0.js)
- Static atlas data chunk: [`world.atlas-nodes.0044.1b21f52e25cb0f52.js`](./world.atlas-nodes.0044.1b21f52e25cb0f52.js)
- Static atlas data chunk: [`world.atlas-nodes.0045.92aafaf26b55a68b.js`](./world.atlas-nodes.0045.92aafaf26b55a68b.js)
- Static atlas data chunk: [`world.atlas-nodes.0046.252983735ab6f87f.js`](./world.atlas-nodes.0046.252983735ab6f87f.js)
- Static atlas data chunk: [`world.atlas-nodes.0047.1e4a08be7c923202.js`](./world.atlas-nodes.0047.1e4a08be7c923202.js)
- Static atlas data chunk: [`world.atlas-nodes.0048.ff74e6294071c3da.js`](./world.atlas-nodes.0048.ff74e6294071c3da.js)
- Static atlas data chunk: [`world.atlas-nodes.0049.aa5964d405e846e4.js`](./world.atlas-nodes.0049.aa5964d405e846e4.js)
- Static atlas data chunk: [`world.atlas-nodes.0050.afbeaca2488588a3.js`](./world.atlas-nodes.0050.afbeaca2488588a3.js)
- Static atlas data chunk: [`world.atlas-nodes.0051.bcc5ea7ba35799d0.js`](./world.atlas-nodes.0051.bcc5ea7ba35799d0.js)
- Static atlas data chunk: [`world.atlas-nodes.0052.c6f6c7af11ecb72d.js`](./world.atlas-nodes.0052.c6f6c7af11ecb72d.js)
- Static atlas data chunk: [`world.atlas-nodes.0053.a4570048efd0fc5f.js`](./world.atlas-nodes.0053.a4570048efd0fc5f.js)
- Static atlas data chunk: [`world.atlas-nodes.0054.68dc841176bf34a3.js`](./world.atlas-nodes.0054.68dc841176bf34a3.js)
- Static atlas data chunk: [`world.atlas-nodes.0055.991570911d760793.js`](./world.atlas-nodes.0055.991570911d760793.js)
- Static atlas data chunk: [`world.atlas-nodes.0056.9944bda0a7c91270.js`](./world.atlas-nodes.0056.9944bda0a7c91270.js)
- Static atlas data chunk: [`world.atlas-nodes.0057.def3dbc31e09babe.js`](./world.atlas-nodes.0057.def3dbc31e09babe.js)
- Static atlas data chunk: [`world.atlas-nodes.0058.1d26f3694b061160.js`](./world.atlas-nodes.0058.1d26f3694b061160.js)
- Static atlas data chunk: [`world.atlas-nodes.0059.15aa20f510f44acd.js`](./world.atlas-nodes.0059.15aa20f510f44acd.js)
- Static atlas data chunk: [`world.atlas-nodes.0060.ea247aa625578550.js`](./world.atlas-nodes.0060.ea247aa625578550.js)
- Static atlas data chunk: [`world.atlas-nodes.0061.3911b605c8525f7c.js`](./world.atlas-nodes.0061.3911b605c8525f7c.js)
- Static atlas data chunk: [`world.atlas-nodes.0062.0da2b1c114a0c0e8.js`](./world.atlas-nodes.0062.0da2b1c114a0c0e8.js)
- Static atlas data chunk: [`world.atlas-edges.0063.03e5591d6c3484ff.js`](./world.atlas-edges.0063.03e5591d6c3484ff.js)
- Static atlas data chunk: [`world.atlas-sequences.0064.5804b9d74ad26395.js`](./world.atlas-sequences.0064.5804b9d74ad26395.js)
- Static atlas data chunk: [`world.atlas-indexes.0065.66baef36408d6cc9.js`](./world.atlas-indexes.0065.66baef36408d6cc9.js)
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


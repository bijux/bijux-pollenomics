# Nordic Evidence Atlas

This shared interactive map bundle was generated on `2026-05-07`.
It combines mapped Homo sapiens aDNA records from AADR `v66` with whichever contextual datasets are present in the repository at generation time and copies those derived artifacts into this directory. When the tracked data root contains mapped animal aDNA locality records, the atlas publishes them as separate domesticated-core and comparator layers with explicit filter and caveat surfaces instead of flattening them into generic context.

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
- Country sample counts in this README refer to Homo sapiens aDNA records derived from AADR. Context layers and animal aDNA review surfaces can have different geographic scope and record counts inside the map.

## Output Files

- Interactive map: [`nordic-atlas_map.html`](./nordic-atlas_map.html)
- Combined GeoJSON: [`nordic-atlas_samples.geojson`](./nordic-atlas_samples.geojson)
- Machine-readable summary: [`nordic-atlas_summary.json`](./nordic-atlas_summary.json)
- LandClim pollen site GeoJSON: [`nordic_pollen_site_sequences.geojson`](./nordic_pollen_site_sequences.geojson)
- Neotoma pollen GeoJSON: [`nordic_pollen_sites.geojson`](./nordic_pollen_sites.geojson)
- SEAD site GeoJSON: [`nordic_environmental_sites.geojson`](./nordic_environmental_sites.geojson)
- Nordic country boundaries: [`nordic_country_boundaries.geojson`](./nordic_country_boundaries.geojson)
- LandClim REVEALS grid GeoJSON: [`nordic_reveals_grid_cells.geojson`](./nordic_reveals_grid_cells.geojson)
- RAÄ archaeology layer metadata: [`sweden_archaeology_layer.json`](./sweden_archaeology_layer.json)
- RAÄ archaeology density: [`sweden_archaeology_density.geojson`](./sweden_archaeology_density.geojson)
- Animal locality GeoJSON: [`nordic-atlas_animal_localities.geojson`](./nordic-atlas_animal_localities.geojson)
- Domesticated-core animal locality GeoJSON: [`nordic-atlas_domesticated_animal_localities.geojson`](./nordic-atlas_domesticated_animal_localities.geojson)
- Comparator animal locality GeoJSON: [`nordic-atlas_comparator_animal_localities.geojson`](./nordic-atlas_comparator_animal_localities.geojson)
- Candidate site ranking CSV: [`nordic-atlas_candidate_sites.csv`](./nordic-atlas_candidate_sites.csv)
- Candidate site ranking JSON: [`nordic-atlas_candidate_sites.json`](./nordic-atlas_candidate_sites.json)
- Candidate site ranking markdown: [`nordic-atlas_candidate_sites.md`](./nordic-atlas_candidate_sites.md)
- Candidate site sensitivity JSON: [`nordic-atlas_candidate_site_sensitivity.json`](./nordic-atlas_candidate_site_sensitivity.json)
- Candidate site sensitivity markdown: [`nordic-atlas_candidate_site_sensitivity.md`](./nordic-atlas_candidate_site_sensitivity.md)
- Candidate ranking engine manifest: [`nordic-atlas_candidate_ranking_engine_manifest.json`](./nordic-atlas_candidate_ranking_engine_manifest.json)
- Atlas evidence surface JSON: [`nordic-atlas_evidence_surface.json`](./nordic-atlas_evidence_surface.json)
- Atlas evidence surface markdown: [`nordic-atlas_evidence_surface.md`](./nordic-atlas_evidence_surface.md)
- Atlas scientific review JSON: [`nordic-atlas_scientific_review.json`](./nordic-atlas_scientific_review.json)
- Atlas scientific review markdown: [`nordic-atlas_scientific_review.md`](./nordic-atlas_scientific_review.md)


## Animal aDNA Layers

- Total animal locality points: `10`
- Shipped animal species: `10`
- Domesticated-core species layers: `8`
- Comparator species layers: `2`

### Layer Groups

- Domesticated-core animal evidence
- Comparator animal evidence

### Public Animal Filters

- Species focus
- Animal scope
- Chronology bucket
- Nordic animal leads only

### Visible Animal Caveats

- Approximate or inferred coordinates remain visible with explicit warnings.
- Comparator-only evidence remains visible without being counted as domesticated-core support.
- Weak or rejected support classes remain labeled in point popups instead of being silently hidden.
- Nordic relevance can remain regional rather than one exact named country.

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
| horse | Equus caballus | domesticated_core | 1 |
| pig | Sus scrofa domesticus | domesticated_core | 1 |
| sheep | Ovis aries | domesticated_core | 1 |
| cattle | Bos taurus | domesticated_core | 1 |
| goat | Capra hircus | domesticated_core | 1 |
| dog | Canis lupus familiaris | domesticated_core | 1 |
| cat | Felis catus | domesticated_core | 1 |
| dromedary camel | Camelus dromedarius | domesticated_core | 1 |
| reindeer | Rangifer tarandus | comparator | 1 |
| donkey | Equus asinus | comparator | 1 |


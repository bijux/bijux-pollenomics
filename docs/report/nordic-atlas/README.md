# Nordic Evidence Atlas

This shared interactive map bundle was generated on `2026-03-31`.
It combines AADR `v62.0` with whichever contextual datasets are present in the repository at generation time and copies those derived artifacts into this directory.

## Included Countries

| Country | Unique samples |
| --- | ---: |
| Sweden | 519 |
| Norway | 58 |
| Finland | 22 |
| Denmark | 300 |

## Bundle Notes

- This bundle is a generated publication artifact, not a source dataset.
- Local leaflet assets are copied into `./_map_assets` so the HTML does not depend on CDN-hosted library files.
- Basemap tiles are still requested from the active cartographic provider at runtime, so an offline browser session will not display background tiles.
- The map does not rank, score, or reconcile disagreement between sources; it only presents the records and overlays that were generated into this bundle.
- Country sample counts in this README refer to AADR records. Context layers can have different geographic scope and record counts inside the map.

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

# AADR Reports

This is the repository-local operations guide for generated reports and maps. The canonical narrative documentation is published through the MkDocs site under `docs/04-reports/`.

This directory stores country-level AADR report bundles together with one shared Nordic interactive map. The shared map includes AADR aDNA points plus context layers from Neotoma, SEAD, Nordic country boundaries, and RAÄ archaeology density.

The data acquisition model behind these reports is documented in [`docs/data/README.md`](../data/README.md).

## Validation

Run the automated checks from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Or use the local `.venv` workflow:

```bash
make lint
make test
make data-prep
make build
```

## Command Pattern

Generate any country report with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli report-country <COUNTRY_NAME> --version v62.0 --shared-map-label "<MAP_LABEL>" --shared-map-path "<RELATIVE_MAP_PATH>"
```

Each command writes one complete output bundle into `docs/report/<country-slug>/`:

- `README.md`: country summary with counts, coverage, and top localities
- `*_samples.csv`: sample-level inventory with latitude and longitude
- `*_localities.csv`: locality-level aggregation
- `*_samples.geojson`: map-ready point layer
- `*_samples.md`: full markdown inventory

Download the tracked AADR `.anno` inputs with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data aadr --version v62.0 --output-root data
```

Collect the full tracked data tree with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data all --version v62.0 --output-root data
```

These commands write:

- `data/aadr/v62.0/1240k/v62.0_1240k_public.anno`
- `data/aadr/v62.0/ho/v62.0_HO_public.anno`
- `data/neotoma/raw/`: raw Neotoma pollen response snapshot
- `data/neotoma/normalized/`: Nordic pollen CSV and GeoJSON
- `data/sead/raw/`: raw SEAD site snapshot
- `data/sead/normalized/`: Nordic SEAD site CSV and GeoJSON
- `data/boundaries/raw/`: raw Nordic country boundaries
- `data/boundaries/normalized/`: combined Nordic boundary GeoJSON
- `data/raa/raw/`: RAÄ capabilities, schema, and Fornsök domain metadata
- `data/raa/normalized/`: Swedish archaeology layer metadata plus archaeology-density GeoJSON

Generate one shared interactive map for several countries with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli report-multi-country-map <COUNTRY_NAME> <COUNTRY_NAME> ... --version v62.0 --name <MAP_SLUG> --title "<MAP_TITLE>" --context-root data
```

That command writes one shared bundle into `docs/report/<map-slug>/`:

- `README.md`: included countries and shared counts
- `*_samples.geojson`: combined point layer
- `*_map.html`: interactive map with country-wide filtering across all datasets, clustering, search, advanced controls, and acceptance-distance circles
- `nordic_pollen_sites.geojson`: copied Neotoma pollen layer used by the map
- `nordic_environmental_sites.geojson`: copied SEAD site layer used by the map
- `nordic_country_boundaries.geojson`: copied Nordic country outlines used for filtering and framing
- `sweden_archaeology_layer.json`: copied RAÄ layer metadata used by the map
- `sweden_archaeology_density.geojson`: copied RAÄ archaeology density grid used by the map

## Commands For Published Reports

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli collect-data all --version v62.0 --output-root data
PYTHONPATH=src python3 -m bijux_pollen.cli report-multi-country-map Sweden Norway Finland Denmark --version v62.0 --name nordic --title "Nordic Countries" --context-root data
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Sweden --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Norway --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Finland --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Denmark --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
```

## Shared Map

| Map | Countries | Summary | Interactive map |
| --- | --- | --- | --- |
| Nordic Countries | Sweden, Norway, Finland, Denmark | [`docs/report/nordic/README.md`](./nordic/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |

## Published Reports

| Country | Samples | Localities | Summary | Shared map |
| --- | ---: | ---: | --- | --- |
| Sweden | 519 | 91 | [`docs/report/sweden/README.md`](./sweden/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |
| Norway | 58 | 33 | [`docs/report/norway/README.md`](./norway/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |
| Finland | 22 | 4 | [`docs/report/finland/README.md`](./finland/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |
| Denmark | 300 | 119 | [`docs/report/denmark/README.md`](./denmark/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |

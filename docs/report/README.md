# AADR Reports

This directory stores country-level AADR report bundles together with one shared multi-country interactive map.

## Validation

Run the automated checks from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
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

Generate one shared interactive map for several countries with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli report-multi-country-map <COUNTRY_NAME> <COUNTRY_NAME> ... --version v62.0 --name <MAP_SLUG> --title "<MAP_TITLE>"
```

That command writes one shared bundle into `docs/report/<map-slug>/`:

- `README.md`: included countries and shared counts
- `*_samples.geojson`: combined point layer
- `*_map.html`: interactive map with zoom controls, country toggles, and acceptance-distance circles

## Commands For Published Reports

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli report-multi-country-map Sweden Norway Finland --version v62.0 --name nordic --title "Nordic Countries"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Sweden --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Norway --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Finland --version v62.0 --shared-map-label "Nordic Countries map" --shared-map-path "../nordic/nordic_aadr_v62.0_map.html"
```

## Shared Map

| Map | Countries | Summary | Interactive map |
| --- | --- | --- | --- |
| Nordic Countries | Sweden, Norway, Finland | [`docs/report/nordic/README.md`](./nordic/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |

## Published Reports

| Country | Samples | Localities | Summary | Shared map |
| --- | ---: | ---: | --- | --- |
| Sweden | 519 | 91 | [`docs/report/sweden/README.md`](./sweden/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |
| Norway | 58 | 33 | [`docs/report/norway/README.md`](./norway/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |
| Finland | 22 | 4 | [`docs/report/finland/README.md`](./finland/README.md) | [`nordic_aadr_v62.0_map.html`](./nordic/nordic_aadr_v62.0_map.html) |

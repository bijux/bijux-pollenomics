# AADR Country Reports

This directory stores generated country-level report bundles derived from local AADR metadata.

## Validation

Run the automated checks from the repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Command Pattern

Generate any country report with:

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli report-country <COUNTRY_NAME> --version v62.0
```

Each command writes one complete output bundle into `docs/report/<country-slug>/`:

- `README.md`: country summary with counts, coverage, and top localities
- `*_samples.csv`: sample-level inventory with latitude and longitude
- `*_localities.csv`: locality-level aggregation
- `*_samples.geojson`: map-ready point layer
- `*_samples.md`: full markdown inventory
- `*_map.html`: interactive map with zoom controls and acceptance-distance circles

## Commands For Published Reports

```bash
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Sweden --version v62.0
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Norway --version v62.0
PYTHONPATH=src python3 -m bijux_pollen.cli report-country Finland --version v62.0
```

## Published Reports

| Country | Samples | Localities | Summary | Interactive map |
| --- | ---: | ---: | --- | --- |
| Sweden | 519 | 91 | [`docs/report/sweden/README.md`](./sweden/README.md) | [`sweden_aadr_v62.0_map.html`](./sweden/sweden_aadr_v62.0_map.html) |
| Norway | 58 | 33 | [`docs/report/norway/README.md`](./norway/README.md) | [`norway_aadr_v62.0_map.html`](./norway/norway_aadr_v62.0_map.html) |
| Finland | 22 | 4 | [`docs/report/finland/README.md`](./finland/README.md) | [`finland_aadr_v62.0_map.html`](./finland/finland_aadr_v62.0_map.html) |

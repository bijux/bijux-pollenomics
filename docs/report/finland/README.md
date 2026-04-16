# Finland AADR v66 Report

This bundle was generated from the AADR `v66` `.anno` files on `2026-04-16`.
It inventories only AADR sample rows that match the `Finland` country filter. Environmental and archaeology context layers are published in the shared map bundle, not duplicated here.

## Summary

- Country filter: `Finland`
- Unique AADR samples: `32`
- Unique localities: `6`
- Latitude range: `60.200000` to `69.910000`
- Longitude range: `22.178000` to `27.030000`

This country bundle is valid even when the filter returns zero AADR samples. In that case the CSV, GeoJSON, and markdown exports remain present so downstream checks can distinguish an empty result from a missing artifact.
Locality rows now preserve the combined BP coverage of the samples they aggregate.

## Dataset Coverage

| Dataset | Finland rows |
| --- | ---: |
| `1240k` | 23 |
| `ho` | 32 |

The report deduplicates samples by `genetic_id` across datasets. Dataset row counts can differ by coverage, but the combined inventory for `Finland` contains `32` unique samples in AADR `v66`.

## Output Files

- Shared interactive map: <a href="../nordic-atlas/nordic-atlas_map.html">Nordic Evidence Atlas</a>
- Full sample inventory: [`finland_aadr_v66_samples.csv`](./finland_aadr_v66_samples.csv)
- Locality summary: [`finland_aadr_v66_localities.csv`](./finland_aadr_v66_localities.csv)
- Map-ready GeoJSON: [`finland_aadr_v66_samples.geojson`](./finland_aadr_v66_samples.geojson)
- Machine-readable summary: [`finland_aadr_v66_summary.json`](./finland_aadr_v66_summary.json)
- Full markdown sample table: [`finland_aadr_v66_samples.md`](./finland_aadr_v66_samples.md)

## Top Localities

| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |
| --- | ---: | ---: | ---: | --- | --- |
| Finland, modern | 19 | 60.2 | 24.9 | 0 BP | `1240k,ho` |
| Levanluhta (Isokyro) | 8 | 62.948744 | 22.410146 | 1112-1688 BP | `1240k,ho` |
| Utsjoki | 2 | 69.91 | 27.03 | 0 BP | `1240k,ho` |
| Enontekiö | 1 | 68.383893 | 23.632454 | 0 BP | `ho` |
| Käldamäki | 1 | 63.151 | 22.178 | 1322-1474 BP | `1240k,ho` |
| Levänluhta | 1 | 62.949 | 22.418 | 1258-1474 BP | `1240k,ho` |

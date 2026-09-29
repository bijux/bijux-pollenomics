# What we established from Nordic HYDE cropland sources

We asked what the HYDE release itself reports for Nordic country cropland
before using it as model context. We retained 84 modeled totals for Denmark,
Finland, Norway and Sweden at seven native CE year labels and three source
scenarios in our [country-year table](../../docs/report/regions/nordic/hyde-country-cropland/country-years.csv).
Our [report](../../docs/report/regions/nordic/hyde-country-cropland/report.json)
pins four consumed source files by SHA-256. We read country codes from
`HYDE_country_codes.xlsx` and source totals from the scenario-specific
`cropland_c.txt` tables. We reported those totals in km² without assigning
grid cells to countries.

| Country | Base 500 CE, km² | Base 2000 CE, km² | Base 2025 CE, km² |
| --- | ---: | ---: | ---: |
| Denmark | 4,036.0 | 22,884.9 | 23,553.7 |
| Finland | 411.2 | 21,920.0 | 22,443.0 |
| Norway | 811.7 | 8,840.0 | 8,082.6 |
| Sweden | 3,082.2 | 26,022.0 | 25,235.1 |

We keep the lower and upper **scenario** columns as modeled alternatives, not
confidence limits. At 2000 CE, their four-country source totals bracket the
corresponding base totals; we do not infer that ordering for every native grid
cell or year. The release's README describes `cropland_c.txt` as country total
cropland area in km² and identifies `cropland<yr>.asc` as area in km² per cell.
The [provider's HYDE dataset page](https://landuse.sites.uu.nl/datasets/)
identifies HYDE 3.5 as its 2025 release and reports 5 arc minute resolution.
The release attributes HYDE 3.5 to Klein Goldewijk, Beusen, Vander Linden and
Doelman (2025, manuscript in preparation).

We use these modeled totals as external land-use context. They do not measure
pollen or vegetation at our study sites. We kept the source years as CE labels;
we did not convert `0AD` or NetCDF `365_day` conventions to BP. We retained
the 2025 column while flagging release prose that states a 2023 endpoint.
Local Yoda metadata and `License.txt` say CC BY-NC 4.0, while the README and
NetCDF attributes say CC BY 3.0. Pending provider resolution, we apply the
more restrictive declaration to these derived summaries and redistribute no
native HYDE files. Our [native grid-to-country check](../../docs/report/regions/nordic/hyde-country-cropland/grid-conservation/README.md)
verified 21 cropland grids at the seven selected CE labels against their
source country tables. We still need other variables and years, rights
reconciliation, chronology alignment and a matched no-HYDE/HYDE model
comparison.

To reproduce our result, run from the repository root into a new artifacts
directory:

```sh
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.hyde_country_cropland \
  --source-root /Users/bijan/bijux/bijux-pollenomics-data/HYDE-3.5 \
  --output artifacts/jobs/hyde-nordic-country-cropland-replay
```

We can relocate the external source root without changing its relative input
paths. Our [HYDE source review](../../docs/public/pollenomics-data/sources/hyde.md)
records the remaining release and admission conflicts.

# Source-reported Nordic HYDE cropland

The [country-year table](country-years.csv) contains 84 HYDE modeled cropland
totals for Denmark, Finland, Norway and Sweden at seven native CE year labels
and three source scenarios. The [report](report.json) pins the four consumed
source files by SHA-256. The producer reads the country codes from the release's
`HYDE_country_codes.xlsx` member and the scenario-specific `cropland_c.txt`
tables. Its output uses the source's country totals in km²; it does not assign
cells from a grid to countries.

| Country | Base 500 CE, km² | Base 2000 CE, km² | Base 2025 CE, km² |
| --- | ---: | ---: | ---: |
| Denmark | 4,036.0 | 22,884.9 | 23,553.7 |
| Finland | 411.2 | 21,920.0 | 22,443.0 |
| Norway | 811.7 | 8,840.0 | 8,082.6 |
| Sweden | 3,082.2 | 26,022.0 | 25,235.1 |

The lower and upper **scenario** columns are distinct modeled alternatives, not
confidence limits. At 2000 CE, their four-country source-reported totals bracket
their respective base totals; this does not prove ordering for every native grid
cell or year. The release's README describes `cropland_c.txt` as country total
cropland area in km² and identifies `cropland<yr>.asc` as area in km² per cell.
The [provider's HYDE dataset page](https://landuse.sites.uu.nl/datasets/)
identifies HYDE 3.5 as its 2025 release and reports 5 arc minute resolution.
The release attributes HYDE 3.5 to Klein Goldewijk, Beusen, Vander Linden and
Doelman (2025, manuscript in preparation).

These modeled country totals are a useful external land-use context result, but
they do not measure pollen or vegetation at the study sites. Source year labels
are kept as CE labels: the `0AD` and NetCDF `365_day` conventions have not been
converted to BP. The table has a 2025 column although source release prose also
states a 2023 endpoint. The local Yoda metadata and `License.txt` say CC BY-NC
4.0, whereas the README and NetCDF attributes say CC BY 3.0. Treat these small
derived summaries under the more restrictive declaration pending a provider
resolution; no native HYDE files are redistributed here. A grid-country
conservation check, rights reconciliation, chronology alignment and a matched
no-HYDE/HYDE model comparison remain open.

From the repository root, regenerate into a new artifacts directory with:

```sh
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.hyde_country_cropland \
  --source-root /Users/bijan/bijux/bijux-pollenomics-data/HYDE-3.5 \
  --output artifacts/jobs/hyde-nordic-country-cropland-replay
```

The external source root can be relocated without changing its relative input
paths. The [HYDE source review](../../../../public/pollenomics-data/sources/hyde.md)
records the remaining release and admission conflicts.

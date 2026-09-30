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

## Our source-authority decision

We compared the public release description with the declarations in the
retained local files before treating any native grid as an admitted Nordic
covariate. The [Utrecht catalog](https://landuse.sites.uu.nl/datasets/) names
HYDE 3.5 for the 2025 Global Carbon Budget at five arc minutes, but does not
publish a file manifest or checksums binding our local bytes to that release.
The local README calls itself `hyde35_c9_base_mrt2025`; all 48 inspected
NetCDF headers instead say `HYDE3.4 test netCDF`. We kept both declarations.
For a concrete byte anchor, our retained base 2000 CE cropland ZIP has SHA-256
`d0a762ccce3256d25c36e1c58894c6a6b05f93075006366854cc7e6176c7d09f`;
its ordinal-zero `cropland2000AD.asc` member has SHA-256
`31a74f63973886edbd2303737df2684c799caaea83af27561755e1d5da67b0c7`.
These identify our local source, not the provider's current distribution.

We retained the three distinct rights statements. The local Yoda metadata and
`License.txt` say CC BY-NC 4.0, while its README and NetCDF attributes say
CC BY 3.0. The [provider DOI record](../../docs/report/source-relations/hyde/provider-record/README.md)
now says CC BY 4.0 after its September 2026 update; it has no exact-member
binding to the local release. We have not selected whichever statement is
most convenient as permission to redistribute native cells.

The local ASCII grid header fixes a 4320-by-2160 source axis beginning at
longitude-like `-180`, latitude-like `-90`, with literal step `0.0833333`;
NetCDF coordinates carry degree units. Neither declaration gives a formal
datum or EPSG identity for country overlay. The ASCII `0AD` label and NetCDF
`365_day` calendar also lack a provider-specific conversion to historical
BP windows. Local headers name area in `km**2` and population in `capita`,
but do not establish which land-use categories overlap. The base, lower and
upper names are source scenarios, not probability intervals or pointwise
bounds. Our [source review](../../docs/public/pollenomics-data/sources/hyde.md)
retains the detailed axis and scenario observations.

We therefore admit the bounded source-reported country totals and internal
grid conservation below as **modeled-source accounting only**. We do not yet
admit a release-wide native-grid product, public cell redistribution or a
matched pollen-model HYDE comparison. The [open evidence request](../needed/README.md)
asks for provider binding of file identity, rights, CRS, dates, units and
scenario meaning. The older source-authority working review is preserved in
[private custody](../architecture/artifact-custody/hyde-provider-authority.json);
this report owns our current decision.

We use these modeled totals as external land-use context. They do not measure
pollen or vegetation at our study sites. We kept the source years as CE labels
and retained the 2025 column while flagging release prose that states a 2023
endpoint. We apply the more restrictive local rights declaration to these
derived summaries. Our [native grid-to-country check](../../docs/report/regions/nordic/hyde-country-cropland/grid-conservation/README.md)
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

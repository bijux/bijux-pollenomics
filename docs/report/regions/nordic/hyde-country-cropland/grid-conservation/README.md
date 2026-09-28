# Native HYDE cropland country conservation at 2000 CE

The [12-row result](grid-conservation.csv) sums the release's
`cropland2000AD.asc` grid over cells labeled Denmark, Finland, Norway or Sweden
by its own `iso_cr.asc` country grid, separately for base, lower and upper
scenarios. The [report](report.json) pins the general ISO archive, all three
scenario archives and their source country tables by SHA-256. ZIP member
occurrences must be unique and each native grid must have the same six header
declarations and all 2,160 rows of 4,320 cells.

| Country | ISO grid cells | Base cropland km² | Largest absolute grid–table difference across scenarios, km² |
| --- | ---: | ---: | ---: |
| Denmark | 1,103 | 22,884.872 | 0.000000000014 |
| Finland | 9,161 | 21,920.000 | 0.000000000030 |
| Norway | 9,699 | 8,840.000 | 0.000000000014 |
| Sweden | 11,504 | 26,022.000 | 0.000000000071 |

Every selected ISO cell has a finite nonnegative cropland value in all three
scenarios. Decimal sums agree with the source-reported country totals to better
than 0.000001 km²; the tiny differences are consistent with source numeric
rounding. Source zero cells remain counted as zeros, and country cell totals
are not mistaken for land area. The
[country-year study](../README.md) supplies the matched country totals and
their source interpretation.

This verifies a native grid-to-country reconciliation for cropland at one CE
label. It does not establish the formal CRS, translate HYDE time to BP, resolve
the release's rights/version conflicts, admit every variable or year, or turn
modeled land use into independent vegetation truth. The lower and upper source
scenarios remain alternative model outputs, not uncertainty intervals.

From the repository root, regenerate into a new artifacts directory with:

```sh
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.hyde_country_grid_conservation \
  --source-root /Users/bijan/bijux/bijux-pollenomics-data/HYDE-3.5 \
  --output artifacts/jobs/hyde-country-grid-conservation-replay
```

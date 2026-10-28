# Native HYDE cropland country conservation across seven CE labels

The [84-row result](grid-conservation.csv) sums the release's
`cropland<year>AD.asc` grids at **500, 1000, 1500, 1700, 1900, 2000 and
2025 CE** over cells labeled Denmark, Finland, Norway or Sweden by its own
`iso_cr.asc` country grid. Each year is checked separately for base, lower and
upper scenarios. The [report](report.json) pins the general ISO archive, all
21 scenario/year archives and the three source country tables by SHA-256. ZIP
member occurrences must be unique and each native grid must have the same six
header declarations and all 2,160 rows of 4,320 cells.

| Country | ISO grid cells | Base 2000 CE cropland km² | Largest absolute grid–table difference across seven years and three scenarios, km² |
| --- | ---: | ---: | ---: |
| Denmark | 1,103 | 22,884.872 | 0.0000000000274 |
| Finland | 9,161 | 21,920.000 | 0.0000000000851 |
| Norway | 9,699 | 8,840.000 | 0.0000000000138 |
| Sweden | 11,504 | 26,022.000 | 0.0000000000795 |

Every selected ISO cell has a finite nonnegative cropland value in all three
scenarios at all seven labels. Decimal sums agree with the source-reported
country totals to better than 0.000001 km²; the tiny differences are consistent
with source numeric rounding. Source zero cells remain counted as zeros, and
country cell totals are not mistaken for land area. The
[country-year study](../README.md) supplies the matched country totals and
their source interpretation.

This verifies native grid-to-country reconciliation for cropland at seven
selected CE labels. It does not establish the formal CRS, translate HYDE time to
BP, resolve the release's rights/version conflicts, admit other variables or
every source year, or turn modeled land use into independent vegetation truth.
The lower and upper source scenarios remain alternative model outputs, not
uncertainty intervals.

From the repository root, regenerate into a new artifacts directory with:

```sh
source_store="/path/to/qualified/bijux-pollenomics-data"
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.hyde_country_grid_conservation \
  --source-root "$source_store/HYDE-3.5" \
  --output artifacts/jobs/hyde-country-grid-conservation-replay
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained native-grid account uses exact Decimal country-cell sums to reconcile cropland to source tables at sevenCElabels under three separately retained scenarios.

**Unsupported claim.** Conservation does not validate the formal CRS, BP conversion, licence/version conflicts, all release years/variables or ecological accuracy of modeled land use.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer.

**Remaining input or review.** Source-owner rights, coordinate/time interpretation and intended analytical use remain unresolved; no independent measured vegetation target is supplied.

**Cause category.** Numerical source-grid/table conservation on selected modeled variables.

**Consequence.** Native zero cells and source country labels are preserved without converting cell counts to land area or treating scenario bounds as probability intervals.

**Precise next acceptance route.** Replay the seven-year cropland consumer against its22archives and three country tables, then resolve source metadata and rights before a separate scientific comparison.

**Negative or refused result.** The2025source label and conflicting release prose remain explicit; no missing/negative selected cell is silently filled.

**Matched denominator.** 84country/year/scenario rows; four countries,sevenCElabels500/1000/1500/1700/1900/2000/2025,three scenarios; each grid2,160×4,320cells, tolerance1e-6km².

- [Retained qualification evidence: docs/report/regions/nordic/hyde-country-cropland/grid-conservation/report.json](report.json) (SHA-256 `adee39b87859b3adac60c4f9c8a33d987c446950572f058b545ed1010c098628`).

- [Canonical scientific account: reports/science/hyde-cropland-source-account.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/hyde-cropland-source-account.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

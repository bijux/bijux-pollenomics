# LandClim II modeled Nordic panels

The [panel inventory](panels.csv) contains 400 source-window × country × metric rows: four Nordic countries, 25 published PANGAEA 937075 windows, and four separately labeled model metrics. The [receipt](report.json) pins the normalized grid and source classification table by byte count and SHA-256. The producer validates the complete 1,875-row PANGAEA II temporal grid through the production modeled-context manifest before summarizing any row.

ET, ST, and OL are the published evergreen-tree, summer-green-tree, and open-land land-cover types. AL is the published agricultural-land/cereals plant functional type within OL. AL is not a fourth disjoint land-cover category. All values are source-model percentage-cover estimates. A source window is not a physical pollen sample chronology, and none of these values is measured vegetation truth.

Each CSV row gives the number of source grid cells, the high/low/no-pollen quality split, and the minimum and maximum *individual-cell* estimates and source standard errors among high- and low-quality rows. `no_pollen_data` placeholders are excluded from numeric ranges. Blank numeric bounds mean no usable modeled cell. Standard errors are not pooled, converted to confidence intervals, or treated as uncertainty for a country average. The table makes no area-weighted or country-mean estimate.

The 25 windows are discrete published intervals from 11,200–11,700 BP to 0–100 BP. Adjacent windows do not authorize interpolation or propagation. Country groups here use the governed source-grid country labels and the production manifest's country/window quality inventory; they are descriptive model coverage, not a boundary-release decision.

## Reproduce

From the repository root, write to a new artifact directory and compare both files to this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.landclim_modeled_panels \
  --repository . --output artifacts/jobs/landclim-modeled-panels/replay
```

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/landclim_modeled_panels.py) refuses changed source labels or an incomplete model manifest. The [focused checks](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/tests/source_completion/test_landclim_modeled_panels.py) exercise the four-panel inventory, no-pollen denominators, paired standard-error fields, and label drift. Qualified scientific interpretation and comparison to independently measured vegetation are separate decisions.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained panel inventory summarizes source PANGAEA937075 model quality and individual-cell cover/SE ranges by country and published window, keeping AL within OL rather than a fourth disjoint cover class.

**Unsupported claim.** The table gives no area-weighted country mean, pooled SE/confidence interval, physical sample chronology, independent vegetation truth or authorized temporal interpolation.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer.

**Remaining input or review.** Source-classification authority, historical input authenticity and any independent vegetation comparison remain separate review decisions.

**Cause category.** Descriptive source-model coverage rather than measured reconstruction validation.

**Consequence.** Blank ranges represent no usable modeled cell; no-pollen placeholders cannot become zero cover or support an ecological absence claim.

**Precise next acceptance route.** Replay the maintained panel consumer against the complete normalized model manifest and source labels, then separately qualify any matched scientific comparison.

**Negative or refused result.** 307no-pollen cell/window placeholders are excluded from numeric ranges; AL is not summed with its enclosing OL as an independent category.

**Matched denominator.** 400rows=four countries×25published windows×four labeled metrics;1,875source cell/window rows,307no-pollen placeholders; cellwise estimates remain percent cover.

Qualified authored reader SHA-256: `d07027c90d9174393c1623f6e173d81cdee6725bc1ef7469d5d331e743be8178`.

- [Retained qualification evidence: docs/report/regions/nordic/landclim-modeled-panels/report.json](report.json) (SHA-256 `4bb8b1e1bec5a200743c67dc48b8f79c74b48a15fae588f7f21e7cf599343b5c`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

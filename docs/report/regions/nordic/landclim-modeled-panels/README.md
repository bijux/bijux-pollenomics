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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

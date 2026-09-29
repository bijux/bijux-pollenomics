# Three-lake Swedish observed-pollen transfer

The [locked protocol](protocol.json) selected Gilltjärnen, Lake Avegöl and Flinkasjön from Neotoma/EPD **using site, collection-unit, dataset and age metadata before target counts were read**. Each is one lake site with one source pollen dataset and one core. The source-default calibrated-age rule selects **268 of 273** samples; the five other source samples remain outside this study. The selected samples span **63 site by 500 BP bins**.

The [input manifest](input-manifest.json) binds the Neotoma relational snapshot, the authors' 10,788-row taxonomy lookup, the 31-target axis and the previously retained 81-site DK/FI/NO training profiles. Training excludes every Swedish target site. The predictor read only [training](inputs/training-SE.json.gz) and [target metadata](inputs/metadata-SE.json.gz); the separately retained [sealed outcomes](sealed-outcomes/outcomes-SE.json.gz) were opened only after the [predictions](predictions/predictions-SE.json.gz) and their [freeze receipt](prediction-freeze.json) had been committed at `135250049`.

| Target lake | Selected samples | Scored bins | Native pollen NISP | Assigned to 31 targets | Author excluded | Unmapped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Gilltjärnen | 100 | 23 | 59,073 | 57,697 | 1,374 | 2 |
| Lake Avegöl | 62 | 15 | 67,949 | 67,178 | 740 | 31 |
| Flinkasjön | 106 | 25 | 111,775 | 106,240 | 1,711 | 3,824 |
| **Total** | **268** | **63** | **238,797** | **231,115** | **3,825** | **3,857** |

All 63 bins received the three fixed baseline predictions and have positive assigned pollen counts, yielding **189 matched score rows** and zero training-support refusals. The [coverage](coverage.csv), [site scores](site-scores.csv), [all bin scores](scores.csv) and [taxon diagnostics](taxon-diagnostics.csv) retain their denominators.

| Fixed method | Equal-site mean absolute fraction error | Equal-site Hellinger distance |
| --- | ---: | ---: |
| Inverse distance squared | 0.017334 | 0.286757 |
| Nearest site | 0.017932 | 0.288872 |
| Training mean | 0.020682 | 0.333694 |

Inverse distance squared has the lowest three-site mean error in this declared comparison, but nearest site has the lower error at Lake Avegöl. Only three lake groups support the equal-site aggregate, and prior Nordic outcomes informed the fixed study design. This is **development evidence for direct observed-pollen subcomposition**, not a confirmatory estimate, LRA reconstruction, full-pollen or vegetation prediction, or a country-wide Swedish skill claim. Basin geometry, PPE, independent vegetation truth and unresolved source periods remain separate admission questions.

## Reproduce

From the repository root, with the retained external author-reference capsule:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_transfer prepare \
  --repository . --author-source-root /path/to/landclim/author-reference \
  --output artifacts/jobs/swedish-lake-transfer/replay-prepared
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_transfer predict \
  --prepared artifacts/jobs/swedish-lake-transfer/replay-prepared \
  --output artifacts/jobs/swedish-lake-transfer/replay-predictions
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_lake_transfer score \
  --prepared artifacts/jobs/swedish-lake-transfer/replay-prepared \
  --predictions docs/report/regions/nordic/swedish-lake-transfer/predictions \
  --output artifacts/jobs/swedish-lake-transfer/replay-scored
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/regions/nordic/swedish-lake-transfer/verify.py
```

The score command must use the committed prediction file. The [report manifest](manifest.json) binds retained evidence bytes, and `verify.py` checks the freeze, source denominator, score coverage and site-macro arithmetic. The private author lookup is authenticated by digest and is not copied here.

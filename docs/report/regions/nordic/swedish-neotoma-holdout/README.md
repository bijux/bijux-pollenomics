# Storasjö observed-pollen holdout

The [locked protocol](protocol.json) selected Neotoma site 28874, collection
unit 39243, using source metadata before the target pollen counts were read.
Storasjö has two EPD pollen datasets, 54004 and 54005, from the same bog core.
Each has 77 samples at the same 77 depths and with the same default calibrated
ages. The [independent parallel-dataset review](parallel-dataset-review.json)
finds identical source-name pollen NISP vectors at **77/77** matching depths:
35,767 native pollen counts and 60 distinct source names in each dataset.
Dataset 54004 supplies the one physical-core target; counting both would double
the response without adding a separate core. The parallel dataset remains
identified in the source audit.

The [input manifest](input-manifest.json) binds the exact Neotoma relational
snapshot, author taxonomy lookup and previously retained 81-site DK/FI/NO
training profiles. The 77 target samples have selected source-default calibrated
ages from 65 to 10,874 BP. Their 500 BP bins yield **22 target site bins**.
The 31-target mapping retains **35,505 assigned NISP**, 253 author-excluded
NISP and 9 unmapped NISP out of 35,767 native pollen NISP. The [prepared
metadata](inputs/metadata-SE.json.gz) contains sample IDs, age-bin membership
and site location, while [sealed outcomes](sealed-outcomes/outcomes-SE.json.gz)
retain target counts separately. This is a direct observed-pollen
subcomposition; no LRA reconstruction or measured vegetation is involved.

The [prediction freeze](prediction-freeze.json) and [committed prediction
file](predictions/predictions-SE.json.gz) were committed before scoring. All
three fixed methods predicted all 22 bins; target counts were absent from the
predictor inputs. Scoring used that committed prediction file. The [score
table](scores.csv), [coverage](coverage.csv), [site summary](site-scores.csv)
and [taxon diagnostics](taxon-diagnostics.csv) preserve the matched denominator.

| Fixed method | Scored bins | Site mean absolute fraction error | Site Hellinger distance |
| --- | ---: | ---: | ---: |
| nearest site | 22 | 0.015389 | 0.243786 |
| inverse distance squared | 22 | 0.016881 | 0.285723 |
| training mean | 22 | 0.019351 | 0.327260 |

Nearest site has the lowest error for this **one target core** on the fixed
31-target axis. Storasjö is a bog, so its pollen source support need not match
the lake sites in the earlier Swedish study. Prior Nordic outcomes informed the
fixed methods and source records were available before this protocol; this is
an additional development transfer result, not independent confirmation of
model superiority or country-wide performance. The target has no admitted
independent landscape vegetation label.

## Reproduce

From the repository root, with the retained external author-reference capsule:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_holdout prepare \
  --repository . --author-source-root /path/to/landclim/author-reference \
  --output artifacts/jobs/swedish-neotoma-holdout/replay-prepared
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_holdout predict \
  --prepared artifacts/jobs/swedish-neotoma-holdout/replay-prepared \
  --output artifacts/jobs/swedish-neotoma-holdout/replay-predictions
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_holdout score \
  --prepared artifacts/jobs/swedish-neotoma-holdout/replay-prepared \
  --predictions docs/report/regions/nordic/swedish-neotoma-holdout/predictions \
  --output artifacts/jobs/swedish-neotoma-holdout/replay-scored
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_neotoma_duplicate_review \
  --repository . --output artifacts/jobs/swedish-neotoma-holdout/replay-duplicates
```

The [report manifest](manifest.json) lists all retained file digests. Compare
each replay product byte-for-byte with its retained counterpart; the scorer
must use the committed frozen prediction file. The private author lookup is
authenticated by SHA-256 and is not copied into this report.

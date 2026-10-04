# How three additional Swedish lakes transferred on the author pollen axis

## Our decision

We tested the three fixed direct-pollen baselines on Swedish lake cores outside
our original Abborrtjärnen, Bussjösjön and Bökesjön targets. We committed the
[metadata-only selection rule](../../docs/report/regions/nordic/swedish-lake-transfer/protocol.json)
before reading target pollen counts. It selected Gilltjärnen, Lake Avegöl and
Flinkasjön, each with one EPD pollen dataset and one collection unit. We used
source-default comparable calibrated ages, one 500 BP binning rule and the
31-target author taxonomy. All Swedish targets remained outside the 81-site
Denmark/Finland/Norway training set.

We selected 268 of 273 source samples. The five refused samples have
source-default calibrated point ages below 0 BP; the locked nonnegative-BP
rule excludes them from this study, without converting them to missing pollen
or ecological absence. Gilltjärnen has one refusal at −49.97366 BP, Lake
Avegöl one at −15.4 BP, and Flinkasjön three at −50, −33.3 and −9.4 BP.
Their native pollen counts remain source observations.

| Lake | Selected / source samples | Selected native pollen NISP | Age-refused native pollen NISP | All source native pollen NISP |
| --- | ---: | ---: | ---: | ---: |
| Gilltjärnen | 100 / 101 | 59,073 | 610 | 59,683 |
| Lake Avegöl | 62 / 63 | 67,949 | 920 | 68,869 |
| Flinkasjön | 106 / 109 | 111,775 | 3,531 | 115,306 |
| **Total** | **268 / 273** | **238,797** | **5,061** | **243,858** |

The five excluded sample IDs are `551822` at Gilltjärnen, `552864` at Lake
Avegöl, and `552982`, `552983` and `552996` at Flinkasjön, each with the
`neotoma:sample:` prefix. These exclusions precede count aggregation and
leave the retained predictions and scores unchanged. Native pollen `NISP`
selects the source pollen/count measurement rows; it is not an independently
authenticated terrestrial LRA denominator. Neotoma source attribution and
[reuse terms](../../docs/public/pollenomics-data/sources/neotoma.md) continue
to apply. The selected counts contain 238,797 native pollen NISP: 231,115
assigned to the 31 targets, 3,825 author-excluded and 3,857 unmapped. The
[input manifest](../../docs/report/regions/nordic/swedish-lake-transfer/input-manifest.json)
binds the Neotoma relational snapshot, author lookup and training profiles.
The predictor saw training data and target metadata, while target outcomes
remained sealed until the [predictions and freeze receipt](../../docs/report/regions/nordic/swedish-lake-transfer/prediction-freeze.json)
were committed. The [governed verifier](../../docs/report/regions/nordic/swedish-lake-transfer/verify.py)
checks those identities, count closure, score coverage and site-macro arithmetic.
The [producer used at prediction freeze](../../docs/report/regions/nordic/swedish-lake-transfer/reference/prediction-producer.py.txt)
is retained by exact hash from commit `135250049`; later source edits do not
replace the code identity in the frozen receipt. We separately reran the
current prepare, predict and score commands. All ten produced input,
prediction and score files matched their governed counterparts byte for
byte; the prediction SHA-256 remains
`eb10b5e7225cef3c51b544c1a25cebc264d9b5ab10477d9c4216b83a38bad909`.

## What we found

All 63 eligible site by 500 BP bins received all three fixed predictions,
with zero training-support refusals and 189 matched method scores. On the
equal-site 31-target response, inverse distance squared had the lowest
three-site mean absolute fraction error, but nearest site was better at Lake
Avegöl. The [per-site scores](../../docs/report/regions/nordic/swedish-lake-transfer/site-scores.csv)
show where the aggregate comes from:

| Lake | Scored bins | IDW MAE | Nearest MAE | Training-mean MAE |
| --- | ---: | ---: | ---: | ---: |
| Gilltjärnen | 23 | 0.011357 | 0.014240 | 0.012337 |
| Lake Avegöl | 15 | 0.019324 | 0.014938 | 0.023378 |
| Flinkasjön | 25 | 0.021322 | 0.024618 | 0.026330 |
| **Equal-site mean** | **63 total** | **0.017334** | **0.017932** | **0.020682** |

The equal-site Hellinger distances are 0.286757 for IDW, 0.288872 for
nearest site and 0.333694 for training mean. These are distances between
predicted and observed **closed pollen compositions**, not vegetation
accuracy. The [189-row score ledger](../../docs/report/regions/nordic/swedish-lake-transfer/scores.csv),
[coverage](../../docs/report/regions/nordic/swedish-lake-transfer/coverage.csv)
and [machine summary](../../docs/report/regions/nordic/swedish-lake-transfer/report.json)
retain every denominator and source hash. Flinkasjön contributes 3,824 of
the 3,857 unmapped NISP; the matched score excludes this mass rather than
silently assigning it to a target taxon.

## What this supports

The result extends our Swedish **observed-pollen** development evidence to
three further lakes on the same author target axis. It does not increase the
original three-lake study's 51 scored bins: these are separate physical sites
and a separate 63-bin transfer. Earlier Nordic outcomes informed the fixed
design, and only three new lake groups support this aggregate. We therefore
make no untouched-confirmation or country-wide skill claim. Basin geometry,
PPE, a source-qualified LRA chronology and independent measured vegetation
remain unresolved for these cores. This study supplies no REVEALS/LOVE
reconstruction or vegetation truth.

The [governed result page](../../docs/report/regions/nordic/swedish-lake-transfer/README.md)
gives the prepare, predict and score commands. Recheck the retained study from
the repository root with:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/regions/nordic/swedish-lake-transfer/verify.py
```

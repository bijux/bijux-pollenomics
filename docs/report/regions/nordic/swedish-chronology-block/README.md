# Swedish observed-pollen chronology block

This development comparison asks whether fixed pollen predictors can predict a
Swedish target age bin using source pollen from **exactly two 500 BP bins older**.
For every target, the predictor excludes source bins at the target age and the
immediately younger and older ages. It uses the already retained four-country
training folds, which exclude the target physical site and group. The
[preparation](prepared/prepare.json) declares this rule and binds the sealed
outcome identity before scoring. The [prediction freeze](frozen/freeze.json)
contains all predictions and refusals before the target counts are opened.

The 31-taxon response is the retained closed observed-pollen subcomposition.
Each source composition comes from one positive-count bin at the declared older
age. Training mean, nearest site and inverse-distance-squared use fixed methods
and site-center distances. Every one of the 54 target site bins had at least two
eligible training groups: 21 at Abborrtjärnen, 20 at Bussjösjön and 13 at
Bökesjön. There were 162 frozen method predictions, 54 scored bins and no
refusals. The [coverage](coverage.csv), [scores](scores.csv), [paired scores](paired-scores.csv)
and [machine report](report.json) retain those denominators and each source bin.

The paired comparator is the previously retained same-bin, all-site predictor
from the [support sensitivity study](../swedish-support-sensitivity/README.md).
It uses the identical target bins and observed target counts. Equal-site MAE
first averages bins within each of the three sites; sample-weighted MAE is a
separate descriptive view. The [scientific interpretation](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sweden-chronology-block.md)
reports both the effect and its limits.

This is a nominal source-bin separation on previously exposed data. It does
not establish nonoverlap of true age distributions, propagate age-model
uncertainty, provide independent confirmation, reconstruct LRA vegetation or
measure vegetation accuracy.

## Reproduce

From the repository root, run the three stages into absent `artifacts/` paths:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_chronology_block prepare \
  --repository . --output artifacts/jobs/swedish-chronology-block/replay/prepared
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_chronology_block predict \
  --repository . \
  --prepared artifacts/jobs/swedish-chronology-block/replay/prepared \
  --output artifacts/jobs/swedish-chronology-block/replay/frozen
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_chronology_block score \
  --repository . \
  --prepared artifacts/jobs/swedish-chronology-block/replay/prepared \
  --frozen artifacts/jobs/swedish-chronology-block/replay/frozen \
  --freeze-sha256 8592b580600da80a76903c9fa68435619bc53039d4f958e7f5b826a361360c49 \
  --output artifacts/jobs/swedish-chronology-block/replay/scored
```

The score stage authenticates the frozen predictions before reading target
outcomes. Compare the replayed files byte for byte with the retained products.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained31-taxon development comparison uses source pollen from exactly two500-BPbins older, excludes target/adjacent source bins and target physical groups, and scores frozen predictions on the same target outcomes as its baseline.

**Unsupported claim.** Nominal1,000-BPseparation is not nonoverlap of true ages, a chronology posterior, independent confirmation, LRA reconstruction or measured vegetation skill.

**Actual verification performed.** Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer.

**Remaining input or review.** Age-model uncertainty and scientific generalization need source-qualified distributions and independent targets; previously exposed data remain development support.

**Cause category.** Nominal temporal source separation on exposed pollen.

**Consequence.** Matched scores diagnose sensitivity to the declared training-time rule, while equal-site and sample-weighted summaries remain different estimands.

**Precise next acceptance route.** Replay prepare/predict/score under the exact older-bin rule and compare only identical target bins; obtain untouched and source-qualified support before a confirmatory claim.

**Negative or refused result.** PrimaryIDWequal-siteMAE0.0240227681is poorer than the matched baseline0.0236473232; zero refusals is retained support, not scientific validation.

**Matched denominator.** Three physical sites with21/20/13target bins=54bins,31taxa,three methods/162predictions; zero refused or failed bins.

Qualified authored reader SHA-256: `e634d4d343e4eec94c2014e64b59c060646553742c16c1f62192b2e3dbbd2af3`.

- [Retained qualification evidence: docs/report/regions/nordic/swedish-chronology-block/report.json](report.json) (SHA-256 `d6ecc8d8805c778efe63b3527ddb6c8406ed43f536dd991fd0f672205e586487`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

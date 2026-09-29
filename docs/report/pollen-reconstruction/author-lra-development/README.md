# Author-prepared LRA development run

This is an exploratory calculation on the previously exposed English LandClim II
author cohort. It is separate from the Swedish and Nordic Neotoma studies. The
private author-source capsule is authenticated by its 193-file manifest; the
source-bound producer selects the 1250–1750 cal BP window, 31 prepared taxa and
15 sites with positive pollen counts (20,732 counts). EXEBRID and WHH11 have
zero counts in this window and were excluded before fold construction.

The producer uses the author-prepared lake radii and PPE means, diagonal PPE
variances, and fall speeds. The circular basins and homogeneous terrestrial
annuli are declared modeling assumptions, not historical landscape geometry.
The host does not consume off-diagonal PPE covariance. All outcomes had already
been exposed in prior development work; there is no independent vegetation
truth or confirmatory test here.

Whole-site holdout requested 15 folds and three fixed pollen baselines per fold.
Training completed for all 195 fold/site items (168 cache hits, 27 unique
numerical products). All 15 folds refused prediction with `invalid_composition`:
each of the 54 local-cover ring rows in those products has at least one negative
taxon fraction. The minimum was -5.06615 and the maximum was 7.11987; 19 rows
also exceeded one. The fractions sum to one numerically, but they are not valid
compositions. No baseline prediction or score was generated. These values were
neither clipped nor renormalized.

The retained reader independently replays analytical LOVE's local equation from
each product's pollen counts, PPE, regional cover and kernel tables. All 54 rows
agree within `2.67e-15` absolute difference. In 42 rows, 134 taxon cells have
zero local pollen and positive regional correction; their analytical estimate
must be negative because the local pollen term is zero and the regional term is
subtracted. The remaining 12 rows also have negative estimates under the same
equation. This checks the saved products' arithmetic, not the historical basin
assumption or every upstream kernel against original R. The separate retained
[original R reference](../../method-certification/original-r-reference/README.md)
tests the analytical implementation on its bounded cases.

The authenticated 31-taxon parameter profile gives `Filipendula` a fall speed
of **0.006 m/s**. The host's
[`lra-request.v1` validation](../../../../packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra/inputs/validation.py)
requires the named LandClim II GPM-neutral analytical profile when any fall
speed is below 0.01 m/s. Its optimized LOVE route cannot consume this exact
profile without a different parameter or taxon decision. Such a change would
define a new exploratory input and would not resolve the negative analytical
result above. The source-bound next step is a qualified geometry and count
denominator for a Swedish cohort, not an optimizer substitution.

[report.json](report.json) binds the source, experiment and prediction identities
and records the denominators. [folds.csv](folds.csv) retains each refusal;
[cover-diagnostics.csv](cover-diagnostics.csv) retains each authenticated
numerical product's two local ring summaries and equation residuals. The report
reader verifies every prediction and numerical-product manifest before producing
those files.

To reproduce with the private capsule and an empty `artifacts/` destination:

```sh
author_source_root=/path/to/private/source/store/landclim/author-reference
job=artifacts/jobs/author-lra-development-reproduction
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_development \
  --author-source-root "$author_source_root" --output "$job/inputs"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_run \
  --inputs "$job/inputs" --cache-root "$job/cache" --output "$job/predictions"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_report \
  --inputs "$job/inputs" --predictions "$job/predictions" \
  --cache-root "$job/cache" --output "$job/summary"
```

The reproducible outcome is a numerical refusal for this exact source and
assumption set. It does not estimate ecological skill or establish that Nordic
LRA inputs are admissible.

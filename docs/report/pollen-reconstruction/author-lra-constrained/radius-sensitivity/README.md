# English author basin-radius forward sensitivity

We varied each declared circular lake radius by factors 0.8 and 1.2 around
the source profile's radius, while holding the 42 published LRA vegetation
fractions, regional cover, PPE, fall speeds, and training fits fixed. The
original 14 scored sites have assumed radii from 10 to 200 m. We changed the
first forward and inversion annulus inner edges and areas consistently; the
outer edges and all later annuli stayed fixed. This is a target-basin forward
transport diagnostic, not a new LOVE reconstruction or a claim that the
author-example radii represent age-specific surveyed basins.

We [froze 126 pollen predictions](frozen/predictions.json) before opening the
target counts. The unmodified radius reproduces every published forward
pollen fraction exactly. We then [scored all 126 rows](scored/scores.csv) on
the existing 30-taxon count denominator. The unmodified-radius MAE reproduces
the published [42 held-out scores](../scores.csv) within `1e-15`.

| Fixed vegetation method | Radius factor | Site-macro pollen MAE | Site-macro Hellinger |
| --- | ---: | ---: | ---: |
| Training mean | 0.8 | 0.026396 | 0.360975 |
| Training mean | 1.0 | 0.026273 | 0.360671 |
| Training mean | 1.2 | 0.026246 | 0.361927 |
| Nearest site | 0.8 | 0.020960 | 0.283415 |
| Nearest site | 1.0 | 0.021132 | 0.286001 |
| Nearest site | 1.2 | 0.021491 | 0.291210 |
| Inverse distance squared | 0.8 | 0.021032 | 0.283976 |
| Inverse distance squared | 1.0 | 0.021088 | 0.285415 |
| Inverse distance squared | 1.2 | 0.021457 | 0.289825 |

We retain the [machine report](scored/report.json) and per-site scores because
the aggregate moves differently by method and metric. The original study
attempted 15 folds; BECKHAM still has no LRA prediction because three
training fits refused, so this diagnostic scores 14 paired sites. All sites
and target outcomes were already exposed in development. These shifts do not
select a physical radius, quantify chronology or PPE uncertainty, establish
vegetation accuracy, or admit a Swedish core to LRA.

## Paired direct-pollen comparison

We joined the radius scores to the published direct-pollen MAE and Hellinger
rows by target site, method and exact observed raw-row SHA-256. We checked
that the unvaried LRA score and prediction identity reproduce the original
comparison. The [paired rows](paired/paired-scores.csv) and
[summary](paired/report.json) cover 126 matched method/radius/site rows.

| Method | Radius factor | Direct minus LRA MAE | Direct minus LRA Hellinger | Sites favoring direct by MAE |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.8 / 1.0 / 1.2 | −0.005900 / −0.005778 / −0.005750 | −0.078892 / −0.078588 / −0.079845 | 13 / 13 / 13 of 14 |
| Nearest site | 0.8 / 1.0 / 1.2 | −0.001408 / −0.001580 / −0.001939 | −0.027647 / −0.030234 / −0.035443 | 6 / 7 / 7 of 14 |
| Inverse distance squared | 0.8 / 1.0 / 1.2 | −0.002454 / −0.002509 / −0.002878 | −0.040303 / −0.041743 / −0.046152 | 10 / 10 / 9 of 14 |

Negative aggregate differences favor direct pollen. We found that varying
the assumed radius by 20% does not reverse the aggregate direct-pollen
advantage on this matched English development support. Individual sites
disagree, and the direct route used all 14 training pollen sites while LRA
used a regional anchor plus 13 local reconstruction predictors. This is not
an independent model ranking or vegetation-accuracy comparison.

We regenerated the source inputs and 15-site predictions from the qualified
author snapshot. The source experiment hash matched exactly. The fresh
prediction bundle has different run metadata, but all 1,260 retained
vegetation and forward-pollen values match the governed prediction table
exactly. Its 126 radius scores are byte-identical to the governed scores;
only the source and freeze identities in the new run report differ. The
[producer](../radius_sensitivity.py) verifies the candidate bundle members
and every numerical prediction cell against that retained table before it
freezes the radius projections.

To reproduce from the private author snapshot, run these commands from the
repository root with an absent job directory:

```sh
job=artifacts/jobs/author-lra-radius-replay
source_root=/path/to/private/landclim/author-reference
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.essd_reproduction.author_lra_development \
  --author-source-root "$source_root" --output "$job/source-inputs"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/prepare.py \
  --source "$job/source-inputs" --destination "$job/constrained-inputs"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.author_lra_run \
  --inputs "$job/constrained-inputs" --cache-root "$job/cache" \
  --output "$job/predictions"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/radius_sensitivity.py \
  freeze --inputs "$job/constrained-inputs" --predictions "$job/predictions" \
  --output "$job/frozen"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/radius_sensitivity.py \
  score --inputs "$job/constrained-inputs" --predictions "$job/predictions" \
  --frozen "$job/frozen/predictions.json" --output "$job/scored"
```

The producer authenticates the source experiment, prediction bundle members,
every target geometry and each raw count row against the source declarations.
It invokes the installed LRA forward consumer for every projection. Private
author inputs stay outside the repository; the governed outputs preserve the
original prediction and score identities.

To reproduce the downstream comparison from the retained source-locked
scores without private raw files:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/radius-sensitivity/paired_comparison.py \
  --output artifacts/jobs/author-lra-radius-paired-replay
```

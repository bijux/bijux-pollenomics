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

Reproduce with the exact constrained author input and closed-cover prediction
directories named in the [parent study](../README.md). Freeze and retain the
first output before running the score command:

```sh
job=artifacts/jobs/author-lra-radius-replay
inputs=artifacts/jobs/author-lra-slsqp-development/constrained-inputs-300
predictions=artifacts/jobs/author-lra-slsqp-development/closed-cover-predictions
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/radius_sensitivity.py \
  freeze --inputs "$inputs" --predictions "$predictions" \
  --output "$job/frozen"
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/report/pollen-reconstruction/author-lra-constrained/radius_sensitivity.py \
  score --inputs "$inputs" --predictions "$predictions" \
  --frozen "$job/frozen/predictions.json" --output "$job/scored"
```

The producer authenticates the published source experiment and prediction
manifest, each target geometry, and each raw count row against the source
declarations. Its [code](../radius_sensitivity.py) invokes the installed LRA
forward consumer for every projection. Private author inputs stay outside the
repository; these governed outputs preserve prediction and score identities.

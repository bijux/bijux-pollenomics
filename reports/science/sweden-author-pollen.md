# How we held Sweden out on the author pollen taxonomy

We held out all three Swedish EPD/Neotoma lakes in this
[observed-pollen study](../../docs/report/regions/nordic/swedish-author-target-pollen/report.json)
and trained on 81 Danish, Finnish and Norwegian sites. We used the same 31
non-excluded author lookup targets and 500-cal-BP bins as the
[country-held-out study](../../docs/report/regions/nordic/author-target-pollen/README.md).
We predicted each eligible Swedish site-bin with training mean, nearest site
and inverse distance squared. We calculated spatial distances between site
centers. We kept Swedish pollen counts and pollen-derived features out of
the [prediction inputs](../../docs/report/regions/nordic/swedish-author-target-pollen/inputs).

Our [input manifest](../../docs/report/regions/nordic/swedish-author-target-pollen/input-manifest.json)
binds the retained Nordic source profiles, three original Swedish source
transports, the Swedish source mass screen and prepared training/target files
by SHA-256. We stored [target outcomes](../../docs/report/regions/nordic/swedish-author-target-pollen/sealed-outcomes)
separately. We saved and SHA-256-identified
[predictions](../../docs/report/regions/nordic/swedish-author-target-pollen/predictions)
before opening outcomes for the
[scores](../../docs/report/regions/nordic/swedish-author-target-pollen/scores.csv).
We retained derived compositions and counts in gzip
files without copying the private raw author source.

| Target | Source samples | Scored bins | IDW MAE / Hellinger | Nearest MAE / Hellinger | Mean MAE / Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: |
| Abborrtjärnen | 107 | 20 | 0.016018 / 0.266088 | 0.027011 / 0.418772 | 0.015779 / 0.258107 |
| Bussjösjön | 69 | 19 | 0.036493 / 0.483677 | 0.031255 / 0.463496 | 0.040178 / 0.534459 |
| Bökesjön | 52 | 12 | 0.033710 / 0.489568 | 0.029481 / 0.460939 | 0.038889 / 0.560758 |

We recorded **54 attempted site-bins**, **51 scored site-bins** and **three
refused bins** in the [coverage ledger](../../docs/report/regions/nordic/swedish-author-target-pollen/coverage.csv).
We refused bin −1 where fewer than two foreign training sites had positive
target counts. We scored the same 51 bins for all three methods, yielding
**153 method rows**. The equal-site mean MAE is
0.028740 for inverse distance squared, 0.029249 for nearest site and 0.031615
for training mean. Equal-site Hellinger values are 0.413111, 0.447736 and
0.451108, respectively. We retained the contributing units in
[site scores](../../docs/report/regions/nordic/swedish-author-target-pollen/site-scores.csv)
and [taxon diagnostics](../../docs/report/regions/nordic/swedish-author-target-pollen/taxon-diagnostics.csv).

Across all **228** Swedish source samples, we assigned
**221,800 of 240,966** native pollen NISP counts (92.05%); 12,779 are
author-excluded and 6,387 are unmapped. Our earlier Swedish author-parameter
screen covers only **39 bins common to all three sites**. Its 169,013 assigned
of 187,002 native NISP exactly match this study when we restrict both to
those 39 bins. We keep the denominators separate because they cover different
bin support. We also keep this 31-target response separate from the earlier
Swedish 16-label response; their MAEs do not form a paired method comparison.

We treat this as exploratory, prior-exposed direct-pollen interpolation across
country boundaries. We have only three Swedish target sites, no untouched
confirmatory cohort, no independent vegetation truth and **zero LRA
admissions**. The historical lake geometry and decisions in the
[Swedish source review](../../docs/report/pollen-reconstruction/swedish-source-questions.csv)
still govern LRA use.

In our separate [matched training-scope study](sweden-training-scope.md), we
rotate each Swedish lake as a whole-site target and compare the other two
Swedish sites alone with those same sites plus DK/FI/NO training. Its 39
shared bins answer a different question from this study's 51 scored bins
with **all** Swedish sites excluded from training.

To reproduce our result, run from the repository root into absent
directories under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_author_target_pollen prepare \
  --repository . --output artifacts/jobs/swedish-author-target-prepared-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_author_target_pollen predict \
  --prepared artifacts/jobs/swedish-author-target-prepared-replay \
  --output artifacts/jobs/swedish-author-target-predictions-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.swedish_author_target_pollen score \
  --prepared artifacts/jobs/swedish-author-target-prepared-replay \
  --predictions artifacts/jobs/swedish-author-target-predictions-replay \
  --output artifacts/jobs/swedish-author-target-scored-replay
```

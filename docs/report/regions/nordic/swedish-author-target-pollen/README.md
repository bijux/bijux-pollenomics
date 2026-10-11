# Sweden held out on the author pollen taxonomy

This [observed-pollen study](report.json) holds out all three Swedish EPD/Neotoma
lakes while 81 Danish, Finnish and Norwegian sites supply training. It uses the
same 31 non-excluded author lookup targets and 500-cal-BP bins as the
[country-held-out study](../author-target-pollen/README.md). Three fixed methods
predict each eligible Swedish site-bin: training mean, nearest site and inverse
distance squared. Site centers supply spatial distances. No Swedish pollen count
or pollen-derived feature appears in the [prediction inputs](inputs/).

The [input manifest](input-manifest.json) binds the retained Nordic source
profiles, three original Swedish source transports, the Swedish source mass
screen and the prepared training/target files by SHA-256. The
[target outcomes](sealed-outcomes/) are stored separately. The
[predictions](predictions/) were saved and SHA-256 identified before the
[scores](scores.csv) opened those outcomes. The retained gzip files contain
derived compositions and counts, not the private raw author source.

| Target | Source samples | Scored bins | IDW MAE / Hellinger | Nearest MAE / Hellinger | Mean MAE / Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: |
| Abborrtjärnen | 107 | 20 | 0.016018 / 0.266088 | 0.027011 / 0.418772 | 0.015779 / 0.258107 |
| Bussjösjön | 69 | 19 | 0.036493 / 0.483677 | 0.031255 / 0.463496 | 0.040178 / 0.534459 |
| Bökesjön | 52 | 12 | 0.033710 / 0.489568 | 0.029481 / 0.460939 | 0.038889 / 0.560758 |

The [coverage ledger](coverage.csv) records **54 attempted site-bins**, **51
scored site-bins** and **three refused bins** at bin −1 because fewer than two
foreign training sites have positive target counts. All three methods score
the same 51 bins, yielding **153 method rows**. The equal-site mean MAE is
0.028740 for inverse distance squared, 0.029249 for nearest site and 0.031615
for training mean. Equal-site Hellinger values are 0.413111, 0.447736 and
0.451108, respectively. [Site scores](site-scores.csv) and
[taxon diagnostics](taxon-diagnostics.csv) retain the contributing units.

Across all **228** Swedish source samples, the author targets receive
**221,800 of 240,966** native pollen NISP counts (92.05%); 12,779 are
author-excluded and 6,387 are unmapped. The previously reported Swedish
author-parameter screen covers only **39 bins common to all three sites**:
its 169,013 assigned of 187,002 native NISP exactly match this study when
restricted to those 39 bins. These different denominators describe different
bin support, not a source discrepancy. The 31-target response also differs
from the earlier Swedish 16-label response, so their MAE values are not a
paired method comparison.

This is exploratory, prior-exposed direct-pollen interpolation across country
boundaries. It has only three Swedish target sites, no untouched confirmatory
cohort, no independent vegetation truth and **zero LRA admissions**. The
historical lake geometry and source decisions in the [Swedish source review](../../../pollen-reconstruction/swedish-source-questions.csv)
still govern LRA use.

Reproduce from the repository root into absent directories under `artifacts/`:

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

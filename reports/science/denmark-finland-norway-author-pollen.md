# What we predicted from Nordic pollen on the 31 author targets

We asked how observed pollen transfers to a country excluded from training.
In our [source-bound study](../../docs/report/regions/nordic/author-target-pollen/report.json),
we used the 31 non-excluded targets in the authors' exact 10,788-row
[LandClim II taxonomy lookup](https://github.com/rmfyfe/landclimII/blob/57ead2e2fcc493d099be4e5a3092fc396e1c3d3a/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv).
We kept the same selected Danish, Finnish and Norwegian Neotoma/EPD samples
and 500-cal-BP bins as the [16-label study](../../docs/report/regions/nordic/direct-pollen/RESULTS.md).
For each excluded country, we trained on three Swedish EPD lake profiles and
the other two Nordic countries. We removed the target country from every
training input. The [input manifest](../../docs/report/regions/nordic/author-target-pollen/input-manifest.json)
hashes six predictor inputs and three separate [target-outcome files](../../docs/report/regions/nordic/author-target-pollen/sealed-outcomes).
The predictor read only the six files in [inputs](../../docs/report/regions/nordic/author-target-pollen/inputs).
We saved and SHA-256-identified [predictions](../../docs/report/regions/nordic/author-target-pollen/predictions)
before opening target counts for [scoring](../../docs/report/regions/nordic/author-target-pollen/scores.csv).
We stored the large input, target and prediction tables as deterministic
gzip-compressed JSON with checked identities.

| Target country | Sites | Selected samples | Native NISP assigned to author targets | Scored site-bins / attempted | Refused bins | Best fixed baseline by site-macro MAE; Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Denmark | 1 | 91 | 122,998 / 129,768 (94.78%) | 24 / 24 | 0 | nearest site: 0.023242; 0.342996 |
| Finland | 28 | 1,797 | 1,229,019 / 1,260,281 (97.52%) | 435 / 435 | 0 | nearest site: 0.017335; 0.268166 |
| Norway | 52 | 3,544 | 2,018,295 / 2,286,020 (88.29%) | 1,084 / 1,178 | 94 | inverse distance squared: 0.019459; 0.303587 |

We used three fixed methods: training mean, nearest site and inverse distance
squared. All **1,543** scored site-bins have the same three methods, giving
**4,629** [method scores](../../docs/report/regions/nordic/author-target-pollen/scores.csv). The 94 refused Norwegian bins have
fewer than two training site groups with positive 31-target counts. The
[coverage ledger](../../docs/report/regions/nordic/author-target-pollen/coverage.csv) retains every attempted target. We first averaged eligible bins within each physical site; the
[site scores](../../docs/report/regions/nordic/author-target-pollen/site-scores.csv) and [taxon diagnostics](../../docs/report/regions/nordic/author-target-pollen/taxon-diagnostics.csv)
retain the contributing units. We selected no candidate using target outcomes.

We treat this as exploratory: we had inspected country outcomes in the
16-label analysis before designing the broader response. Our 31 targets
aggregate native pollen names. We kept author-excluded and unmapped NISP
outside the scored subcomposition and accounted for them in the
[taxonomy ledger](../../docs/report/regions/nordic/author-taxonomy-mass/README.md). Its MAE cannot be
compared numerically with the 16-label MAE as though the target fractions had
the same denominator or axis. Denmark has one site, so the Danish score does
not establish between-site Danish skill. Site-center distances are used;
age-specific basin support was not asserted. These are observed-pollen
predictions, not REVEALS/LOVE outputs or independent vegetation validation.
We admitted **zero samples to LRA** through this study.

For Dalmutladdo, we also applied a
[strict LegacyAge interval screen](../../docs/report/regions/nordic/dalmutladdo-author-target-age-interval/README.md)
to the already frozen Norway-excluded 31-target predictions. Only two of
72 samples have their full reported 95% age interval inside their original
500-year bin. Six predictions across those two bins remain scored; 20 of
22 originally scored Dalmutladdo bins have no eligible sample. Inverse
distance squared has a two-bin MAE of 0.006445, compared with 0.006341
for the parent's complete outcome compositions on those same bins. The
sample-matched nominal score is identical to the strict score because
neither retained sample changes bin. These small support-dependent numbers
do not establish temporal transfer skill or admit LRA inputs.

We retained derived target counts and predictions without copying the private
author source or raw Neotoma transports. We recorded the source identities and
author lookup hash in the input manifest. Our
[Neotoma](../../docs/public/pollenomics-data/sources/neotoma.md) and
[LandClim](../../docs/public/pollenomics-data/sources/landclim.md) reviews
record the separate source and attribution boundaries.

To reproduce our result, run from the repository root into three absent
artifacts directories:

The checked-in input manifest pins the direct-pollen manifest at product
revision `6cf0e1134193174f214cd280a96e60b08fadf22f`. Use that revision
for exact receipt replay. A later runner-only change to the direct-pollen
manifest leaves the selected samples and numeric results unchanged, but a
fresh current-tree preparation records a different source hash.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_author_target_pollen prepare \
  --repository . \
  --author-source-root /path/to/private/landclim/author-reference \
  --output artifacts/jobs/nordic-author-target-pollen-prepared-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_author_target_pollen predict \
  --prepared artifacts/jobs/nordic-author-target-pollen-prepared-replay \
  --output artifacts/jobs/nordic-author-target-pollen-predictions-replay
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_author_target_pollen score \
  --prepared artifacts/jobs/nordic-author-target-pollen-prepared-replay \
  --predictions artifacts/jobs/nordic-author-target-pollen-predictions-replay \
  --output artifacts/jobs/nordic-author-target-pollen-scored-replay
```

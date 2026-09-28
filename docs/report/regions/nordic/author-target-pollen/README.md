# Nordic observed pollen on the 31 author taxonomy targets

This [source-bound study](report.json) reruns the country-held-out observed-pollen
question on the 31 non-excluded targets in the authors' exact 10,788-row
[LandClim II taxonomy lookup](https://github.com/rmfyfe/landclimII/blob/57ead2e2fcc493d099be4e5a3092fc396e1c3d3a/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv).
It uses the same selected Danish, Finnish and Norwegian Neotoma/EPD samples and
500-cal-BP bins as the [16-label study](../direct-pollen/RESULTS.md). Three
Swedish EPD lake profiles and the other two Nordic countries supply training
for each excluded country. The target country is absent from every training
input; the [input manifest](input-manifest.json) hashes six predictor inputs
and three separately retained [target-outcome files](sealed-outcomes/). The
predictor reads only the six files in [inputs](inputs/). [Predictions](predictions/)
were saved and SHA-256 identified before [scores](scores.csv) used target counts.
The large input, target and prediction tables are deterministic gzip-compressed
JSON so their checked identities can be retained without a large text diff.

| Target country | Sites | Selected samples | Native NISP assigned to author targets | Scored site-bins / attempted | Refused bins | Best fixed baseline by site-macro MAE; Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Denmark | 1 | 91 | 122,998 / 129,768 (94.78%) | 24 / 24 | 0 | nearest site: 0.023242; 0.342996 |
| Finland | 28 | 1,797 | 1,229,019 / 1,260,281 (97.52%) | 435 / 435 | 0 | nearest site: 0.017335; 0.268166 |
| Norway | 52 | 3,544 | 2,018,295 / 2,286,020 (88.29%) | 1,084 / 1,178 | 94 | inverse distance squared: 0.019459; 0.303587 |

The three fixed methods are training mean, nearest site and inverse distance
squared. All **1,543** scored site-bins have the same three methods, giving
**4,629** [method scores](scores.csv). The 94 refused Norwegian bins have
fewer than two training site groups with positive 31-target counts. The
[coverage ledger](coverage.csv) retains every attempted target. Equal-site
averages first average eligible bins within a physical site; the
[site scores](site-scores.csv) and [taxon diagnostics](taxon-diagnostics.csv)
retain the contributing units. No candidate was selected using target outcomes.

This study is exploratory: the country outcomes had been inspected in the
16-label analysis before this broader response was designed. The 31 targets
aggregate native pollen names, while author-excluded and unmapped NISP stay
outside the scored subcomposition and remain accounted for in the
[taxonomy ledger](../author-taxonomy-mass/README.md). Its MAE cannot be
compared numerically with the 16-label MAE as though the target fractions had
the same denominator or axis. Denmark has one site, so the Danish score does
not establish between-site Danish skill. Site-center distances are used;
age-specific basin support was not asserted. These are observed-pollen
predictions, not REVEALS/LOVE outputs or independent vegetation validation.
**Zero samples are admitted to LRA** by this study.

The retained files contain derived target counts and predictions; private
author source and raw Neotoma transports are not copied here. The source
identities and author lookup hash are recorded in the input manifest. The
[Neotoma](../../../../public/pollenomics-data/sources/neotoma.md) and
[LandClim](../../../../public/pollenomics-data/sources/landclim.md) reviews
record the separate source and attribution boundaries.

Reproduce from the repository root into three absent artifacts directories:

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

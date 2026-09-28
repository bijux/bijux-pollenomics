# Selected Nordic observed-pollen transfer

The [training-only development search](../pollen-development/README.md) chose
one predictor for each excluded target country. The prediction command read the
country-excluded training profiles and target site/age-bin metadata, then saved
[hash-bound predictions](freeze.json) before a separate scoring command opened
target pollen observations. Denmark selected inverse-distance-squared (IDW);
Finland selected CLR RBF at the 0.75 positive training-pairwise-distance
quantile with ridge 0.1; Norway selected the 0.50 quantile with ridge 0.1.
The frozen [DK](predictions-DK.json), [FI](predictions-FI.json) and
[NO](predictions-NO.json) files retain every attempted prediction and refusal.

The [paired score ledger](paired-scores.csv) uses the same site-bins and native
16-label closed pollen denominator as the
[published fixed-method comparison](../direct-pollen/RESULTS.md). The
[report](report.json) gives equal-site macro scores; negative differences mean
lower error for the selected predictor. All paired rows match the fixed result's
target count denominators and training site IDs.

| Excluded country | Selected method | Scored sites/bins | Selected MAE | IDW MAE | Selected minus IDW | Fixed RBF MAE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Denmark | IDW | 1 / 24 | 0.033022 | 0.033022 | 0 | 0.039220 |
| Finland | RBF q75, ridge 0.1 | 28 / 435 | 0.034871 | 0.034375 | +0.000496 | 0.082477 |
| Norway | RBF q50, ridge 0.1 | 52 / 1,084 | 0.033942 | 0.027012 | +0.006930 | 0.034496 |

The selected RBF improves over the earlier fixed RBF in Finland and slightly
in Norway, but **does not improve on IDW transfer** in either country. It has
lower site-average MAE than IDW at 11 of 28 Finnish sites and 8 of 52
Norwegian sites. Norway has 1,178 candidate site-bins, 1,177 with positive
closed-axis counts, 1,084 predicted and scored, and 94 refused bins under the
same support rule as the fixed study. Denmark has one physical site, so its
between-site uncertainty cannot be estimated here.

This is a **prior-exposed development comparison**. The country outcomes were
seen before this protocol was designed, even though each run's model selection
used only its excluded-country training profiles. Its scores cannot be presented
as independent confirmation or as measured vegetation accuracy. The response
is observed pollen composition; no PPE, basin geometry, HYDE or LRA output
enters this calculation.

To replay, first regenerate the exact source profiles as described in the
[development search](../pollen-development/README.md). With absent destinations
under `artifacts/`, run the prediction and scoring commands separately:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_pollen_transfer predict \
  --repository . --inputs artifacts/jobs/nordic-development-inputs \
  --output artifacts/jobs/nordic-selected-pollen-freeze-replay
freeze_sha=$(shasum -a 256 artifacts/jobs/nordic-selected-pollen-freeze-replay/freeze.json | cut -d ' ' -f 1)
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic_pollen_transfer score \
  --repository . --inputs artifacts/jobs/nordic-development-inputs \
  --frozen artifacts/jobs/nordic-selected-pollen-freeze-replay \
  --freeze-sha256 "$freeze_sha" \
  --output artifacts/jobs/nordic-selected-pollen-score-replay
```

The score command verifies the supplied freeze digest, producer, selection,
published fixed-study manifest and all three prediction/input hashes before
reading any target observations. [Neotoma source terms and attribution](../../../../public/pollenomics-data/sources/neotoma.md)
apply to the observed counts and source investigators.

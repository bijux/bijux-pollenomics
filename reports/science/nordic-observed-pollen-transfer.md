# What happened when we transferred the selected Nordic pollen predictors

Our [training-only development search](nordic-observed-pollen-selection.md)
selected one predictor for each excluded country. We read country-excluded
training profiles and target site/age-bin metadata, saved
[hash-bound predictions](../../docs/report/regions/nordic/selected-pollen-transfer/freeze.json),
and opened target pollen only in a separate scoring step. Training selected
inverse-distance-squared (IDW) for Denmark, CLR RBF at the 0.75 positive
training-pairwise-distance quantile with ridge 0.1 for Finland, and the 0.50
quantile with ridge 0.1 for Norway. We retained every attempted prediction
and refusal in the frozen [DK](../../docs/report/regions/nordic/selected-pollen-transfer/predictions-DK.json),
[FI](../../docs/report/regions/nordic/selected-pollen-transfer/predictions-FI.json)
and [NO](../../docs/report/regions/nordic/selected-pollen-transfer/predictions-NO.json)
files.

We scored on the same site-bins and native 16-label closed pollen denominator
as the [published fixed-method comparison](../../docs/report/regions/nordic/direct-pollen/RESULTS.md).
Our [paired score ledger](../../docs/report/regions/nordic/selected-pollen-transfer/paired-scores.csv)
matches its target count denominators and training site IDs. Our
[report](../../docs/report/regions/nordic/selected-pollen-transfer/report.json)
gives equal-site macro scores; negative differences indicate lower error
for the selected predictor.

| Excluded country | Selected method | Scored sites/bins | Selected MAE | IDW MAE | Selected minus IDW | Fixed RBF MAE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Denmark | IDW | 1 / 24 | 0.033022 | 0.033022 | 0 | 0.039220 |
| Finland | RBF q75, ridge 0.1 | 28 / 435 | 0.034871 | 0.034375 | +0.000496 | 0.082477 |
| Norway | RBF q50, ridge 0.1 | 52 / 1,084 | 0.033942 | 0.027012 | +0.006930 | 0.034496 |

We observed lower MAE for the selected RBF than the earlier fixed RBF in
Finland and slightly lower in Norway, but **no improvement over IDW transfer**
in either country. The selected RBF has lower site-average MAE than IDW at
11 of 28 Finnish sites and 8 of 52 Norwegian sites. Norway has 1,178
candidate site-bins, 1,177 with positive closed-axis counts, 1,084 predicted
and scored, and 94 refused under the fixed study's support rule. Denmark has
one physical site, so we cannot estimate its between-site uncertainty here.

We label this a **prior-exposed development comparison**. We saw the country
outcomes before designing the protocol, although each run selected its model
using only excluded-country training profiles. We therefore do not claim
independent confirmation or measured vegetation accuracy. Our response is
observed pollen composition; we used no PPE, basin geometry, HYDE or LRA
output in this calculation.

To replay these retained results, use the authenticated historical
[development preparation](../../data/neotoma/pollen-development/custody.json)
and [transfer metadata](../../data/neotoma/selected-pollen-transfer/custody.json).
The replay stages their original publication manifest, training profiles,
target metadata, fixed scores and Neotoma observations under `artifacts/`.
It runs the current producer's prediction command first, pins the newly
written freeze, and then opens target observations in its separate score
command. The three prediction files and paired score ledger must match the
historical bytes. The current freeze records the current producer hash,
and the current report records that freeze's hash; all other values must
match the historical receipts.

The original [freeze](../../data/neotoma/selected-pollen-transfer/historical-freeze.json)
and [score report](../../data/neotoma/selected-pollen-transfer/historical-report.json)
remain separate historical receipts. Their publication and prepared-input
hashes identify the saved development study. Regenerating preparation from
the present direct-pollen manifest creates a different lineage.

Use an absent destination beneath the repository's `artifacts/` directory:

```sh
repository=$(pwd -P)
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.nordic.nordic_selected_transfer_replay \
  --repository "$repository" \
  --output "$repository/artifacts/jobs/nordic-selected-pollen-replay"
```

We verify the supplied freeze digest, producer, selection, published
fixed-study manifest and all three prediction/input hashes before reading
target observations. We apply [Neotoma source terms and attribution](../../docs/public/pollenomics-data/sources/neotoma.md)
to the observed counts and source investigators.

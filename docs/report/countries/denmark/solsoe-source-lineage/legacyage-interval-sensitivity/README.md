# Solsø pollen predictions under strict LegacyAge age intervals

We used the [exact-depth LegacyAge S5 source join](../legacyage-chronology/README.md)
to check the age support of the existing [Denmark country-held-out observed-pollen
predictions](../../../../regions/nordic/direct-pollen/RESULTS.md). This is a
**prior-exposed development sensitivity** of a closed **16-literal-label**
Neotoma pollen subcomposition. Its denominator is the sum of those labels'
native NISP counts, not all pollen or vegetation cover. It reuses the four
already frozen methods without refitting or selecting a new model.

The age rule retains a source-comparable sample only when its full closed S5
95% range fits inside its original half-open 500-cal-BP Neotoma age bin. No
age interpolation, posterior draw or reassignment to a neighboring bin is
made. [Sample support](sample-support.csv) records every core and refusal.

| Source support | Samples |
| --- | ---: |
| Two Solsø cores with exact S5 depth matches | 92 |
| Refused Neotoma calibrated age with negative younger bound | 1 |
| Comparable samples in the parent cohort | 91 |
| Comparable intervals crossing a bin boundary | 76 |
| Full intervals inside their original bin | 15 |

Fourteen retained samples come from SOLSOE81 (Neotoma dataset 4445), and one
from SOLSOE83 (dataset 4446). They occupy eight original bins: 2, 3, 4, 5, 6,
12, 15 and 16. The parent has 24 scored Solsø bins; **16 have no retained
sample** under this rule. All 32 reused prediction rows and their prior
Denmark-excluded training identities are pinned in [predictions.json](predictions.json)
and [protocol.json](protocol.json). The freeze step opens no target pollen
observations.

| Fixed method | Strict eight-bin MAE | Parent MAE, same bins | Strict Hellinger | Parent Hellinger, same bins |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.043627 | 0.042678 | 0.468875 | 0.465636 |
| Nearest site | 0.032310 | 0.032104 | 0.386071 | 0.384834 |
| Inverse distance squared | 0.038178 | 0.037560 | 0.435518 | 0.432374 |
| CLR/RBF ridge | 0.040337 | 0.040081 | 0.414663 | 0.414330 |

These are one-site, eight-bin descriptive averages, not uncertainty intervals
or a model ranking. The [score ledger](scores.csv) retains every method/bin
pair and its sample count. The nominal score on exactly the retained samples
equals the strict-interval score because every retained sample stays in its
original bin. The parent columns score the full original pollen composition
in those same eight bins. Their small differences reflect **sample support
restriction**, not an age-driven change in bin membership or a better fit.

The [producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/replay.py) reconstructs all 24 parent bin counts from the
original Neotoma observation part after the predictions have been frozen. It
checks each parent bin's sample, total NISP and 16-label count denominator.
The [machine report](report.json) retains source hashes and denominators.
Replay from the repository root into an absent disposable output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/replay.py \
  freeze --repository . --output artifacts/jobs/solsoe-legacyage-pollen-check
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/replay.py \
  score --repository . --output artifacts/jobs/solsoe-legacyage-pollen-check
```

LegacyAge is an alternative chronology; this result does not identify the
historical LandClim age model or its 79 selected Solsø samples. It does not
admit LRA input or validate vegetation against independent field observations.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Solsø two-core native counts/ages, source lineage and unresolved historical79 versus current92 selection.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md) (source SHA-256 `e6b29b0cfd3e763b8bc38ca390f894b0cc5c583259040a3e3c9fef2bf363fe71`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

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

**Supported claim.** This prior-exposed one-site development sensitivity reuses 4 fixed methods on the closed 16 literal pollen labels native-NISP subcomposition under strict full 95%-interval containment.

**Unsupported claim.** It supplies neither independent-site uncertainty, an untouched model ranking, measured vegetation accuracy, age posterior, historical LandClim chronology nor LRA admission.

**Actual verification performed.** Read the retained protocol,report and score/sample ledgers; checked 92 sample decisions,15 retained in 8 bins and 32 method/bin predictions. No refit, private taxonomy mapping or fresh score producer was run.

**Remaining input or review.** A historical interpretation still needs the 79 author samples/chronology and dated basins; an accuracy claim needs qualified independent observations and a fresh predeclared evaluation.

**Cause category.** Prior-exposed restricted-support chronology sensitivity.

**Consequence.** Nearest-site strict MAE 0.032310 versus parent same-bin 0.032104; all four strict MAEs are slightly worse than their parent same-bin values. The same retained samples stay in their nominal bins, so no improvement can be credited to age reassignment.

**Precise next acceptance route.** Replay the exact frozen 16 literal pollen labels protocol/Denmark-excluded predictions before opening observations, then compare strict and nominal scores on identical samples; retain separate 16/31 target denominators.

**Negative or refused result.** One negative source-age refusal and 76 crossing intervals remain;16 of 24 parent bins have no retained sample. The source restriction is not repaired by interpolating ages.

**Matched denominator.** 92 source samples=91 comparable+1 refused;91=15 contained+76 crossing;15=14 SOLSOE81 + 1 SOLSOE83; 8 of 24 bins supported,32 reused predictions=4 methods×8 bins;closed 16 literal pollen labels, not vegetation cover.

Qualified authored reader SHA-256: `428b1fc74cdb582a4f51a6cef7034f1ff949e54dea107d6aaf87c4b3da86cb5b`.

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/report.json](report.json) (SHA-256 `74973466ec934c81b0db2c424927cbcdbbe033e8bb96c39428940a6f3c490206`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/protocol.json](protocol.json) (SHA-256 `3598c4d8ae3c2c3249e5c562612f4c396463d37568e6d35c8267d01610f61f85`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/sample-support.csv](sample-support.csv) (SHA-256 `fa5c7a3f74c2f750d3f4a3f4cea18382aeab9970c87f6321342b569d3365c619`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/scores.csv](scores.csv) (SHA-256 `67b6170d7e41d9488b59a1de92ddd4774f9d4bb2a4601a9580c8c8113a2cf851`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/legacyage-interval-sensitivity/predictions.json](predictions.json) (SHA-256 `b9b3e3ca2c1fb439d29b20fc0e0299b7d200a802d3092ca9d15a35accb7c3a1e`).

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md) (source SHA-256 `3f8a2b8a26f84b4029a7f1e3761a4eac3e9a7a07514a375d5aa5cbc1781a7caf`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

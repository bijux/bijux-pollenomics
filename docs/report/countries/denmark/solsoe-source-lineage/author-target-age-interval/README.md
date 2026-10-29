# Solsø age support on the 31 author pollen targets

We applied the [primary LegacyAge exact-depth join](../legacyage-chronology/README.md)
to the separate [Nordic author-target observed-pollen study](../../../../regions/nordic/author-target-pollen/README.md).
This is a **prior-exposed development sensitivity** of a closed subcomposition
of **31 author taxonomy targets**, with author-assigned native pollen NISP as
its denominator. The [16-literal-label sensitivity](../legacyage-interval-sensitivity/README.md)
has a different response and denominator; its scores are not combined here.

The original 31-target Danish cohort selects exactly the 91 Solsø samples
with comparable calibrated Neotoma ages from both cores. The S5 join has 92
exact sample-depth matches; the remaining sample, `352996`, retains its
negative-bound age refusal. We kept a comparable sample only when its entire
closed S5 95% interval lies inside its original half-open 500-cal-BP bin.
There is no age interpolation, posterior draw or bin reassignment.

| Source support | Samples |
| --- | ---: |
| Exact Solsø sample-depth joins, both cores | 92 |
| Refused calibrated source age | 1 |
| Comparable samples in the 31-target parent | 91 |
| Intervals crossing a bin boundary | 76 |
| Full intervals within the original bin | 15 |

The [sample ledger](sample-support.csv) preserves all 92 decisions. The 15
retained samples include 14 from SOLSOE81 and one from SOLSOE83. They occupy
eight nominal bins: 2, 3, 4, 5, 6, 12, 15 and 16. The parent scores 24 Solsø
bins; **16 have no sample** under this strict rule. The
[protocol](protocol.json) pins the author-target axis, source age join,
Denmark-excluded training input and prediction hashes. All **24
reused prediction rows** for the three fixed methods are in
[predictions.json](predictions.json). The freeze step opens no target pollen
observations.

| Fixed method | Strict eight-bin MAE | Parent MAE, same bins | Strict Hellinger | Parent Hellinger, same bins |
| --- | ---: | ---: | ---: | ---: |
| Training mean | 0.034878 | 0.035023 | 0.491619 | 0.490921 |
| Nearest site | 0.025673 | 0.025513 | 0.357172 | 0.356094 |
| Inverse distance squared | 0.027231 | 0.027082 | 0.405523 | 0.405143 |

These are one-site, eight-bin descriptive averages, not independent-site
uncertainty intervals or a model ranking. The [score ledger](scores.csv)
shows every method/bin pair. Scores on the same retained samples using their
original nominal bins exactly match the strict-interval scores, because no
retained sample changes bins. The parent columns use complete original pollen
compositions in those same eight bins. Their differences reflect **sample
support restriction**, not age reassignment or a new fit.

The [producer](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/replay.py) maps the original Neotoma observation counts through
the exact author taxonomy lookup after predictions are frozen. It checks all
24 reconstructed parent bins against the sealed author-target counts and
assigned, excluded and unmapped mass. The [machine report](report.json)
records source identities, coverage and results. Replay from the repository
root into an absent disposable output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/replay.py \
  freeze --repository . --output artifacts/jobs/solsoe-author-age-check
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
.venv/bin/python docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/replay.py \
  score --repository . \
  --author-source-root ../bijux-pollenomics-data/landclim/author-reference \
  --output artifacts/jobs/solsoe-author-age-check
```

LegacyAge is an alternative chronology. This result does not establish the
historical LandClim age model or its 79 selected Solsø samples, supply basin
geometry, admit LRA input or validate measured vegetation.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Solsø two-core native counts/ages, source lineage and unresolved historical79 versus current92 selection.

**Supported claim.** This prior-exposed one-site development sensitivity reuses 3 fixed methods on the closed 31 author taxonomy targets native-NISP subcomposition under strict full 95%-interval containment.

**Unsupported claim.** It supplies neither independent-site uncertainty, an untouched model ranking, measured vegetation accuracy, age posterior, historical LandClim chronology nor LRA admission.

**Actual verification performed.** Read the retained protocol,report and score/sample ledgers; checked 92 sample decisions,15 retained in 8 bins and 24 method/bin predictions. No refit, private taxonomy mapping or fresh score producer was run.

**Remaining input or review.** A historical interpretation still needs the 79 author samples/chronology and dated basins; an accuracy claim needs qualified independent observations and a fresh predeclared evaluation.

**Cause category.** Prior-exposed restricted-support chronology sensitivity.

**Consequence.** Nearest-site strict MAE 0.025673 versus parent same-bin 0.025513; differences reflect restricted source composition. The same retained samples stay in their nominal bins, so no improvement can be credited to age reassignment.

**Precise next acceptance route.** Replay the exact frozen 31 author taxonomy targets protocol/Denmark-excluded predictions before opening observations, then compare strict and nominal scores on identical samples; retain separate 16/31 target denominators.

**Negative or refused result.** One negative source-age refusal and 76 crossing intervals remain;16 of 24 parent bins have no retained sample. The source restriction is not repaired by interpolating ages.

**Matched denominator.** 92 source samples=91 comparable+1 refused;91=15 contained+76 crossing;15=14 SOLSOE81 + 1 SOLSOE83; 8 of 24 bins supported,24 reused predictions=3 methods×8 bins;closed 31 author taxonomy targets, not vegetation cover.

Qualified authored reader SHA-256: `d02da3e5be4aaf7289e95ba7e48e97893d95eb6d69a8dffc11574d07502695d8`.

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/report.json](report.json) (SHA-256 `c78342a1490638d7aa31614d12015d5353405c0ad35b503b55d974adeed5111b`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/protocol.json](protocol.json) (SHA-256 `45dd6fc90b8550f1e4758007030d4987044fda49bba5eea2ecdd9862302ed7ed`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/sample-support.csv](sample-support.csv) (SHA-256 `fa5c7a3f74c2f750d3f4a3f4cea18382aeab9970c87f6321342b569d3365c619`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/scores.csv](scores.csv) (SHA-256 `fa726106e254b41ac60462dea6d1eeb69ce82b661970bcc9e24b85751b6d7405`).

- [Retained qualification evidence: docs/report/countries/denmark/solsoe-source-lineage/author-target-age-interval/predictions.json](predictions.json) (SHA-256 `0747fd1661a08c9e77035dbc4d50d242fb005a78be9ad4ea2593000bc34070c9`).

- [Canonical scientific account: reports/science/solsoe-lra-input.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/solsoe-lra-input.md) (source SHA-256 `99e7ca4e9d88391f808fec8665108601b6956fa9627b8db6991682d6c715131f`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

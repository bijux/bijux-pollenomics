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

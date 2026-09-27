# Synthetic change time and first observed events

[Retained report](report.json) consumes the public `estimate_first_observed`
estimator with fabricated sample sequences and independently declared step-change
truth at 5500 cal BP. The estimator accepts native samples and an event identity
template. It does not accept ecological change truth or scoring parameters.

## Fixed profiles and source support

The synthetic signal is zero before the declared change and five at and after it.
Dense observation ages are `[5600, 5550, 5500, 5450, 5400]`; sparse ages are
`[5700, 5600, 5400, 5200]`. These schedules and all 19 attempts are fixed before
scoring. No profile threshold or tolerance is selected from the resulting errors.

| Profile | Native condition |
|---|---|
| `reported_positive_v1` | Valid source value greater than zero |
| `count_ge_3_v1` | Integral count at least three |
| `percentage_ge_1_v1` | Percentage at least one, with an explicit positive native denominator |
| `two_consecutive_positive_v1` | Two positive observations in adjacent governed sample positions |

Each attempt retains required feature, source family, source snapshot identity,
original values, units, measure kinds, percentage
denominators, collection identity, sample positions, chronology claim identifiers,
comparability statuses, and canonical age bounds. Mixed units are not combined.
The synthetic percentage denominator is explicitly 100; it is not an approved
real-source pollen-sum definition. A profile declares a calculation rule and does
not provide empirical threshold validation, taxon mapping, or source admission.

The estimator requires every sample's feature, source family and source snapshot
to match the claimed event template, including zero-valued and later unselected
samples. Mixed phenomena or stale source snapshots refuse the complete attempt
before estimation. This binding does not approve a real taxon or pollen mapping.

The estimator requires one site, one collection, compatible native measurement
semantics and sample-level subjects. It uses the source's explicit order with
definite canonical age ordering, never interval midpoints. Noncomparable ages,
missing ages and overlapping chronology refuse the sequence; numeric ages do not
silently acquire comparable status. Site envelopes cannot become sample events.
Duplicate sample identities/order are refused. Missing positions and intervening
negative values cannot manufacture consecutive positive samples.

The numeric uncalibrated radiocarbon control retains each raw age and its source
unit, with `context_only` status and null canonical bounds. It is explicitly
refused, not converted into calendar BP or collapsed into an absent raw age.

## All attempts and their outcomes

| Attempts | Number | Result against independent truth |
|---|---:|---|
| Dense count profiles | 3 | First observed age 5500; exact change recovery |
| Sparse positive and persistence profiles | 2 | First observed age 5400; detection delayed 100 years |
| Dense percentage profile | 1 | First observed age 5500; exact change recovery |
| Fixed cyclic sample-value shuffle | 1 | First observed age 5600; falsely early by 100 years |
| Isolated and terminal positive controls | 2 | Insufficient persistence; no event |
| Missing chronology, overlapping ages, and uncalibrated native ages | 3 | Chronology refusals; no event |
| Site envelopes, mixed native units, unknown percentage denominator | 3 | Explicit input refusals; no event |
| No-change negative control | 1 | Threshold not met; no event |
| Mixed feature, different source family, stale source snapshot | 3 | Ownership refusals; no event |

The report retains all **19 attempts: seven estimates and 12 refusals**. Four
estimates recover the true change exactly and three are biased. All 19 prospective
calculation/refusal expectations pass; that count does not imply that all change
times were recovered. Mean absolute error across the seven estimates, including
the shuffled negative control, is `300/7 = 42.857142857142854 years`. Refused attempts
remain in the requested denominator and have null errors, not zero error.

Prediction outputs and their input hashes are frozen before scoring. Changing the
scoring truth leaves every native sample and estimator output unchanged. The
selected event carries the actual selected sample's chronology and all supporting
observation IDs. Two adjacent positives establish this profile's observed
persistence criterion, not continuous presence between dated observations.

## Reproduce and interpret

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.lra_validation.change_time_challenge \
  --output docs/report/synthetic-validation/change-time/report.json
```

The event is labelled **first observed in governed data**. It estimates an observed
sample event, not an interpolated ecological change time or the global first
appearance. This independent synthetic scoring exposes sampling and shuffle bias;
it does not establish real-data accuracy, confidence interval coverage, continuous
presence, or historical spread.

Focused command receipts and logs live under
`artifacts/jobs/lra-synthetic-change-time/`. Numerical LRA parity and R execution
are not changed by this sample-event estimator.

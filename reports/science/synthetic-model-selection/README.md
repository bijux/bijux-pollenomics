# Why the synthetic parameter winner is not our LRA recommendation

## Our decision

We retained a historical 12-trial synthetic development result because it
answers a narrow question about the installed host's behavior. We did not
adopt its winning parameter set for English, Swedish or four-country LRA.
The independent finite-cell truth generator used an inverse-square deposition
law, while the installed REVEALS calculation used its own transport kernel.
Changing PPE or transport in that comparison can compensate for a difference
between the two equations. A lower score against that synthetic truth is not
evidence that the changed parameter is ecologically better.

## What we ran and observed

The retained [policy](policy.json) fixed two development cases, three
broadleaf-PPE scales (0.8, 1.0 and 1.2) crossed with `lsm unstable` and
`gpm neutral` distance weighting, a 175 m circular lake radius, the source
oracle's other PPE and fall speeds, and a one-million-grain deterministic
count conversion. The metric was mean absolute vegetation-fraction error
averaged equally over the two cases. Selection required both cases to
complete, then broke ties by maximum case error and candidate ID. It had no
final-test access or ecological acceptance threshold.

All 12 trials completed without a refusal or failure. The exact
[historical result](report.json) records these eligible candidates:

| Candidate | Mean MAE, fraction | Largest case MAE, fraction |
| --- | ---: | ---: |
| `lsm-ppe080` | 0.039862 | 0.043250 |
| `lsm-ppe100` | 0.043548 | 0.047157 |
| `gpm-ppe080` | 0.049603 | 0.054787 |
| `lsm-ppe120` | 0.066515 | 0.069737 |
| `gpm-ppe100` | 0.067563 | 0.073440 |
| `gpm-ppe120` | 0.091482 | 0.096790 |

`lsm-ppe080` was best **within this declared two-case synthetic candidate
set**. Its mean error was 0.039861593480655426 in vegetation-fraction units.
The report identifies source commit
`d915d1709d3c8fca4680f70958452860d578d5d1`, installed backend
`python-host-lra-0.1.9.dev74`, policy SHA-256
`cb954fdd8b03b66bd1efebf36db41608a1a051b02dc2ab8b4b6eceba3648a395`
and independent oracle SHA-256
`c53291b9be045fef04334533a8a7f40f8811d7f49c809745522409db8b94aff8`.
We copied the policy and result byte for byte from the historical run into
this owned report. The result JSON has SHA-256
`a80f54035934530b291a646f0d9a167a0c0f816833cb049996d0f2d9895c9fc8`.

## What the result cannot establish

This is a prior synthetic development comparison with two related cases,
three taxa, no measured vegetation and no held-out pollen prediction. Its
producer still depends on a historical snapshot and helper under the retained
`artifacts/v3/known-landscape/` prefix. The receipt preserves the observed
ranking but is not yet a self-contained product replay; we keep that prefix
until the producer is made durable or its historical role is explicitly
retired. We do not use this ranking to tune PPE, transport or basin geometry
for a real core.

Our current [governed synthetic reconstruction challenge](../../../docs/report/synthetic-validation/reconstruction/README.md)
separately tests transport-matched calculation controls and deliberate
transport/support mismatches. It also remains synthetic-only. For real model
use, our [source and parameter guide](../model-use.md) requires admitted
chronology, geometry, taxon denominator, PPE and an independent reference
before any vegetation-accuracy claim.

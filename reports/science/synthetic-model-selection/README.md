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
Our maintained [selection audit](selection-audit.json) independently
recomputes all 12 three-taxon errors from the retained trial values, checks
all 12 candidate/case pairs, the ranking and winner, and confirms that
assigning error `1.0` to the selected candidate's two trials changes the
selection. It verifies the tracked trial table, not the historical item
envelopes or a fresh LRA numerical run.

The report identifies source commit
`d915d1709d3c8fca4680f70958452860d578d5d1`, installed backend
`python-host-lra-0.1.9.dev74`, policy SHA-256
`cb954fdd8b03b66bd1efebf36db41608a1a051b02dc2ab8b4b6eceba3648a395`
and independent oracle SHA-256
`c53291b9be045fef04334533a8a7f40f8811d7f49c809745522409db8b94aff8`.
We retained the policy and trial result byte for byte from the original run.
The audit checks their exact hashes before interpreting the scores.

## What the result cannot establish

This is a prior synthetic development comparison with two related cases,
three taxa, no measured vegetation and no held-out pollen prediction. Its
original trial envelopes and engine inputs remain in the qualified private
source archive; the tracked result does not reproduce the original numerical
engine execution without them. We do not use this ranking to tune PPE,
transport or basin geometry for a real core.

From the repository root, reproduce the governed selection audit into an
absent disposable output and compare it with the retained result:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/synthetic-model-selection/replay.py \
  --output artifacts/jobs/synthetic-selection-reproduction/audit.json
cmp artifacts/jobs/synthetic-selection-reproduction/audit.json \
  reports/science/synthetic-model-selection/selection-audit.json
```

Our current [governed synthetic reconstruction challenge](../../../docs/report/synthetic-validation/reconstruction/README.md)
separately tests transport-matched calculation controls and deliberate
transport/support mismatches. It also remains synthetic-only. For real model
use, our [source and parameter guide](../model-use.md) requires admitted
chronology, geometry, taxon denominator, PPE and an independent reference
before any vegetation-accuracy claim.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Historical synthetic trial ranking and selection audit are retained.

**Unsupported claim.** Real-core PPE/transport recommendation or independent final-test result.

**Actual verification performed.** Retained 12-trial result and selection audit are cited; index did not rerun engine inputs.

**Remaining input or review.** The 12-trial two-case synthetic winner can compensate for a transport-law mismatch; original private trial envelopes are unavailable for fresh engine replay and no ecological holdout supports real-core tuning. Resolver: Synthetic trial custodian and qualified transport/field reviewer Reopen when: Authenticated trial inputs permit numerical replay; an admitted real-core cohort and independent reference permit separate parameter evaluation.

**Cause category.** assumption|comparability|access/rights

**Consequence.** Best-in-sweep candidate cannot be transferred across different transport laws or real cores.

**Precise next acceptance route.** Authenticated trial inputs permit numerical replay; an admitted real-core cohort and independent reference permit separate parameter evaluation. Then update reports/science/model-use.md.

**Negative or refused result.** All 12 trial cases completed without refusal; no held-out ecological target was tested.

**Matched denominator.** Two related synthetic cases × six parameter combinations =12 trials on three taxa; winner mean MAE 0.039861593480655426.

Retained evidence: [reports/science/synthetic-model-selection/report.json](report.json), [reports/science/synthetic-model-selection/selection-audit.json](selection-audit.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

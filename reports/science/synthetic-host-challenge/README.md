# What the independent host challenge established

## Our decision

We retained the historical host-interface challenge as a bounded engineering
diagnostic. It exercised evidence validation, installed REVEALS, product reading
and tamper refusal with independently generated synthetic pollen. We do not use
its vegetation residual as an ecological accuracy score or as a fitted LRA
parameter recommendation. The oracle's finite-cell inverse-square deposition
law differs from the REVEALS transport kernel, even though basin geometry and
the outer extent were declared consistently.

## What we observed

The exact [historical result](report.json) used three synthetic taxa and
converted oracle pollen fractions into 1,000,000 integer counts by largest
remainder. The maximum count-quantization residual was below
`0.00000036` fraction. The oracle basin radius was 175 m; the host received a
350 m basin diameter. Both declared a 5 km outer extent. Those declarations
align the geometric inputs, not the forward equations.

| Host run | Reconstructed broadleaf | Conifer | Open land | MAE against oracle truth |
| --- | ---: | ---: | ---: | ---: |
| Original PPE | 0.53213 | 0.35991 | 0.10796 | 0.039940 |
| Altered PPE | 0.88968 | 0.08023 | 0.03008 | 0.226457 |

Both output sums closed within the declared percentage-rounding bound. The
altered PPE increased MAE by `0.18651666666666664` vegetation fraction in this
one synthetic case. The reader returned the expected product manifest for both
runs. When the source evidence was altered after request construction, input
validation refused it with `evidence_digest_mismatch`.

The result binds source commit `70ddf5085ea8fef060f359ef0a4ddc719fb5cb68`
and independent oracle report SHA-256
`c53291b9be045fef04334533a8a7f40f8811d7f49c809745522409db8b94aff8`.
Our maintained [result check](replay.py) recomputes the pollen-count
quantization, geometry declarations, two three-taxon vegetation errors,
cover closure, reader-manifest equality and the recorded tamper refusal from
the tracked report:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/synthetic-host-challenge/replay.py
```

## Boundary and custody

The result is one three-taxon synthetic comparison with a deliberately
different forward law, no observed pollen, measured vegetation, calibration
threshold or LOVE support test. The result check verifies retained arithmetic
and declarations; it does not rerun the original numerical engine or
independently reproduce its tamper experiment. Those historical inputs and
outputs require the qualified private source archive. The current
[governed reconstruction challenge](../../../docs/report/synthetic-validation/reconstruction/README.md)
has an owned producer for calculation controls under declared source limits.

The separate [development sweep](../synthetic-model-selection/README.md)
used this oracle to compare twelve synthetic PPE/transport candidates. Neither
study chooses parameters for a real core.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** One source-bound synthetic host exercise checks input validation, output reading and PPE sensitivity.

**Unsupported claim.** Real-core parameter superiority or measured ecological accuracy.

**Actual verification performed.** Retained arithmetic/replay check is reported; index did not rerun original numerical host or tamper experiment.

**Remaining input or review.** Retained arithmetic and tamper receipt are bounded; the oracle inverse-square law differs from REVEALS, original private engine inputs are not public and synthetic truth is not measured vegetation. Resolver: Synthetic source custodian and qualified transport/ecology reviewer Reopen when: For a stronger calculation claim, authenticated original envelopes are replayed; for ecology, use a transport-matched and independently measured case.

**Cause category.** assumption|comparability|access/rights

**Consequence.** Different oracle/REVEALS transport laws prevent physical calibration from these residuals.

**Precise next acceptance route.** For a stronger calculation claim, authenticated original envelopes are replayed; for ecology, use a transport-matched and independently measured case. Then update reports/science/synthetic-model-selection/README.md.

**Negative or refused result.** One tampered request refused evidence_digest_mismatch; both synthetic host runs completed.

**Matched denominator.** One three-taxon case, one-million integer grains, 175 m oracle radius versus 350 m host diameter; original/altered PPE MAE 0.039940/0.226457.

Retained evidence: [reports/science/synthetic-host-challenge/report.json](report.json), [docs/report/synthetic-validation/reconstruction/README.md](../../../docs/report/synthetic-validation/reconstruction/README.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->

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

The source commit was `70ddf5085ea8fef060f359ef0a4ddc719fb5cb68` and the
independent oracle report SHA-256 was
`c53291b9be045fef04334533a8a7f40f8811d7f49c809745522409db8b94aff8`.
We copied the result byte for byte from the historical run; this owned copy
has SHA-256
`dc004ea877e29e1ea4d8778edd3c2809aeddd2efdd54159fd39e30fdc9b3a0bdc`.

## Boundary and custody

The result is one three-taxon synthetic comparison with a deliberately
different forward law, no observed pollen, measured vegetation, calibration
threshold or LOVE support test. Its historical producer and input products
still reside under `artifacts/v3/known-landscape/host-challenge/`, where the
producer depends on a frozen repository snapshot. We retain that subtree
until the producer and exact input closure have an owned replay route or a
documented supersession. Copying the result does not make the historical run
self-contained.

Our current [governed reconstruction challenge](../../../docs/report/synthetic-validation/reconstruction/README.md)
tests eight cases with an owned producer and declares the same transport-mismatch
limit. The separate [development sweep](../synthetic-model-selection/README.md)
used this oracle to compare twelve synthetic PPE/transport candidates. Neither
study chooses parameters for a real core.

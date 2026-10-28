# Independent synthetic recovery and counting diagnostics

The [retained account](report.json) brings together the eight-case
[public REVEALS reconstruction challenge](../reconstruction/README.md) and
three conditional counting experiments. The account producer reads exact
immutable numerical products; it does not rerun transport, reconstruction or
simulation. [The counting packet](../../../../data/synthetic-validation/finite-count-coverage/manifest.json)
retains its protocol, all actual synthetic count draws, all replicate/taxon
results and the independent review.

The reconstruction challenge was freshly executed on source candidate
`0179bc4fe37e4928776eb07a793f769aef680da2`. All eight public `run_reveals`
attempts were scored and passed their predeclared calculation contracts. Its
output is byte-identical to the retained report
`5023c8d46e58680492ce3bc821d1db6ff10af1c0ad7f7bb75907aa3562e19e84`.
The generator imports only standard library modules, and the execution checked
that both the generator and public consumer came from the frozen owned source.

Six runs use two independently implemented GPM peatland cases, each with matched
parameters, a broadleaf PPE multiplied by `0.8`, and a cyclic taxon-label shuffle.
These share the production method's equations and are inverse crime controls
for calculation correctness. Two further cases use a different finite-cell
inverse-square forward model and preserve its mismatch with the production GPM
transport/support assumptions. Their truth MAEs are `0.0674633333333333` and
`0.07989669750321703` vegetation fraction. Passing the calculation contract
preserves these errors; it does not establish recovery of that different model's
truth. The maximum calculation discrepancy is `4.864424231990072e-6`, within
the declared `5e-6` rounding tolerance, and the maximum deposition discrepancy
is `5.551115123125783e-17`, within the declared `1e-12` absolute tolerance.

The counting experiments were executed at their original source candidate
`2b076418e86577058f70db216783ae3b2b74040b`. Each retains 1,000 independently
sampled multinomial draws on six fixed synthetic supports and ten taxa. The
count probabilities use the protocol's fixed deposition, PPE and synthetic
vegetation truth. The production fixed-site covariance consumer uses a measured
boolean mask, zero PPE covariance and fixed site geometry. These are synthetic
counts in a development fixture, not observed source counts or independent
field vegetation measurements.

| Counting experiment | Attempts / accepted | Preserved interval outcome |
|---|---:|---|
| Uniform vegetation, matched transport | 1,000 / 1,000 | Per-taxon coverage ranges from 934/1,000 to 963/1,000 |
| Rare Alnus truth (`0.00001`), matched transport | 1,000 / 1,000 | Alnus covers 427/1,000; 525 draws have zero pooled count and zero standard error |
| Uniform vegetation, assumed Alnus deposition multiplied by 1.5 | 1,000 / 1,000 | Alnus covers 0/1,000; bias is `-0.030951302160679012` |

The reported intervals are unclipped marginal normal intervals with multiplier
`1.959963984540054`. Compositional closure makes their simultaneous interpretation
inappropriate. The full account preserves every taxon's coverage numerator,
denominator, Monte Carlo standard error, bias, RMSE, empirical variance, mean
plug-in variance and zero-count/zero-standard-error frequency, including the
poorer outcomes. There were no refused counting draws. The matched counting
experiments share the inverse model; they are conditional numerical controls.
The named transport misspecification is a deliberate sensitivity, not a measured
transport error.

The separate independent review recomputed cover and marginal counting variance
from all 3,000 retained draws: 60,000 scalar comparisons across 30,000 marginal
rows. Maximum differences were `5.551115123125783e-17` for cover and
`5.421010862427522e-20` for variance. The review binds all four source products
and preserves the poor outcomes. The earlier production spot checks cover only
25 draws per experiment and remain distinct from this complete retained review.

These diagnostics establish independent forward generation, noise-free numerical
contracts, noisy conditional coverage measurements and explicit model
misspecification cases. They do not certify interval coverage, generalize to
unseen support/model choices, estimate PPE uncertainty, resample sites, validate
chronology uncertainty, establish ecological accuracy, or supply global method,
rights, human-review or release acceptance.

Rebuild the deterministic retained account from an installed development package:

```bash
python -m bijux_pollenomics_dev.lra_validation.recovery_evidence \
  --repository . \
  --output artifacts/science/synthetic-recovery-evidence/report.json
cmp docs/report/synthetic-validation/recovery-evidence/report.json \
  artifacts/science/synthetic-recovery-evidence/report.json
```

The original eight-case producer and its independent generator remain available
through the linked reconstruction challenge. The source packet's immutable
hashes reject changed report, draw, marginal-row and review bytes; retaining this
account does not authorize relabelling historical results as a fresh study.

## Maintained numerical reproduction

The maintained counting producer was executed against numerical source candidate
`159d541e7b86442728b9d540ebec93588eba54eb` using the exact prepared producer
code recorded in the [execution custody](../../../../data/synthetic-validation/finite-count-coverage/execution-custody.json).
That producer/verifier code was an artifact proposal at execution time and is
identified by its own physical hashes; it was not already tracked in that baseline
commit. The new native consumer completed in `7.57752462499775` seconds; the
independent complete scalar verification completed in `0.9345254999934696` seconds.
Both native exits were zero and all 156 registered input pins remained unchanged.

Every generated multinomial draw and all 30,000 marginal CSV rows exactly match
the original study bytes. Every scientific report field also matches. Only the
fresh execution's candidate and plan hash differ, and both original and fresh
reports are retained separately. The fresh scalar verification again reproduces
the reported maximum differences and all poor outcomes. Runtime/source/native
log identities, the exact numerical source closure and original/fresh execution
distinctions are retained in the custody packet. No source R program was replayed.

To repeat the fixed numerical experiment, supply the actual source revision and
SHA-256 of your separately frozen execution plan, and choose absent artifact
destinations. The source protocol retains its original preparatory metadata and
local source locator as historical bytes; the maintained producer instead uses
explicit repository/protocol/output arguments and the adjacent immutable source
report to validate the fixed support, taxa, PPE and deposition.

```bash
python -m bijux_pollenomics_dev.lra_validation.counting_coverage \
  --repository . \
  --protocol data/synthetic-validation/finite-count-coverage/protocol.json \
  --output artifacts/science/counting-recovery/products \
  --source-candidate <full-source-revision> \
  --plan-sha256 <frozen-execution-plan-sha256>
python -m bijux_pollenomics_dev.lra_validation.counting_coverage_verification \
  --repository . \
  --protocol data/synthetic-validation/finite-count-coverage/protocol.json \
  --products artifacts/science/counting-recovery/products \
  --output artifacts/science/counting-recovery/independent-review.json
```

The verifier uses only the standard library. It recomputes each scalar quotient
and marginal multinomial quadratic form from the retained counts, rather than
calling the production inverse or covariance code. The full draw and marginal
rows make numerical and missingness counterexamples available to tracked-only
readers without rebuilding an unrelated source capture.

# Synthetic REVEALS reconstruction challenge

The [retained result](report.json) runs eight deterministic reconstructions
through the public `run_reveals` workflow. Truth and pollen come from the
independent standard library landscape generator, which imports no production
forward model, inverse method or numerical kernel.

Two GPM peatland annulus cases each have three paired runs: correct parameters,
a 20% broadleaf PPE reduction, and one cyclic shuffle of pollen taxon labels.
Each pair preserves the same truth, support, basin, total pollen weight and
transport settings. The expected changed-parameter reconstruction is calculated
independently. Two additional finite-cell cases deliberately challenge the
production GPM transport and annulus support assumptions. Their known truth
differs from the production model's estimand; their errors are retained and
identified as transport and support mismatches.

The prospective calculation tolerance is `0.000005` vegetation fraction, half a
unit of the source's three-decimal percentage rounding. Deposition comparison
uses an absolute `1e-12` tolerance. These are numerical contracts, not reviewed
ecological performance thresholds. Inputs are analytical pollen weights;
there are no observed counts, invented counting efforts or simulated uncertainty
interval claims.

All eight attempts produced scored outputs. Both matched parameter runs recover
their known truth exactly after source rounding. The other six runs retain the
expected disagreement with that truth:

| Synthetic support | Control | Vegetation MAE, fraction |
|---|---|---:|
| 350 m peatland, 5 km GPM annuli | Correct parameters | 0.000000 |
| 350 m peatland, 5 km GPM annuli | Broadleaf PPE reduced by 20% | 0.036263 |
| 350 m peatland, 5 km GPM annuli | Cyclic pollen label shuffle | 0.468187 |
| 200 m peatland, 8 km GPM annuli | Correct parameters | 0.000000 |
| 200 m peatland, 8 km GPM annuli | Broadleaf PPE reduced by 20% | 0.036740 |
| 200 m peatland, 8 km GPM annuli | Cyclic pollen label shuffle | 0.381760 |
| Homogeneous finite cells, 5 km extent | GPM transport/support mismatch | 0.067463 |
| Heterogeneous finite cells, 8 km extent | GPM transport/support mismatch | 0.079897 |

Every output agrees with its independent calculation expectation within the
declared rounding tolerance. The largest absolute calculation discrepancy is
`0.000004864425` fraction. For negative controls, the contract verifies the
calculation and preserves its disagreement with known landscape truth.

The matched GPM generator independently implements the same transport equations
as the production method. This is an inverse crime control for calculation
correctness. The finite-cell challenges use a different transport model. Neither
result establishes measured vegetation accuracy, spatial interpolation skill,
held-out ecological performance, PPE estimation or calibrated uncertainty.

The recorded configuration and production manifest both name the
`disqover-0.9.14-wrapper-v1` fall-speed profile. The report retains the model,
inputs, backend and runtime identity from the
production manifest. It omits the editable distribution's SCM-derived package
version because its commit distance changes as unrelated repository work is
committed; that distance does not identify a different numerical method.
Reproduce from the repository root with the configured environment:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.lra_validation.reconstruction_challenge \
  --output artifacts/jobs/synthetic-validation/reconstruction/report.json
cmp docs/report/synthetic-validation/reconstruction/report.json \
  artifacts/jobs/synthetic-validation/reconstruction/report.json
```

The report retains each source case, source identities, true and assumed
parameters, input weights, independent expected outputs, production manifest,
prediction, truth error and calculation error. Refusals remain in the attempted
denominator. `test_reconstruction_challenge.py` exercises the public consumer,
independent known truth, paired controls and refusal accounting.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Known constructed method/identity challenge; no empirical biological accuracy or untouched confirmation.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->

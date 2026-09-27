# Synthetic grouped site leakage challenge

The [retained result](report.json) rotates all six fabricated physical sites,
each with an alternate record connected by an explicit synthetic alias. Sites
form three nearby pairs with independently declared tree/grass cover. Their
coordinates are synthetic WGS84 points, and distances use the unrounded inverse
geodesic from the production distance function with a retained pyproj version.

Every fold runs four controls through the actual grouped split guard and public
`predict_withheld_site` interface. Nearest site prediction uses one composition
per training physical group and calls the numerical engine's public
`forward_deposition`. The second control cyclically reassigns compositions among
the five admitted training sites, preserving the training denominator and
withholding the target's outcome. Two further attempts insert a held-out alias
or a product with transitive target ancestry into fit inputs. Both must be
refused before the engine is called.

The producer declares 24 attempts: twelve predictions and twelve expected
leakage refusals. It retains every fold's exclusions, complete dependency graph,
training assignment, allowed prediction inputs, immutable prediction identity,
output, score and refusal. Target truth is scored after prediction. A separate
scoring-store perturbation regression verifies that changing truth changes
scores while preserving every frozen prediction identity and output.

All 24 attempts completed: twelve scored predictions and twelve expected leakage
refusals, with twelve numerical calls. Both controls scored every eligible site
on paired support:

| Training site assignment | Sites scored | Vegetation MAE, fraction | Pollen MAE, fraction | Pollen Hellinger |
|---|---:|---:|---:|---:|
| Original nearest pair | 6 | 0.000000 | 0.000000 | 0.000000 |
| Cyclic training site shuffle | 6 | 0.400000 | 0.370370 | 0.287271 |

The zero baseline error follows the deliberately constructed equal-truth nearby
pairs. The shuffle breaks that site association while preserving the same
training and scoring denominator. These results test the declared synthetic
interpolation and leakage contracts.

Truth has the same two-category site support as the predicted composition.
The synthetic forward context uses unit local deposition factors, zero regional
background and fixed PPE `[2, 1]`; its pollen expectation is computed independently
from that explicit formula. The `1e-12` comparison tolerance tests calculations.
The prediction context binds the loaded numerical forward module's SHA-256.
There are no observed counts or calibrated predictive intervals. The complete
alias graph is known by construction and provides no reviewed real-source
crosswalk or empirical ecological accuracy claim.

Reproduce from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
.venv/bin/python -m bijux_pollenomics_dev.lra_validation.site_leakage_challenge \
  --output docs/report/synthetic-validation/site-leakage/report.json
```

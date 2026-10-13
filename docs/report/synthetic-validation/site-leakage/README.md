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
  --output artifacts/jobs/synthetic-validation/site-leakage/report.json
cmp docs/report/synthetic-validation/site-leakage/report.json \
  artifacts/jobs/synthetic-validation/site-leakage/report.json
```


## Development evaluator input isolation

A separate [development intake witness](development-input-isolation.json) uses
real analytical LRA reconstruction products and the public baseline/fitted
spatial evaluator APIs on four inspected constructed sites. Five direct public
experiment paths now write and flush their existing split payloads before
reconstruction, cached-result consumption or spatial fitting. They verify those
bytes before subsequent numerical work and publication; changed or replaced
manifests are refused without rewriting them.

A nine-record identity witness forms four groups. Six records share the target
group through explicit core, publication, alternative-chronology, alias and
transitive derived ownership. Three unrelated records remain training groups.
An unowned derived product with target ancestry is refused. These identities
are known by construction; they do not qualify missing real-source links.

The withheld `p01` counts change from `[600,400]` to valid `[100,900]`, with
constructed vegetation truth changing from `[0.25,0.75]` to `[0.9,0.1]`.
The three fixed baseline predictions and both fitted-family target predictions
retain identical full training and prediction fingerprints. Scores change only
after the published predictions are reopened for scoring:

| Target method | Original pollen MAE | Perturbed pollen MAE |
| --- | ---: | ---: |
| Training mean | 0.002610865 | 0.502610865 |
| Nearest site | 0.002062155 | 0.502062155 |
| Inverse distance squared | 0.002399884 | 0.502399884 |
| CLR/WGS84 RBF ridge | 0.002610715 | 0.502610715 |

The fitted family also retains its separate training-mean baseline; all twenty
pollen/vegetation target metric cells and both variant fingerprints are in the
aggregate account. These are scores against declared constructed truth.

The perturbed record becomes training data in the other three outer folds.
Those folds legitimately refuse negative reconstructed compositions. Baseline
outputs therefore change from 12 of 12 predictions to 3 of 12; fitted outputs
change from 8 of 8 to 2 of 8. Their thirty failed-prediction scoring rows remain
explicit, alongside fifty scored rows. Counts remain valid; negative local
composition is not clipped or discarded to force a prediction.

The fitted runs verify sixteen reconstruction cache hits from ten exact
request/profile/code/runtime-bound products and perform five spatial fits,
without repeating basin inversions. A separate verification-only capture passes
57 focused guards and an independent producer-free audit: all nine records and
four groups, 185 journal events, target fingerprints and fifty Decimal50 MAE
cells (maximum difference `8.5e-17`, tolerance `2e-13`). The
[source account](development-input-isolation-source-account.json) retains
actual commands, hashes, measured resource scope and every earlier failed
whole-job receipt. Completed numerical products are qualified separately from
those failed harness runs; no missing past event ledger is invented.

This inspected software-contract exercise supplies no measured vegetation
accuracy, qualified real-source identity graph, biological admission or
untouched confirmation. The original 24-case forward challenge above retains
its separate source, denominator and result.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Known constructed method/identity challenge; no empirical biological accuracy or untouched confirmation.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/pollen-prediction.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/pollen-prediction.md) (source SHA-256 `2f61fcbbf6fb36a075790199e81d834dbf8225e426aa7d92dc1ba4cbfb19f1f0`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
